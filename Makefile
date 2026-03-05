# ============== VARIABLES ==============
INFRA := db adminer mailcatcher
APP := frontend backend
DEV := $(INFRA) $(APP)

# ============== HELP ==============
.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development:"
	@echo "  dev       Start all services with watch (frontend :3000, backend :8000; no proxy, no port 80)"
	@echo "  dev-full  Start all services with proxy (production-like, requires port 80)"
	@echo "  dev-fe     Start frontend only"
	@echo "  dev-be     Start backend only"
	@echo "  up         Start infrastructure only"
	@echo "  down       Stop all services"
	@echo "  logs      View logs (follow; holds compose lock)"
	@echo "  logs-tail View last 200 log lines (one-shot; use in another terminal while dev runs)"
	@echo "  ps        Show running containers"
	@echo ""
	@echo "Database:"
	@echo "  migrate           Run pending migrations"
	@echo "  migrate-fresh     Drop all tables, re-run all (stamp + downgrade + upgrade)"
	@echo "  migrate-rollback  Rollback last migration"
	@echo "  migrate-reset     Rollback all migrations"
	@echo "  migrate-status    Show current revision"
	@echo "  migrate-stamp     Mark DB at head without running migrations"
	@echo "  migration         Generate migration (e.g. make migration create_users_table)"
	@echo "  seed              Seed database"
	@echo "  db-reset          Delete DB volume and run prestart"
	@echo ""
	@echo "Tools:"
	@echo "  test             Run all tests (backend + frontend)"
	@echo "  test-cov         Backend tests with coverage"
	@echo "  test-cov-100     Backend coverage, fail if < 100%"
	@echo "  test-unit        Frontend unit tests with coverage"
	@echo "  test-unit-ui     Frontend unit tests (Vitest UI)"
	@echo "  test-e2e         E2E tests (Playwright)"
	@echo "  lint             Lint frontend + backend"
	@echo "  format           Format backend (ruff)"
	@echo "  build            Build images"
	@echo "  clean            Remove generated files and deps"

# ============== DEVELOPMENT ==============
.PHONY: dev
dev: up kill-watch
	docker compose watch

.PHONY: dev-full
dev-full:
	docker compose up -d $(DEV)
	@echo "Waiting for services..." && for i in $$(seq 1 60); do docker compose ps frontend backend 2>/dev/null | grep -q "Up" && break || sleep 2; done

.PHONY: dev-fe
dev-fe:
	docker compose up -d frontend

.PHONY: dev-be
dev-be:
	docker compose up -d backend

.PHONY: up
up:
	docker compose up -d $(INFRA) --remove-orphans

# Release project lock: Docker Compose watch does not always release lock on Ctrl+C
# or terminal close (see docker/compose#11069). (1) Linux: kill watch process with
# cwd=this project. (2) macOS fallback: run watch --no-up in background, parse
# "PID X is still running" or kill the background job after 2s so we don't leave it running.
kill-watch:
	@./scripts/kill-watch.sh

.PHONY: down
down: kill-watch
	docker compose --profile proxy --profile tools down --remove-orphans

.PHONY: logs
logs:
	docker compose logs -f

.PHONY: logs-tail
logs-tail:
	docker compose logs --tail=200

.PHONY: ps
ps:
	docker compose ps

# ============== DATABASE ==============

.PHONY: migrate
migrate:
	@current=$$(docker compose exec -T backend alembic current 2>/dev/null | tail -1); \
	head=$$(docker compose exec -T backend alembic heads 2>/dev/null | tail -1); \
	if [ "$$current" = "$$head" ] && [ -n "$$head" ]; then \
	  echo "Nothing to migrate. Already up to date."; \
	else \
	  docker compose exec -T backend alembic upgrade head; \
	fi

# Refresh DB = reset (downgrade base) + migrate (upgrade head).
# Stamp head first so if DB has old tables but alembic_version is wrong/empty, downgrade still works.
.PHONY: migrate-fresh
migrate-fresh:
	docker compose exec -T backend alembic stamp head
	docker compose exec -T backend sh -c 'while rev=$$(alembic current 2>/dev/null | tail -1) && [ -n "$$rev" ]; do alembic downgrade -1; done'
	docker compose exec -T backend alembic upgrade head

.PHONY: migrate-rollback
migrate-rollback:
	@current=$$(docker compose exec -T backend alembic current 2>/dev/null | tail -1); \
	if [ -z "$$current" ]; then \
	  echo "Nothing to roll back. Already at base."; \
	else \
	  docker compose exec -T backend alembic downgrade -1; \
	fi

# Reset only: bring DB to base (step-by-step downgrade). Don't re-run migrate.
# Use repeated downgrade -1 instead of "downgrade base" to avoid "0 found" error when deleting rows in alembic_version.
.PHONY: migrate-reset
migrate-reset:
	@current=$$(docker compose exec -T backend alembic current 2>/dev/null | tail -1); \
	if [ -z "$$current" ]; then \
	  echo "Already at base. Nothing to reset."; \
	else \
	  docker compose exec -T backend sh -c 'while rev=$$(alembic current 2>/dev/null | tail -1) && [ -n "$$rev" ]; do alembic downgrade -1; done'; \
	fi

.PHONY: db-reset
db-reset:
	docker compose stop db
	docker volume rm fastapi-nextjs-template_app-db-data 2>/dev/null || true
	docker compose up -d db
	@echo "Waiting for DB..." && for i in $$(seq 1 30); do docker compose ps db 2>/dev/null | grep -q "healthy\|Up" && break || sleep 2; done
	docker compose run --rm prestart

.PHONY: migrate-status
migrate-status:
	docker compose exec -T backend alembic current

.PHONY: migrate-stamp
migrate-stamp:
	docker compose exec -T backend alembic stamp head

.PHONY: migration
migration:
	@M="$(word 2,$(MAKECMDGOALS))"; \
	if [ -z "$$M" ]; then echo "Usage: make migration create_users_table"; exit 1; fi; \
	docker compose exec -T --user $$(id -u):$$(id -g) backend alembic revision --autogenerate -m "$$M"

.PHONY: seed
seed:
	docker compose exec -T -e PYTHONPATH=/app/backend backend python app/initial_data.py

# Test DB: name = MYSQL_DATABASE from .env + _test (scripts read .env). Override: make test MYSQL_TEST_DATABASE=xxx_test
MYSQL_TEST_DATABASE ?= app_test

# ============== TOOLS ==============

.PHONY: test
test:
	./scripts/run-backend-tests.sh cov
	. ./.env 2>/dev/null || true; \
	docker compose exec -T \
		-e FIRST_SUPERUSER="$$FIRST_SUPERUSER" \
		-e FIRST_SUPERUSER_PASSWORD="$$FIRST_SUPERUSER_PASSWORD" \
		-e VITEST_COVERAGE_DIR=/tmp/frontend-coverage \
		frontend sh -c 'cd /app/frontend && bun install && bun run test:coverage'

.PHONY: test-unit
test-unit:
	docker compose exec -T -e VITEST_COVERAGE_DIR=/tmp/frontend-coverage frontend sh -c 'cd /app/frontend && bun install && bun run test:coverage'

.PHONY: test-unit-ui
test-unit-ui:
	docker compose exec -T frontend sh -c 'cd /app/frontend && bun install && bun run test:ui'

# Component/browser tests disabled (path alias issue). Use test-e2e for E2E.
.PHONY: test-browser
test-browser:
	@echo "Browser tests disabled. Run E2E instead: make test-e2e"

# E2E: ensure backend is up so run container joins same network and can resolve "backend". FIRST_SUPERUSER from .env.
# Use --no-recreate on up and --no-deps on run so existing backend (e.g. from make dev) is not recreated.
.PHONY: test-e2e
test-e2e:
	docker compose up -d --no-recreate --wait backend
	docker compose up -d --no-recreate mailcatcher
	if [ -t 1 ]; then \
	  docker compose run --rm --no-deps -t -e CI=0 playwright bun run test:e2e -- --reporter=list --max-failures=1 --retries=0; \
	else \
	  docker compose run --rm --no-deps -e CI=0 playwright bun run test:e2e -- --reporter=list --max-failures=1 --retries=0; \
	fi

.PHONY: test-cov
test-cov:
	./scripts/run-backend-tests.sh cov

.PHONY: test-cov-100
test-cov-100:
	./scripts/run-backend-tests.sh cov-100

.PHONY: lint
lint:
	docker compose exec -T frontend bun run lint
	docker compose run --rm --user root -v "$$(pwd)/backend:/app/backend:rw" -w /app/backend -e RUFF_CACHE_DIR=/tmp/.ruff_cache backend ruff check . --fix

.PHONY: format
format:
	docker compose run --rm --user root -v "$$(pwd)/backend:/app/backend:rw" -w /app/backend -e RUFF_CACHE_DIR=/tmp/.ruff_cache backend ruff format .

.PHONY: build
build:
	docker compose build

.PHONY: clean
clean:
	docker compose down
	rm -rf backend/.venv frontend/node_modules node_modules
	@echo "Note: frontend/.next may need manual removal (created by Docker)"

# Catch-all so extra goals (e.g. make migration foo) don't cause "No rule to make target"
%:
	@:
