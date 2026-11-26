# Thin wrapper around scripts/dev.py, which does the real work on every OS.
# Windows without make: run `python scripts/dev.py <target>` instead.
PYTHON ?= python3

.PHONY: up down smoke reset migrate ps logs
up down smoke reset migrate ps logs:
	$(PYTHON) scripts/dev.py $@
