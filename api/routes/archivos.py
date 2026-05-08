from math import ceil

from fastapi import APIRouter, Depends, Query

from datasets import ArchivosDataset
from models.archivo import Archivo
from models.pagination import PaginatedResponse
from security import get_current_user
from soql_query import SoQLQuery

router = APIRouter(prefix="/archivos", tags=["archivos"])


@router.get("", response_model=PaginatedResponse[Archivo])
def listar_archivos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    extension: str | None = Query(None, description="Ej: pdf, xlsx, docx"),
    entidad: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    base = SoQLQuery(ArchivosDataset.ID)

    if extension:
        base = base.where(f"{ArchivosDataset.EXTENSION} = '{extension}'")
    if entidad:
        base = base.where(f"{ArchivosDataset.ENTIDAD} = '{entidad}'")

    total = int(base.copy().select("COUNT(*) AS total").fetch().iloc[0]["total"])

    items = (
        base.copy()
        .limit(page_size)
        .offset((page - 1) * page_size)
        .fetch()
        .to_dict(orient="records")
    )

    return PaginatedResponse(
        items=[Archivo.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size),
    )
