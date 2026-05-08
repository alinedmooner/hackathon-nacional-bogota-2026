from math import ceil
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from db import get_db
from models.pagination import PaginatedResponse
from security import get_current_user

router = APIRouter(prefix="/contratos-local", tags=["contratos-local"])

COLLECTION = "contratos-electronicos"


def serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("", response_model=PaginatedResponse[Dict[str, Any]])
def listar_contratos_mongo(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    estado: Optional[str] = Query(None, description="Ej: terminado, En ejecución"),
    departamento: Optional[str] = Query(None),
    tipo_de_contrato: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    col = get_db()[COLLECTION]

    filtro = {}
    if estado:
        filtro["estado_contrato"] = estado
    if departamento:
        filtro["departamento"] = departamento
    if tipo_de_contrato:
        filtro["tipo_de_contrato"] = tipo_de_contrato

    total = col.count_documents(filtro)
    items = [
        serialize(doc)
        for doc in col.find(filtro).skip((page - 1) * page_size).limit(page_size)
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size) if total else 0,
    )
