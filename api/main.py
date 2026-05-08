from datetime import datetime
from typing import Any, Dict, List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

from config import settings
from routes.auth import router as auth_router
from routes.contratos import router as contratos_router
from routes.contratos_mongo import router as contratos_mongo_router
from routes.archivos import router as archivos_router
from routes.analytics import router as analytics_router
from routes.analytics_paso1 import router as analytics_paso1_router
from security import get_current_user

app = FastAPI(title="SECOP API", version="1.0.0")

# ------------------------------------------------------------------ #
# CORS                                                                 #
# ------------------------------------------------------------------ #

cors_origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],  # credentials no es compatible con wildcard
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

# ------------------------------------------------------------------ #
# MongoDB                                                              #
# ------------------------------------------------------------------ #

def get_db():
    client = MongoClient(settings.mongo_uri)
    return client["ai_analyzer"]


# ------------------------------------------------------------------ #
# Rutas públicas                                                       #
# ------------------------------------------------------------------ #

@app.get("/")
def root():
    return {"status": "ok", "service": "SECOP API", "version": "1.0.0"}

@app.get("/health")
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

@app.get("/results", response_model=List[Dict[str, Any]])
def get_results(limit: int = 10, current_user: dict = Depends(get_current_user)):
    db = get_db()
    results = list(db["results"].find().sort("timestamp", -1).limit(limit))
    for r in results:
        r["_id"] = str(r["_id"])
        if "timestamp" in r and hasattr(r["timestamp"], "isoformat"):
            r["timestamp"] = r["timestamp"].isoformat()
    return results

@app.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user
