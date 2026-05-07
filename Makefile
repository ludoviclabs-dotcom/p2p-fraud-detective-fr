# Makefile reproductible — installations, tests, benchmarks, lint, build.

.PHONY: help install test lint format bench bench-f1 docs clean dataset-50k

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
