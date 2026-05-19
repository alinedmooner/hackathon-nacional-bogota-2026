from typing import Optional
from fastapi import APIRouter, Depends, Query
from src.core.models.contrato import Contrato
from src.core.models.pagination import PaginatedResponse
from src.core.security import get_current_user
from src.contracts import service as contratos_service

router = APIRouter(prefix="/contratos", tags=["contratos"])


@router.get("", response_model=PaginatedResponse[Contrato],
            summary="Listar contratos SECOP II")
def listar_contratos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    estado: Optional[str] = Query(None),
    departamento: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    return contratos_service.listar_contratos_socrata(page, page_size, estado, departamento)
