.DEFAULT_GOAL := all

# Variables
DEV = 1
VENV_NAME = .venv
# REQUIREMENTS = requirements/common.txt
# COMMON_REQUIREMENTS = requirements/common.txt
# DEV_REQUIREMENTS = requirements/dev.txt

MUTE_OUTPUT = 1>/dev/null
ALL_PYTHON_FILES := $$(git ls-files "*.py")

# .env variables
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Get dependencies
.PHONY: install
install:
	@ chmod +x ./.github/add_github_hooks.sh && ./.github/add_github_hooks.sh
#	@ echo "Installing dependencies... [START]" && \
	$(PIP) install --upgrade pip      $(MUTE_OUTPUT) && \
	$(PIP) install --upgrade wheel    $(MUTE_OUTPUT) && \
	$(PIP) install -r $(REQUIREMENTS) $(MUTE_OUTPUT) && \
	$(PLAYWRIGHT) install $(MUTE_OUTPUT) && \
	echo "Installing dependencies... [FINISHED]"
	@ echo "Installing dependencies... [START]"
	uv sync && uv run playwright install
	@ echo "Installing dependencies... [FINISHED]"

# Delete env
.PHONY: delete_venv
delete_venv:
	@ rm -rf $(VENV_NAME)

# Format code for consistency
.PHONY: format
format:
	@ uv run ruff format

# Check code for any potential issues
.PHONY: lint
lint:
	@ uv run ruff check
	@ uv run mypy $(ALL_PYTHON_FILES)

# Check type-hints
.PHONY: type-check
type-check:
	@ uv run mypy $(ALL_PYTHON_FILES)

# Run jupyter
.PHONY: jupyter
jupyter:
	@ uv run jupyter lab

# Verify code behavior
.PHONY: test
test:
	@ echo "TODO: Implement tests"
#	@ uv run pytest -vv --cov-report term-missing --cov=. testing/

# Clean up and remove cache files
.PHONY: clean
clean:
	@ find . -type f -name "*.py[co]" -delete -o -type d -name "__pycache__" -delete
	@ dirs=".mypy_cache .pytest_cache .ruff_cache .ipynb_checkpoints"; \
	for dir in $$dirs; do \
		rm -rf "$$dir"; \
	done
	@ rm -rf .coverage

.PHONY: run
run:
	@ uv run src/main.py

# Execute all steps
.PHONY: all
all: install format lint test