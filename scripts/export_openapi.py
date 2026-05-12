"""Export `openapi.json` du FastAPI vers `docs/api/openapi.json` (P5-3).

Utilisé par :
- la cible Makefile `openapi-export`,
- la cible Makefile `sdk-python` (`openapi-python-client generate`),
- la cible Makefile `sdk-typescript` (`openapi-typescript`),
- la doc Redoc statique générée pour `docs/api/`.

Pas de network calls — l'OpenAPI est généré à partir de l'objet
`app` FastAPI in-memory via `app.openapi()`.
"""

from __future__ import annotations

import json
from pathlib import Path

from p2p_fraud.api.main import app

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "docs" / "api" / "openapi.json"


def main(out: Path | None = None) -> Path:
    out_path = out or DEFAULT_OUT
    out_path.parent.mkdir(parents=True, exist_ok=True)
    spec = app.openapi()
    out_path.write_text(json.dumps(spec, indent=2, sort_keys=False), encoding="utf-8")
    n_paths = len(spec.get("paths", {}))
    print(f"OpenAPI exporté : {out_path} ({n_paths} endpoints)")
    return out_path


if __name__ == "__main__":
    main()
