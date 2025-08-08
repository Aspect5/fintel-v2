PY?=python3

.PHONY: lint-py deadcode-py

lint-py:
	$(PY) -m ruff check .

deadcode-py:
	$(PY) -m vulture . --min-confidence 70

