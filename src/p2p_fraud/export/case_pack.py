"""Case Pack vérifiable hors-ligne — format proof-manifest/v1.

Export ZIP d'un cas d'investigation qu'un tiers (CAC, ACPR, contrôleur
interne) peut vérifier SANS aucun accès au produit :

- chaque fichier du pack est hashé SHA-256 dans `manifest.json` ;
- le manifeste canonique est signé Ed25519 (`signature.sig`) avec la clé du
  produit — la même que celle qui signe l'audit log ;
- `audit-trail.jsonl` embarque la chaîne complète, re-vérifiable hors-ligne ;
- `README.txt` documente la procédure et embarque la clé publique ;
- `scripts/verify_case_pack.py` (stdlib uniquement) exécute les contrôles.

Zéro IA dans la chaîne de preuve : tout est déterministe (ADR-0007).
Le format est documenté dans `docs/proof-manifest-v1.md` et conçu pour être
réutilisé tel quel par d'autres produits (mutualisation au niveau du format,
pas du code).
"""

from __future__ import annotations

import hashlib
import io
import json
import uuid
import zipfile
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.models import Case, CaseEvent
from p2p_fraud.security.signing import Ed25519Signer

SCHEMA_VERSION = "proof-manifest/v1"
PROJECT_KEY = "p2p"


def _canonical(obj: Any) -> str:
    """Canonicalisation JSON stricte — identique à celle de l'audit log."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_README_TEMPLATE = """\
CASE PACK VÉRIFIABLE — P2P Fraud Detective FR
=============================================

Ce pack est un export de preuve au format proof-manifest/v1. Il est conçu
pour être vérifié HORS-LIGNE, sans accès au produit qui l'a généré.

Contenu
-------
- manifest.json      : inventaire des fichiers avec leur hash SHA-256,
                       tête de chaîne d'audit, clé publique du signataire.
- signature.sig      : signature Ed25519 (hex) du SHA-256 du manifeste
                       canonique (JSON trié, séparateurs compacts, UTF-8).
                       Fichier vide = pack généré en mode démo non signé.
- case.json          : le cas d'investigation et ses événements de workflow.
- audit-trail.jsonl  : la chaîne d'audit complète (une entrée JSON par ligne,
                       hash SHA-256 chaîné + signatures Ed25519 par entrée).
- dossier-ia.json    : (optionnel) dossier d'enquête généré par IA — contenu
                       assistif, la preuve reste 100 % déterministe.

Vérification
------------
1. Recalculer le SHA-256 de chaque fichier et comparer à manifest.json.
2. Re-canonicaliser manifest.json (clés triées, séparateurs "," ":"),
   calculer son SHA-256 et vérifier signature.sig avec la clé publique
   Ed25519 ci-dessous (32 octets, base64).
3. Re-vérifier la chaîne d'audit-trail.jsonl : pour chaque entrée,
   hash = SHA-256 du JSON canonique de
   {{"actor","at","kind","payload","prev_hash","seq"}} ; prev_hash doit
   être le hash de l'entrée précédente (genesis : 64 zéros) ; les
   signatures d'entrée signent la chaîne hex du hash (UTF-8).

Le script `verify_case_pack.py` (Python 3, bibliothèque standard ;
PyNaCl optionnel pour les signatures) automatise ces contrôles :

    python verify_case_pack.py case-pack-p2p-<case_id>.zip

Clé publique Ed25519 (base64)
-----------------------------
{public_key}

Export
------
- exportId    : {export_id}
- généré le   : {generated_at}
- cas         : {case_id}
- chainHead   : {chain_head}
"""


def build_case_pack(
    case: Case,
    events: list[CaseEvent],
    audit_log: AuditLog,
    *,
    signer: Ed25519Signer,
    dossier_ia: dict[str, Any] | None = None,
    actor: str = "system",
) -> bytes:
    """Construit le Case Pack ZIP en mémoire.

    L'export est lui-même journalisé (`case.pack_exported`) AVANT la capture
    de la chaîne, afin que le pack contienne sa propre trace d'export. Le
    hash du manifeste n'y figure pas (dépendance circulaire : le manifeste
    hashe audit-trail.jsonl) — c'est `chainHead` qui ancre le pack.
    """
    export_id = f"exp_{uuid.uuid4().hex[:16]}"
    generated_at = datetime.now(UTC).isoformat()

    # 1. Tracer l'export dans le journal — il fera partie du pack.
    audit_log.append(
        actor=actor,
        kind="case.pack_exported",
        payload={"case_id": case.case_id, "export_id": export_id},
    )

    # 2. Contenus des fichiers de preuve.
    case_json = json.dumps(
        {
            "case": case.model_dump(mode="json"),
            "events": [e.model_dump(mode="json") for e in events],
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8")

    entries = audit_log.all()
    audit_jsonl = "\n".join(
        json.dumps(asdict(e), sort_keys=True, ensure_ascii=False) for e in entries
    ).encode("utf-8")
    chain_head = entries[-1].hash if entries else ""

    files: dict[str, bytes] = {
        "case.json": case_json,
        "audit-trail.jsonl": audit_jsonl,
    }
    kinds = {"case.json": "json", "audit-trail.jsonl": "jsonl"}
    if dossier_ia is not None:
        files["dossier-ia.json"] = json.dumps(
            dossier_ia, ensure_ascii=False, indent=2, sort_keys=True
        ).encode("utf-8")
        kinds["dossier-ia.json"] = "json"

    # 3. Manifeste : inventaire hashé, trié par chemin.
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "exportId": export_id,
        "project": PROJECT_KEY,
        "entityType": "case",
        "entityId": case.case_id,
        "generatedAt": generated_at,
        "chainHead": chain_head,
        "signerPublicKeyB64": signer.public_key_b64,
        "algorithms": {"hash": "SHA-256", "signature": "Ed25519"},
        "files": [
            {"path": path, "sha256": _sha256_hex(content), "kind": kinds[path]}
            for path, content in sorted(files.items())
        ],
    }
    manifest_sha256 = _sha256_hex(_canonical(manifest).encode("utf-8"))
    # Même patron que l'audit log : on signe la chaîne hex du hash.
    signature_hex = signer.sign(manifest_sha256)

    readme = _README_TEMPLATE.format(
        public_key=signer.public_key_b64 or "(pack non signé — mode démo)",
        export_id=export_id,
        generated_at=generated_at,
        case_id=case.case_id,
        chain_head=chain_head or "(journal vide)",
    ).encode("utf-8")

    # 4. Assemblage ZIP (manifest.json lisible ; le vérificateur
    #    re-canonicalise depuis le JSON parsé, pas depuis les octets).
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        )
        zf.writestr("signature.sig", signature_hex)
        zf.writestr("README.txt", readme)
        for path, content in sorted(files.items()):
            zf.writestr(path, content)
    return buffer.getvalue()
