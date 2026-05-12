# Makefile reproductible — installations, tests, benchmarks, lint, build.

.PHONY: help install test lint format bench bench-f1 docs clean dataset-50k \
        openapi-export sdk-python sdk-typescript

help:
	@echo "Cibles disponibles :"
	@echo "  install       Installe le package et les deps dev"
	@echo "  test          pytest"
	@echo "  lint          ruff check"
	@echo "  format        ruff format"
	@echo "  bench         Benchmark perf end-to-end (50k factures par défaut)"
	@echo "  bench-f1      Benchmark F1 par détecteur sur ground truth"
	@echo "  dataset-50k   Génère un dataset synthétique 50k factures"
	@echo "  docs          Build MkDocs (HTML local)"
	@echo "  docs-serve    Lance le serveur local MkDocs"
	@echo "  clean         Supprime build/cache"

install:
	pip install -e ".[dev]"

test:
	python -m pytest -q

lint:
	python -m ruff check src/ tests/ pages/ scripts/

format:
	python -m ruff format src/ tests/ pages/ scripts/

bench:
	python scripts/bench_pipeline.py --rows 50000 --vendors 5000 --skip-iforest

bench-f1:
	python scripts/benchmark_f1.py --rows 50000 --vendors 5000 --seed 42 --output docs/benchmark_results.json

dataset-50k:
	python -m p2p_fraud.synthetic.generator --rows 50000 --vendors 5000 --seed 42 \
		--output data/synthetic/dataset_50k.csv

docs:
	mkdocs build

docs-serve:
	mkdocs serve

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .ruff_cache/ site/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# ─── P5-3 : OpenAPI export + SDKs Python/TypeScript ──────────────────────────

openapi-export:
	python scripts/export_openapi.py

# SDK Python via openapi-python-client — installer manuellement avant :
#   pip install openapi-python-client
# La cible produit `sdks/python/` complet, à publier ensuite manuellement
# sur PyPI au tag v0.5.0 :
#   cd sdks/python && python -m build && twine upload dist/*
sdk-python: openapi-export
	@echo "Génération SDK Python (openapi-python-client)..."
	@command -v openapi-python-client >/dev/null || { \
		echo "openapi-python-client absent. Installer : pip install openapi-python-client"; \
		exit 1; \
	}
	@rm -rf sdks/python
	@mkdir -p sdks
	openapi-python-client generate \
		--path docs/api/openapi.json \
		--output-path sdks/python \
		--meta poetry
	@echo "SDK Python généré : sdks/python/"

# SDK TypeScript via openapi-typescript — installer Node + npx avant.
# Produit `sdks/typescript/src/api.ts` (types-only). Publier ensuite :
#   cd sdks/typescript && npm install && npm run build && npm publish
sdk-typescript: openapi-export
	@echo "Génération SDK TypeScript (openapi-typescript)..."
	@command -v npx >/dev/null || { echo "npx absent (installer Node 20+)"; exit 1; }
	@mkdir -p sdks/typescript/src
	npx --yes openapi-typescript@7 docs/api/openapi.json \
		--output sdks/typescript/src/api.ts
	@echo "SDK TypeScript généré : sdks/typescript/src/api.ts"
