"""Tests du Case Pack vérifiable (proof-manifest/v1) — déterministes.

Les tests de signature génèrent un keypair Ed25519 jetable (skip si PyNaCl
absent) ; les tests de hash et de structure tournent sans dépendance.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from p2p_fraud.cases.audit_log import AuditLog
from p2p_fraud.cases.service import CaseService
from p2p_fraud.export.case_pack import build_case_pack
from p2p_fraud.schema import Finding, Severity
from p2p_fraud.security.signing import Ed25519Signer, verify_signature

VERIFY_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "verify_case_pack.py"


def _canonical_sha256(obj) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _make_case(service: CaseService):
    finding = Finding(
        invoice_id="INV-77",
        detector="master_data",
        rule_id="IBAN_CHANGE_NO_4EYES",
        signal="IBAN modifié sans validation 4-eyes",
        severity=Severity.CRITICAL,
        evidence={"vendor_id": "V-ALPHACOM", "exposure_eur": 125000},
    )
    case = service.create_case_from_finding(finding, actor="analyste@test")
    service.comment(case.case_id, actor="analyste@test", text="RIB à confirmer")
    return service.get(case.case_id), service.list_events(case.case_id)


def _build(signer: Ed25519Signer, *, dossier_ia=None) -> tuple[bytes, str]:
    service = CaseService(":memory:", audit_log=AuditLog(":memory:", signer=signer))
    case, events = _make_case(service)
    pack = build_case_pack(
        case, events, service.audit_log, signer=signer, dossier_ia=dossier_ia, actor="test"
    )
    return pack, case.case_id


def _signer() -> Ed25519Signer:
    pytest.importorskip("nacl")
    return Ed25519Signer(Ed25519Signer.generate().private_key_b64)


# ─── Structure et hashes ─────────────────────────────────────────────────────


def test_pack_structure_and_file_hashes():
    pack, _case_id = _build(Ed25519Signer())  # mode démo non signé
    with zipfile.ZipFile(io.BytesIO(pack)) as zf:
        names = set(zf.namelist())
        assert {
            "manifest.json",
            "signature.sig",
            "README.txt",
            "case.json",
            "audit-trail.jsonl",
        } == names
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["schemaVersion"] == "proof-manifest/v1"
        assert manifest["project"] == "p2p"
        assert manifest["algorithms"] == {"hash": "SHA-256", "signature": "Ed25519"}
        # Chaque fichier inventorié re-hashe à l'identique.
        assert {f["path"] for f in manifest["files"]} == {"case.json", "audit-trail.jsonl"}
        for item in manifest["files"]:
            assert hashlib.sha256(zf.read(item["path"])).hexdigest() == item["sha256"]
        # Mode démo : non signé mais structurellement valide.
        assert manifest["signerPublicKeyB64"] == ""
        assert zf.read("signature.sig") == b""


def test_pack_includes_optional_dossier_ia():
    pack, _ = _build(Ed25519Signer(), dossier_ia={"executive_summary": "x"})
    with zipfile.ZipFile(io.BytesIO(pack)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        assert "dossier-ia.json" in {f["path"] for f in manifest["files"]}
        assert json.loads(zf.read("dossier-ia.json"))["executive_summary"] == "x"


def test_export_is_itself_audit_logged_in_pack():
    pack, case_id = _build(Ed25519Signer())
    with zipfile.ZipFile(io.BytesIO(pack)) as zf:
        entries = [json.loads(line) for line in zf.read("audit-trail.jsonl").decode().splitlines()]
        exported = [e for e in entries if e["kind"] == "case.pack_exported"]
        assert exported and exported[-1]["payload"]["case_id"] == case_id
        # chainHead ancre la dernière entrée (l'événement d'export).
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["chainHead"] == entries[-1]["hash"]


# ─── Signature Ed25519 ───────────────────────────────────────────────────────


def test_manifest_signature_verifies_with_public_key():
    signer = _signer()
    pack, _ = _build(signer)
    with zipfile.ZipFile(io.BytesIO(pack)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        signature_hex = zf.read("signature.sig").decode("ascii")
    assert manifest["signerPublicKeyB64"] == signer.public_key_b64
    assert verify_signature(
        message=_canonical_sha256(manifest),
        signature_hex=signature_hex,
        public_key_b64=signer.public_key_b64,
    )


def test_tampered_manifest_signature_fails():
    signer = _signer()
    pack, _ = _build(signer)
    with zipfile.ZipFile(io.BytesIO(pack)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        signature_hex = zf.read("signature.sig").decode("ascii")
    manifest["entityId"] = "CASE-FALSIFIE"
    assert not verify_signature(
        message=_canonical_sha256(manifest),
        signature_hex=signature_hex,
        public_key_b64=signer.public_key_b64,
    )


# ─── Vérificateur autonome (subprocess, stdlib) ──────────────────────────────


def _run_verifier(pack: bytes, tmp_path: Path) -> subprocess.CompletedProcess:
    target = tmp_path / "pack.zip"
    target.write_bytes(pack)
    return subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), str(target)],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_verifier_accepts_valid_signed_pack(tmp_path):
    pack, _ = _build(_signer())
    result = _run_verifier(pack, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PACK VALIDE" in result.stdout


def test_verifier_accepts_unsigned_demo_pack_with_warning(tmp_path):
    pack, _ = _build(Ed25519Signer())
    result = _run_verifier(pack, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WARN" in result.stdout


def test_verifier_rejects_tampered_file(tmp_path):
    pack, _ = _build(Ed25519Signer())
    # Reconstruit le ZIP avec un case.json altéré d'un octet.
    src = zipfile.ZipFile(io.BytesIO(pack))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as out:
        for name in src.namelist():
            data = src.read(name)
            if name == "case.json":
                data = data.replace(b"INV-77", b"INV-99", 1)
            out.writestr(name, data)
    result = _run_verifier(buffer.getvalue(), tmp_path)
    assert result.returncode == 1
    assert "PACK INVALIDE" in result.stdout


def test_verifier_rejects_uninventoried_file(tmp_path):
    pack, _ = _build(Ed25519Signer())
    src = zipfile.ZipFile(io.BytesIO(pack))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as out:
        for name in src.namelist():
            out.writestr(name, src.read(name))
        out.writestr("intrus.json", b"{}")
    result = _run_verifier(buffer.getvalue(), tmp_path)
    assert result.returncode == 1


def test_verifier_rejects_broken_audit_chain(tmp_path):
    signer = _signer()
    pack, _ = _build(signer)
    src = zipfile.ZipFile(io.BytesIO(pack))
    # Altère une entrée d'audit PUIS ré-inventorie le fichier pour que seuls
    # les contrôles de chaîne (et la signature du manifeste) puissent échouer.
    entries = [json.loads(line) for line in src.read("audit-trail.jsonl").decode().splitlines()]
    entries[0]["payload"] = {"falsifie": True}
    audit = "\n".join(json.dumps(e, sort_keys=True, ensure_ascii=False) for e in entries).encode()
    manifest = json.loads(src.read("manifest.json"))
    for item in manifest["files"]:
        if item["path"] == "audit-trail.jsonl":
            item["sha256"] = hashlib.sha256(audit).hexdigest()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as out:
        for name in src.namelist():
            if name == "audit-trail.jsonl":
                out.writestr(name, audit)
            elif name == "manifest.json":
                out.writestr(
                    name, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
                )
            else:
                out.writestr(name, src.read(name))
    result = _run_verifier(buffer.getvalue(), tmp_path)
    assert result.returncode == 1
    assert "Chaîne d'audit rompue" in result.stdout or "rompue" in result.stdout


# ─── Endpoint ────────────────────────────────────────────────────────────────


def test_endpoint_returns_zip_and_404_on_unknown_case():
    from fastapi import HTTPException

    from p2p_fraud.api.v1 import case_pack_download

    service = CaseService(":memory:")
    case, _events = _make_case(service)
    response = case_pack_download(case.case_id, "anonymous", service)
    assert response.media_type == "application/zip"
    assert case.case_id in response.headers["content-disposition"]

    with pytest.raises(HTTPException) as exc:
        case_pack_download("CASE-INCONNU", "anonymous", service)
    assert exc.value.status_code == 404
