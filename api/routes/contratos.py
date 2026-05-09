from typing import Optional
from fastapi import APIRouter, Depends, Query
from models.contrato import Contrato
from models.pagination import PaginatedResponse
from security import get_current_user
from services import contratos_service

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
