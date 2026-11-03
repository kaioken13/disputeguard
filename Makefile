# Define os caminhos diretos dos binários da virtualenv
VENV = .venv
BIN = $(VENV)/bin
PYTHON = $(BIN)/python
PIP = $(BIN)/pip
PYTEST = $(BIN)/pytest
RUFF = $(BIN)/ruff
MYPY = $(BIN)/mypy
UVICORN = $(BIN)/uvicorn

.PHONY: help install lint format test check dev clean

help:
	@echo "Comandos disponíveis no DisputeGuard:"
	@echo "  make install  - Instala/atualiza o projeto e dependências de dev na .venv"
	@echo "  make lint     - Executa o Ruff (linter) e o Mypy (tipagem estrita)"
	@echo "  make format   - Aplica formatação e correções automáticas de código via Ruff"
	@echo "  make test     - Roda toda a suíte de testes unitários e de integração"
	@echo "  make check    - Executa format + lint + test em sequência (pipeline local)"
	@echo "  make dev      - Inicia a API com recarregamento automático (Uvicorn)"
	@echo "  make clean    - Remove caches do Python, pytest, mypy e ruff"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	$(PIP) install httpx

lint:
	$(RUFF) check src/ tests/
	$(MYPY) src/ --ignore-missing-imports

format:
	$(RUFF) check --fix src/ tests/
	$(RUFF) format src/ tests/

test:
	$(PYTEST) tests/ -v

check: format lint test

dev:
	$(UVICORN) src.main:app --reload --host 0.0.0.0 --port 8000

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__ src/__pycache__ tests/__pycache__
