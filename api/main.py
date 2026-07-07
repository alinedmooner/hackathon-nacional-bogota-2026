from datetime import datetime
from typing import Any, Dict, List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.auth.router import router as auth_router
from src.contracts.router import router as contratos_router
from src.contracts.router_mongo import router as contratos_mongo_router
from src.contracts.router_archivos import router as archivos_router
from src.analytics.router import router as analytics_router
from src.analytics.router_paso1 import router as analytics_paso1_router
from src.ai.router import router as ai_router
from src.analytics.radar import router as radar_router
from src.core.security import get_current_user
from src.database import get_db

app = FastAPI(
    title="SECOP API",
    version="1.0.0",
    description="API para consultar contratos y archivos SECOP II con JWT.",
)

# ------------------------------------------------------------------ #
# CORS                                                                 #
# ------------------------------------------------------------------ #

cors_origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
# Routers                                                              #
# ------------------------------------------------------------------ #

app.include_router(auth_router)
app.include_router(contratos_router)
app.include_router(contratos_mongo_router)
app.include_router(archivos_router)
app.include_router(analytics_router)
app.include_router(analytics_paso1_router)
app.include_router(ai_router)
app.include_router(radar_router)

# ------------------------------------------------------------------ #
# Rutas públicas                                                       #
# ------------------------------------------------------------------ #

@app.get("/", summary="Root", description="Estado basico del servicio.")
def root():
    return {"status": "ok", "service": "SECOP API", "version": "1.0.0"}

@app.get("/health", summary="Healthcheck", description="Verifica salud del API y MongoDB.")
def health():
    try:
        get_db().command("ping")
        mongo_status = "connected"
    except Exception as e:
        mongo_status = f"error: {e}"
    return {"status": "healthy", "mongo": mongo_status, "timestamp": datetime.now().isoformat()}

# ------------------------------------------------------------------ #
# Rutas protegidas (requieren JWT)                                     #
# ------------------------------------------------------------------ #

@app.get(
    "/results",
    response_model=List[Dict[str, Any]],
    summary="Resultados del analizador",
    description="Retorna resultados recientes almacenados en MongoDB. Requiere JWT.",
)
def get_results(limit: int = 10, current_user: dict = Depends(get_current_user)):
    db = get_db()
    results = list(db["results"].find().sort("timestamp", -1).limit(limit))
    for r in results:
        r["_id"] = str(r["_id"])
        if "timestamp" in r and hasattr(r["timestamp"], "isoformat"):
            r["timestamp"] = r["timestamp"].isoformat()
    return results

@app.get(
    "/me",
    summary="Perfil actual",
    description="Retorna el payload decodificado del JWT. Requiere JWT.",
)
def me(current_user: dict = Depends(get_current_user)):
    return current_user
