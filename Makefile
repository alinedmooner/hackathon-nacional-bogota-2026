.PHONY: build build-back build-front deploy all

# Construir todos los servicios (backend y frontend)
build:
	docker compose build

# Construir el backend individualmente
build-back:
	docker compose build api

# Construir el frontend individualmente
build-front:
	docker compose build frontend

# Desplegar todo el stack unificado (frontend + api + mongo)
deploy:
	docker stack deploy -c docker-compose.yml hackathon

all: build deploy

# ------------------------------------------------------------------ #
# Linting
# ------------------------------------------------------------------ #

lint-back:
	cd api && ~/.pyenv/shims/python -m ruff check .

lint-front:
	cd web && pnpm run lint

lint: lint-back lint-front

# ------------------------------------------------------------------ #
# Testing
# ------------------------------------------------------------------ #

test-back:
	cd api && ~/.pyenv/shims/python -m pytest

test-front:
	cd web && pnpm run test -- --watch=false --browsers=ChromeHeadless

test: test-back test-front
