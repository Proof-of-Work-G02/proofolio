# Thin wrapper around scripts/dev.py, which does the real work on every OS.
# Windows without make: run `python scripts/dev.py <target>` instead.
PYTHON ?= python3

TARGETS := up down smoke reset migrate ps logs contracts-setup contracts-validate contracts-types contracts-check contracts-breaking

.PHONY: $(TARGETS)
$(TARGETS):
	$(PYTHON) scripts/dev.py $@
