# Hackathon 5.0 - SECOP Analytics

Plataforma para consultar datos de SECOP II, autenticar usuarios con JWT y visualizar graficas en un dashboard Angular.

## Arquitectura

- API: FastAPI (Python) en [api](api) con endpoints protegidos por JWT.
- Frontend: Angular 17 en [frontend](frontend), consume la API via `/api` y proxy local.
- Datos: consultas SoQL contra datos.gov.co (datasets SECOP II).
- AI Analyzer: servicio auxiliar en [ai-analyzer](ai-analyzer) (no expone API pública).

## Requisitos

- Python 3.11+
- Node.js 18+
- MongoDB (si usas `/results` del analizador)
- Docker (opcional)

## Ejecutar en local

### Backend (API)

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend (Angular)

```bash
cd frontend
npm install
npm start
```

El frontend queda en `http://localhost:4200` y el backend en `http://localhost:8000`.

## Ejecutar con Docker (solo API)

El `docker-compose.yml` actual levanta unicamente la API.

```bash
docker compose up --build
```

## Configuracion

### Backend

Variables en [api/.env](api/.env):

- `MONGO_URI`
- `DATASET_CONTRATOS_ID`
- `DATASET_ARCHIVOS_ID`
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`
- `CORS_ORIGINS`

### Frontend

El runtime config vive en [frontend/src/assets/env.js](frontend/src/assets/env.js). Por defecto usa `/api`.
El proxy local esta en [frontend/proxy.conf.json](frontend/proxy.conf.json).

## Autenticacion

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

### Parametros comunes

- `page` (default: 1)
- `page_size` (default: 20, max: 1000)

Filtros:

- `/contratos`: `estado`, `departamento`
- `/archivos`: `extension`, `entidad`

## Swagger

La documentacion OpenAPI esta en:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

En produccion, el backend esta en `https://gludsitohackathon5back.glud.org` y la
documentacion es `https://gludsitohackathon5back.glud.org/docs`. Este enlace debe
mostrarse en el login.
