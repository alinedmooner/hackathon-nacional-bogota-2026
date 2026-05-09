from typing import Optional
from fastapi import APIRouter, Depends, Query
from models.archivo import Archivo
from models.pagination import PaginatedResponse
from security import get_current_user
from services import contratos_service

router = APIRouter(prefix="/archivos", tags=["archivos"])


@router.get("", response_model=PaginatedResponse[Archivo],
            summary="Listar archivos SECOP II")
def listar_archivos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    extension: Optional[str] = Query(None),
    entidad: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    return contratos_service.listar_archivos_socrata(page, page_size, extension, entidad)
