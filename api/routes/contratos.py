from math import ceil
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query

from datasets import ContratosDataset
from models.contrato import Contrato
from models.pagination import PaginatedResponse
from security import get_current_user
from soql_query import SoQLQuery

router = APIRouter(prefix="/contratos", tags=["contratos"])


@router.get("", response_model=PaginatedResponse[Contrato])
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

    total = int(base.copy().select("COUNT(*) AS total").fetch().iloc[0]["total"])

    items = (
        base.copy()
        .limit(page_size)
        .offset((page - 1) * page_size)
        .fetch()
        .to_dict(orient="records")
    )

    return PaginatedResponse(
        items=[Contrato.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size),
    )
