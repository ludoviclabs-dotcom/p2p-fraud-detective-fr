#!/usr/bin/env python3
"""Vérificateur hors-ligne d'un Case Pack proof-manifest/v1.

Conçu pour être exécuté par un tiers (CAC, ACPR, contrôleur interne) SANS
installer le produit : uniquement la bibliothèque standard Python 3.
PyNaCl est optionnel — sans lui, les signatures Ed25519 sont signalées
comme non vérifiées (avertissement), les contrôles de hash restent complets.

Usage :
    python verify_case_pack.py case-pack-p2p-<case_id>.zip

Sortie : un verdict par contrôle, exit code 0 si tout passe, 1 sinon.

Contrôles :
1. SHA-256 de chaque fichier vs manifest.json ;
2. signature Ed25519 du manifeste canonique vs signerPublicKeyB64 ;
3. chaîne d'audit-trail.jsonl : recalcul des hash, continuité prev_hash,
   cohérence avec chainHead, signatures d'entrées présentes ;
4. cohérence du schéma (schemaVersion, fichiers manquants/inattendus).

La logique de hash est volontairement DUPLIQUÉE depuis le produit pour que
ce script reste autonome — toute divergence casserait la vérification, ce
qui est le comportement voulu (fail-closed).
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
import zipfile

GENESIS_HASH = "0" * 64
SCHEMA_VERSION = "proof-manifest/v1"
# Fichiers hors inventaire : le manifeste (hashé via sa forme canonique),
# sa signature, et le README (documentation, non probant).
NON_INVENTORY = {"manifest.json", "signature.sig", "README.txt"}

_ok = True


def report(passed: bool, label: str, detail: str = "") -> None:
    global _ok
    mark = "OK " if passed else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    if not passed:
        _ok = False


def warn(label: str, detail: str = "") -> None:
    print(f"[WARN] {label}" + (f" — {detail}" if detail else ""))


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_ed25519(message: bytes, signature_hex: str, public_key_b64: str) -> bool | None:
    """True/False si vérifiable ; None si PyNaCl absent."""
    try:
        from nacl.signing import VerifyKey
    except ImportError:
        return None
    try:
        VerifyKey(base64.b64decode(public_key_b64)).verify(message, bytes.fromhex(signature_hex))
        return True
    except Exception:
        return False


def entry_hash(entry: dict) -> str:
    """Recalcule le hash d'une entrée d'audit (même canonicalisation que le produit)."""
    body = {
        "seq": entry["seq"],
        "at": entry["at"],
        "actor": entry["actor"],
        "kind": entry["kind"],
        "payload": entry["payload"],
        "prev_hash": entry["prev_hash"],
    }
    return sha256_hex(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def main(path: str) -> int:
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        manifest = json.loads(zf.read("manifest.json"))
        signature_hex = zf.read("signature.sig").decode("ascii").strip()

        # ── Schéma ───────────────────────────────────────────────────────────
        report(
            manifest.get("schemaVersion") == SCHEMA_VERSION,
            "Schéma du manifeste",
            str(manifest.get("schemaVersion")),
        )

        # ── 1. Hash de chaque fichier inventorié ─────────────────────────────
        inventoried = {f["path"] for f in manifest.get("files", [])}
        for item in manifest.get("files", []):
            if item["path"] not in names:
                report(False, f"Fichier manquant : {item['path']}")
                continue
            actual = sha256_hex(zf.read(item["path"]))
            report(
                actual == item["sha256"],
                f"SHA-256 {item['path']}",
                ""
                if actual == item["sha256"]
                else f"attendu {item['sha256'][:16]}…, obtenu {actual[:16]}…",
            )
        unexpected = names - inventoried - NON_INVENTORY
        report(not unexpected, "Aucun fichier hors inventaire", ", ".join(sorted(unexpected)))

        # ── 2. Signature du manifeste canonique ─────────────────────────────
        manifest_sha = sha256_hex(canonical(manifest).encode("utf-8"))
        public_key = manifest.get("signerPublicKeyB64") or ""
        if not signature_hex or not public_key:
            warn("Manifeste non signé", "pack généré en mode démo (pas de clé Ed25519)")
        else:
            verdict = verify_ed25519(manifest_sha.encode("utf-8"), signature_hex, public_key)
            if verdict is None:
                warn("Signature non vérifiée", "installer PyNaCl : pip install pynacl")
            else:
                report(verdict, "Signature Ed25519 du manifeste")

        # ── 3. Chaîne d'audit ────────────────────────────────────────────────
        lines = [
            json.loads(line)
            for line in zf.read("audit-trail.jsonl").decode("utf-8").splitlines()
            if line.strip()
        ]
        prev = GENESIS_HASH
        chain_ok = True
        signatures_checked = 0
        for entry in lines:
            if entry["prev_hash"] != prev or entry_hash(entry) != entry["hash"]:
                report(False, f"Chaîne d'audit rompue à seq={entry['seq']}")
                chain_ok = False
                prev = entry["hash"]
                continue
            if entry.get("signature") and public_key:
                verdict = verify_ed25519(
                    entry["hash"].encode("utf-8"), entry["signature"], public_key
                )
                if verdict is False:
                    report(False, f"Signature d'entrée invalide à seq={entry['seq']}")
                    chain_ok = False
                elif verdict is True:
                    signatures_checked += 1
            prev = entry["hash"]
        if chain_ok:
            report(
                True,
                f"Chaîne d'audit ({len(lines)} entrées, {signatures_checked} signatures vérifiées)",
            )
        report(
            (lines[-1]["hash"] if lines else "") == manifest.get("chainHead", ""),
            "chainHead du manifeste ancre la dernière entrée",
        )

    print()
    print("VERDICT :", "PACK VALIDE" if _ok else "PACK INVALIDE")
    return 0 if _ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
