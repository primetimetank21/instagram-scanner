.DEFAULT_GOAL := all
# .SILENT: install

# Variables
DEV = 1
VENV_NAME = .venv
REQUIREMENTS = requirements/common.txt
COMMON_REQUIREMENTS = requirements/common.txt
DEV_REQUIREMENTS = requirements/dev.txt

ifeq ($(DEV), 1)
    REQUIREMENTS = $(DEV_REQUIREMENTS)
    VENV_NAME = .venv_dev
else
    REQUIREMENTS = $(COMMON_REQUIREMENTS)
    VENV_NAME = .venv
endif

PIP = $(VENV_NAME)/bin/pip
PYTHON = $(VENV_NAME)/bin/python
RUFF = $(VENV_NAME)/bin/ruff
MYPY = $(VENV_NAME)/bin/mypy
JUPYTER = $(VENV_NAME)/bin/jupyter
PYTEST = $(VENV_NAME)/bin/pytest
PLAYWRIGHT = $(VENV_NAME)/bin/playwright
MUTE_OUTPUT = 1>/dev/null
ALL_PYTHON_FILES := $$(git ls-files "*.py")
ALL_iPYTHON_FILES := $$(git ls-files "*.ipynb")

# .env variables
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Get dependencies
.PHONY: install
install: $(REQUIREMENTS)
	@ chmod +x ./.github/add_github_hooks.sh && ./.github/add_github_hooks.sh
	@ echo "Installing dependencies... [START]"
	@ $(PIP) install --upgrade pip && \
	$(PIP) install --upgrade wheel && \
	$(PIP) install -r $(REQUIREMENTS) && \
	$(PLAYWRIGHT) install && \
	yes | $(MYPY) --install-types && \
	echo "Installing dependencies... [FINISHED]"
#	@ echo "Installing dependencies... [START]" && \
	$(PIP) install --upgrade pip      $(MUTE_OUTPUT) && \
	$(PIP) install --upgrade wheel    $(MUTE_OUTPUT) && \
	$(PIP) install -r $(REQUIREMENTS) $(MUTE_OUTPUT) && \
	$(PLAYWRIGHT) install $(MUTE_OUTPUT) && \
	$(MYPY) --install-types $(MUTE_OUTPUT) && \
	echo "Installing dependencies... [FINISHED]"

# Create/Activate env; install dependencies
.PHONY: venv/bin/activate
venv/bin/activate: $(REQUIREMENTS)
	@ python3 -m venv $(VENV_NAME) && \
	chmod +x $(VENV_NAME)/bin/activate && \
	. ./$(VENV_NAME)/bin/activate
	@ make install -s

# Activate env
.PHONY: venv
venv: venv/bin/activate
	@ . ./$(VENV_NAME)/bin/activate

# Delete env
.PHONY: delete_venv
delete_venv:
	@ rm -rf $(VENV_NAME)

# Format code for consistency
.PHONY: format
format: venv
	$(RUFF) format $(ALL_PYTHON_FILES)
	$(RUFF) format $(ALL_iPYTHON_FILES)

# Check code for any potential issues
.PHONY: lint
lint: venv
	$(RUFF) check $(ALL_PYTHON_FILES)
	$(MYPY) $(ALL_PYTHON_FILES)

# Check type-hints
.PHONY: type-check
type-check: venv
	@ $(MYPY) $(ALL_PYTHON_FILES)

# Run jupyter
.PHONY: jupyter
jupyter: venv
	@ $(JUPYTER) lab

# Verify code behavior
.PHONY: test
test: venv
	@ echo "TODO: Implement tests"
#	@ $(PYTEST) -vv --cov-report term-missing --cov=. testing/

# Clean up and remove cache files
.PHONY: clean
clean:
	@ find . -type f -name "*.py[co]" -delete -o -type d -name "__pycache__" -delete
	@ dirs=".mypy_cache .pytest_cache .ruff_cache"; \
	for dir in $$dirs; do \
		rm -rf "$$dir"; \
	done
	@ rm .coverage

# Execute all steps
.PHONY: all
all: format lint test