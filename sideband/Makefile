.PHONY: test lint experiments all

test:
	pytest -q

lint:
	python tools/lint_findings.py

experiments:
	python experiments/run_all.py

all: test lint experiments
