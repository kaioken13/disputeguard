# Define os caminhos diretos dos binários da virtualenv
VENV = .venv
BIN = $(VENV)/bin
PYTHON = $(BIN)/python
PIP = $(BIN)/pip
PYTEST = $(BIN)/pytest
RUFF = $(BIN)/ruff
MYPY = $(BIN)/mypy
UVICORN = $(BIN)/uvicorn

# Configurações do Docker
DOCKER_COMPOSE = docker compose

.PHONY: help install lint format test check dev clean docker-build docker-up docker-down docker-logs

help:
	@echo "Comandos disponíveis no DisputeGuard:"
	@echo "  make install      - Instala/atualiza dependências na .venv"
	@echo "  make lint         - Roda Ruff e Mypy"
	@echo "  make format       - Formata código com Ruff"
	@echo "  make test         - Roda suíte de testes unitários e de integração"
	@echo "  make check        - Executa format + lint + test"
	@echo "  make dev          - Sobe a API local com recarregamento via Uvicorn"
	@echo "  make clean        - Limpa caches do Python, pytest e linters"
	@echo "  make docker-build - Constrói a imagem Docker da aplicação sem cache"
	@echo "  make docker-up    - Sobe os containers em segundo plano (-d)"
	@echo "  make docker-down  - Para e remove os containers ativos"
	@echo "  make docker-logs  - Exibe os logs em tempo real do container"

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

docker-build:
	$(DOCKER_COMPOSE) build --no-cache

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f

eval:
	$(PYTHON) evaluate.py
