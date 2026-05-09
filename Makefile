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
