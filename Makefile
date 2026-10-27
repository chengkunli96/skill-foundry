.PHONY: check
check:
	python3 scripts/check.py
	python3 -m unittest discover -s tests -v
