from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from models.pagination import PaginatedResponse
from src.core.security import get_current_user
from src.contracts import service as contratos_service

router = APIRouter(prefix="/contratos-local", tags=["contratos-local"])


@router.get("", response_model=PaginatedResponse[Dict[str, Any]])
def listar_contratos_mongo(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    estado: Optional[str] = Query(None),
    departamento: Optional[str] = Query(None),
    tipo_de_contrato: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    return contratos_service.listar_local(page, page_size, estado, departamento, tipo_de_contrato)
