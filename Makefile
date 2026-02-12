.PHONY: help
help: ## Show this help documentation
	@sed -ne '/@sed/!s/#! //p' $(MAKEFILE_LIST)
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST) | column -t -s ":" # In this way, `column` works on MacOS too


.PHONY: install
install: ## Install all dependencies
	uv sync --all-groups

.PHONY: run
run: ## Run the main application
	uv run streamlit run src/app.py

.PHONY: test
test: ## Run all tests
	uv run pytest

.PHONY: coverage
coverage: ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

.PHONY: format
format: ## Format code with Black and Ruff
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/

.PHONY: lint
lint: ## Lint code with Ruff
	uv run ruff check src/ tests/

.PHONY: type-check
type-check: ## Type check code with Mypy
	uv run mypy src/

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

.PHONY: clean
clean: ## Clean up build artifacts and caches
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
