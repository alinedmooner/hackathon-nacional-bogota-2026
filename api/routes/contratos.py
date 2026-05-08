from math import ceil

from fastapi import APIRouter, Depends, Query

from datasets import ContratosDataset
from models.pagination import PaginatedResponse
from security import get_current_user
from soql_query import SoQLQuery

router = APIRouter(prefix="/contratos", tags=["contratos"])


@router.get("")
def listar_contratos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    estado: str | None = Query(None, description="Ej: En ejecución, Cerrado"),
    departamento: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    base = SoQLQuery(ContratosDataset.ID)

    if estado:
        base = base.where(f"{ContratosDataset.ESTADO_CONTRATO} = '{estado}'")
    if departamento:
        base = base.where(f"{ContratosDataset.DEPARTAMENTO} = '{departamento}'")

    total = base.fetch_count()

    items = (
        base.copy()
        .limit(page_size)
        .offset((page - 1) * page_size)
        .fetch()
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if total else 0,
    }
