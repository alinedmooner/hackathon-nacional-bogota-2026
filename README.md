# Hackathon 5.0 - SECOP Analytics

Plataforma para consultar datos de SECOP II, autenticar usuarios con JWT y visualizar graficas en un dashboard Angular.

## Arquitectura

- **API:** FastAPI (Python) en `api/` con endpoints protegidos por JWT. Organizado en feature modules (auth, contratos, ai, analytics).
- **Web:** Angular 18 en `web/`, consume la API via `/api` y proxy local.
- **Datos:** Consultas SoQL contra datos.gov.co (datasets SECOP II) y base de datos MongoDB.
- **Documentación:** Las decisiones de diseño de UI y contratos API están detalladas en `docs/ARCHITECTURE.md`. La configuración de IA (Context7) está en `docs/mcp-config.md`.

## Requisitos

- Python 3.11+
- Node.js 18+
- MongoDB (para almacenamiento de logs de análisis)
- Docker (recomendado para desarrollo)

## Ejecutar en local

### Backend (API)

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Angular)

```bash
cd web
npm install
npm start
```

El frontend queda en `http://localhost:4200` y el backend en `http://localhost:8000`.

## Ejecutar con Docker

El `docker-compose.yml` levanta toda la pila (API, Web, MongoDB).

```bash
docker-compose up --build
```

## Configuración

### Backend

Variables necesarias en `api/.env`:

- `MONGO_URI`
- `DATASET_CONTRATOS_ID`
- `DATASET_ARCHIVOS_ID`
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`
- `CORS_ORIGINS`

### Web (Frontend)

El runtime config vive en `web/src/assets/env.js`. Por defecto usa `/api`.
El proxy local está en `web/proxy.conf.json`.

## Autenticación

1. POST `/auth/login` con `{ "username": "admin", "password": "admin123" }`.
2. Usar el JWT en el header: `Authorization: Bearer <token>`.

## Endpoints principales

Base URL: `http://localhost:8000`

- `GET /health` - Salud del servicio
- `POST /auth/login` - Login y JWT
- `GET /contratos` - Lista contratos (paginado, requiere JWT)
- `GET /archivos` - Lista archivos (paginado, requiere JWT)
- `GET /results` - Resultados del analizador (requiere JWT)
- `GET /me` - Payload del JWT actual

## Swagger

La documentación OpenAPI está en:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

En producción, el backend está en `https://gludsitohackathon5back.glud.org` y la documentación es `https://gludsitohackathon5back.glud.org/docs`.
