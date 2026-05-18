.PHONY: all pre-commit mypy test test-cov-html test-cov-xml setup-sqlite

CMD:=python -m
PYMODULE:=pyrit
TESTS:=tests

all: pre-commit

pre-commit:
	$(CMD) isort --multi-line 3 --recursive $(PYMODULE) $(TESTS)
	pre-commit run --all-files

mypy:
	$(CMD) mypy $(PYMODULE) $(TESTS)

test:
	$(CMD) pytest --cov=$(PYMODULE) $(TESTS)

test-cov-html:
	$(CMD) pytest --cov=$(PYMODULE) $(TESTS) --cov-report html

test-cov-xml:
	$(CMD) pytest --cov=$(PYMODULE) $(TESTS) --cov-report xml --junitxml=junit/test-results.xml --doctest-modules

setup-sqlite:
	@echo "Detecting OS and running SQLite installer..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		powershell -ExecutionPolicy Bypass -File samples/security-evaluator/scripts/installers/setup_sqlite_windows.ps1; \
	else \
		bash samples/security-evaluator/scripts/installers/setup_sqlite_linux.sh; \
	fi
