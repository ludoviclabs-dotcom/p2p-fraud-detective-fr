"""Script ad-hoc P5-4.1 — migration i18n des init_page() sur les 18 pages restantes.

À exécuter une seule fois. Conservé en `scripts/` pour traçabilité.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "pages"

# Mapping fichier → (page_key, surtitle_key, kicker_key)
PAGES = {
    "1_📤_Upload.py": ("page_upload", "surtitle_donnees", "kicker_upload"),
    "2_🔢_Benford.py": ("page_benford", "surtitle_controles", "kicker_benford"),
    "3_🏦_Master_data_history.py": (
        "page_master_data",
        "surtitle_donnees",
        "kicker_master_data",
    ),
    "4_♊_Doublons.py": ("page_doublons", "surtitle_controles", "kicker_doublons"),
    "5_📏_Sous_seuils.py": ("page_sous_seuils", "surtitle_controles", "kicker_sous_seuils"),
    "6_🇫🇷_Sirene_check.py": ("page_sirene", "surtitle_donnees", "kicker_sirene"),
    "7_🤖_Anomalies_ML.py": ("page_anomalies_ml", "surtitle_ml", "kicker_anomalies_ml"),
    "8_🕸️_Anneaux_fraude.py": ("page_anneaux", "surtitle_ml", "kicker_anneaux"),
    "9_⚖️_Sanctions_PEP.py": ("page_sanctions", "surtitle_controles", "kicker_sanctions"),
    "10_🗂️_File_d_investigation.py": ("page_file", "surtitle_pilotage", "kicker_file"),
    "11_📊_Synthèse_export.py": ("page_synthese", "surtitle_investigation", "kicker_synthese"),
    "13_📜_Audit_trail.py": (
        "page_audit_trail",
        "surtitle_investigation",
        "kicker_audit_trail",
    ),
    "14_💡_Score_explorer.py": (
        "page_score_explorer",
        "surtitle_ml",
        "kicker_score_explorer",
    ),
    "16_🛡️_Gouvernance.py": ("page_gouvernance", "surtitle_gouvernance", "kicker_gouvernance"),
    "17_🏛️_DECP_RBE.py": ("page_decp", "surtitle_controles", "kicker_decp"),
    "18_🔔_Alertes.py": ("page_alertes", "surtitle_pilotage", "kicker_alertes"),
    "19_👥_Collaboration.py": ("page_collab", "surtitle_pilotage", "kicker_collab"),
    "20_🎮_Sandbox.py": ("page_sandbox", "surtitle_pilotage", "kicker_sandbox"),
}

INIT_PAGE_PATTERN = re.compile(
    r"init_page\(\s*\n"
    r"\s*title=[\"']([^\"']*)[\"'],?\s*\n"
    r"\s*surtitle=[\"']([^\"']*)[\"'],?\s*\n"
    r"\s*kicker=(?:\(\s*[\"']([^\"']*)[\"']\s*\)|[\"']([^\"']*)[\"']),?\s*\n"
    r"\)",
    re.MULTILINE,
)


def migrate(path: Path, page_k: str, surtitle_k: str, kicker_k: str) -> bool:
    txt = path.read_text(encoding="utf-8")
    if "from p2p_fraud.i18n import" in txt:
        # Déjà partiellement migré — on ajoute juste l'appel init_page i18n
        pass
    else:
        # Ajouter import au plus près des autres p2p_fraud
        # Pattern : ligne `from p2p_fraud.streamlit_theme import init_page`
        txt = re.sub(
            r"(from p2p_fraud\.streamlit_theme import init_page)",
            r"from p2p_fraud.i18n import _, init_locale_from_session\n\1",
            txt,
            count=1,
        )
        # Ajouter init_locale_from_session() juste avant init_page(
        txt = re.sub(
            r"(\ninit_page\()",
            r"\ninit_locale_from_session()\n\1",
            txt,
            count=1,
        )

    # Remplacer le bloc init_page()
    def repl(m: re.Match) -> str:
        return (
            "init_page(\n"
            f'    title=_("nav.{page_k}"),\n'
            f'    surtitle=_("nav.{surtitle_k}"),\n'
            f'    kicker=_("nav.{kicker_k}"),\n'
            ")"
        )

    new_txt, n = INIT_PAGE_PATTERN.subn(repl, txt)
    if n == 0:
        print(f"⚠️ {path.name}: no init_page() block matched, skipping")
        return False
    path.write_text(new_txt, encoding="utf-8")
    print(f"✅ {path.name}: migrated")
    return True


def main() -> None:
    n_ok = 0
    for fname, (p, s, k) in PAGES.items():
        path = ROOT / fname
        if not path.exists():
            print(f"⚠️ {fname}: file not found")
            continue
        if migrate(path, p, s, k):
            n_ok += 1
    print(f"\n{n_ok} / {len(PAGES)} pages migrées.")


if __name__ == "__main__":
    main()
