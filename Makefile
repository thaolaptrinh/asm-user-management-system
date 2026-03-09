# ============== VARIABLES ==============
DEV_PROJECT  := dev
TEST_PROJECT := test

# Auto-detect host UID/GID for Docker user mapping
HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)

DC        := docker compose --env-file .env
DC_BASE   := $(DC) -f docker/compose.base.yml

DB_CONNECTION ?= mysql
DB_SERVICE    := db-$(DB_CONNECTION)

DC_DEV    := $(DC_BASE) -f docker/compose.dev.yml --profile $(DB_CONNECTION)
DC_TEST   := $(DC_BASE) -f docker/compose.test.yml -p $(TEST_PROJECT)
DC_STAGE  := $(DC_BASE) -f docker/compose.staging.yml
DC_PROD   := $(DC_BASE) -f docker/compose.prod.yml

.SHELL := /bin/bash
.ONESHELL:

.DEFAULT_GOAL := help

.PHONY: help
help:
	@awk 'BEGIN{FS=":.*##"} /^[a-zA-Z_-]+:.*##/{printf "  \033[36m%-20s\033[0m %s\n",$$1,$$2}' $(MAKEFILE_LIST)

# ============== SETUP ==============
.PHONY: init
init: ## First-time setup: copy env, generate secrets
	@cp .env.example .env
	@echo "Generated .env - now run 'make secrets' to fill secrets"

.PHONY: secrets
secrets: ## Generate secure secret values for .env
	@bash scripts/generate-secrets.sh

# ============== DEVELOPMENT ==============
.PHONY: dev
dev: ## Start all services with hot-reload via docker compose watch (blocks terminal)
	$(DC_DEV) watch

.PHONY: dev-build
dev-build: ## Rebuild images then start with hot-reload (NO_CACHE=1 for no-cache)
	$(DC_DEV) build --build-arg USER_ID=$(HOST_UID) --build-arg GROUP_ID=$(HOST_GID) $(if $(NO_CACHE),--no-cache,)
	$(DC_DEV) watch

.PHONY: restart
restart: ## Restart all services
	$(DC_DEV) restart

.PHONY: stop
stop: ## Stop all services
	$(DC_DEV) stop

.PHONY: down
down: ## Stop and remove containers
	$(DC_DEV) down --remove-orphans

.PHONY: clean
clean: ## Stop and remove containers + volumes (DESTRUCTIVE)
	$(DC_DEV) down -v --remove-orphans

.PHONY: ps
ps: ## Show running containers
	$(DC_DEV) ps

# ============== LOGS ==============
.PHONY: logs
logs: ## All logs
	$(DC_DEV) logs -f

.PHONY: logs-be
logs-be: ## Backend logs
	$(DC_DEV) logs -f backend

.PHONY: logs-fe
logs-fe: ## Frontend logs
	$(DC_DEV) logs -f frontend

.PHONY: logs-db
logs-db: ## Database logs
	$(DC_DEV) logs -f $(DB_SERVICE)

# ============== SHELL ACCESS ==============
.PHONY: shell-be
shell-be: ## Open shell in backend container
	$(DC_DEV) exec backend bash

.PHONY: shell-fe
shell-fe: ## Open shell in frontend container
	$(DC_DEV) exec frontend sh

.PHONY: shell-db
shell-db: ## Open database shell (MySQL or PostgreSQL based on DB_CONNECTION)
	@if [ "$(DB_CONNECTION)" = "postgres" ]; then \
		$(DC_DEV) exec $(DB_SERVICE) psql -U $${DB_USERNAME} -d $${DB_DATABASE}; \
	else \
		$(DC_DEV) exec -e MYSQL_PWD="$${DB_PASSWORD}" $(DB_SERVICE) mysql -u$${DB_USERNAME} $${DB_DATABASE}; \
	fi

# ============== DATABASE ==============
.PHONY: migrate
migrate: ## Run pending migrations
	$(DC_DEV) exec backend alembic upgrade head

.PHONY: migrate-fresh
migrate-fresh: ## Drop all tables (bypasses down migrations) and re-run all migrations
	$(DC_DEV) exec backend python -c \
		"from sqlalchemy import create_engine; from app.core.config import settings; from app.db.base import Base; e = create_engine(settings.DATABASE_URL_SYNC); Base.metadata.reflect(bind=e); Base.metadata.drop_all(e); e.dispose()"
	$(DC_DEV) exec backend alembic upgrade head

.PHONY: migrate-rollback
migrate-rollback: ## Rollback the last migration
	$(DC_DEV) exec backend alembic downgrade -1

.PHONY: migrate-reset
migrate-reset: ## Rollback all migrations
	$(DC_DEV) exec backend alembic downgrade base

.PHONY: migrate-refresh
migrate-refresh: ## Rollback all migrations and re-run
	$(DC_DEV) exec backend alembic downgrade base
	$(DC_DEV) exec backend alembic upgrade head

.PHONY: migrate-status
migrate-status: ## Show migration status
	$(DC_DEV) exec backend alembic current -v

.PHONY: migrate-make
migrate-make: ## Create new migration: make migrate-make m="create_users_table"
	$(DC_DEV) exec backend alembic revision --autogenerate -m "$(m)"

.PHONY: seed
seed: ## Seed the database
	$(DC_DEV) exec backend python -m app.db.seed

.PHONY: db-reset
db-reset: ## Reset database: drop, recreate, migrate, seed
	$(DC_DEV) stop $(DB_SERVICE)
	$(DC_DEV) rm -fv $(DB_SERVICE)
	$(DC_DEV) up -d --wait $(DB_SERVICE)
	$(MAKE) migrate-fresh seed

# ============== CODE GENERATION ==============
.PHONY: generate-client
generate-client: ## Generate TypeScript client from OpenAPI (manual, one-time)
	@bash scripts/generate-client.sh

.PHONY: generate-client-watch
generate-client-watch: ## Auto-generate TypeScript client on API changes (dev only)
	$(DC_DEV) up -d codegen

# ============== TESTING ==============
.PHONY: test
test: ## Run all tests
	$(MAKE) test-be
	$(MAKE) test-fe

# Always builds first (Docker cache makes this ~2s when deps unchanged).
# Source code is bind-mounted — changes reflected without rebuild.
.PHONY: test-be
test-be: ## Backend tests with coverage
	$(DC_TEST) --profile $(DB_CONNECTION) up -d --wait $(DB_SERVICE)
	$(DC_TEST) --profile $(DB_CONNECTION) run --build --rm --use-aliases backend \
		sh -c "alembic upgrade head && python -m app.db.seed && pytest tests/ -v --cov=app --cov-report=term-missing"; \
	EXIT=$$?; $(DC_TEST) down; exit $$EXIT

.PHONY: test-be-reset
test-be-reset: ## Backend tests — destroy DB volume after run (fully clean slate)
	$(DC_TEST) --profile $(DB_CONNECTION) up -d --wait $(DB_SERVICE)
	$(DC_TEST) --profile $(DB_CONNECTION) run --build --rm --use-aliases backend \
		sh -c "alembic upgrade head && python -m app.db.seed && pytest tests/ -v --cov=app --cov-report=term-missing"; \
	EXIT=$$?; $(DC_TEST) down -v; exit $$EXIT

.PHONY: test-fe
test-fe: ## Frontend tests with coverage
	$(DC_DEV) exec frontend bun run test:coverage

.PHONY: test-e2e
test-e2e: ## E2E tests - local dev (fast, base image with runtime install)
	$(DC_DEV) --profile e2e up -d --wait
	$(DC_DEV) --profile e2e run --rm playwright

.PHONY: test-e2e-ci
test-e2e-ci: ## E2E tests - CI/CD (deterministic, pre-built Docker image)
	$(DC_TEST) --profile $(DB_CONNECTION) --profile e2e up -d --wait
	$(DC_TEST) --profile e2e run --rm --build playwright; \
	EXIT=$$?; $(DC_TEST) down; exit $$EXIT

# ============== CODE QUALITY ==============
.PHONY: lint
lint: ## Lint backend + frontend
	$(DC_DEV) exec backend ruff check .
	$(DC_DEV) exec frontend bun run lint

.PHONY: lint-be
lint-be: ## Lint backend only
	$(DC_DEV) exec backend ruff check .

.PHONY: lint-fe
lint-fe: ## Lint frontend only
	$(DC_DEV) exec frontend bun run lint

.PHONY: typecheck
typecheck: ## Type-check backend + frontend
	$(DC_DEV) exec backend mypy app
	$(DC_DEV) exec frontend bun run typecheck

.PHONY: typecheck-be
typecheck-be: ## Type-check backend only
	$(DC_DEV) exec backend mypy app

.PHONY: typecheck-fe
typecheck-fe: ## Type-check frontend only
	$(DC_DEV) exec frontend bun run typecheck

.PHONY: check
check: lint typecheck ## Run all checks

# ============== BUILD ==============
.PHONY: build
build: ## Build all images
	$(DC_BASE) --profile $(DB_CONNECTION) build

.PHONY: build-prod
build-prod: ## Build production images
	$(DC_PROD) build

.PHONY: build-no-cache
build-no-cache: ## Build with no cache
	$(DC_BASE) --profile $(DB_CONNECTION) build --no-cache

# ============== UTILITIES ==============
.PHONY: prune
prune: ## Remove unused Docker resources
	docker system prune -f

.PHONY: env
env: ## Show current environment variables
	@echo "APP_ENV=$${APP_ENV:-local}"
	@echo "DB_DATABASE=$${DB_DATABASE:-app}"
