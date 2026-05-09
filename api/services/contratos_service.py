from math import ceil
from typing import Optional
from repositories import contratos_repo
from datasets import ContratosDataset, ArchivosDataset
from soql_query import SoQLQuery


def listar_local(page: int, page_size: int, estado: Optional[str],
                 departamento: Optional[str], tipo_de_contrato: Optional[str]) -> dict:
    return contratos_repo.listar(page, page_size, estado, departamento, tipo_de_contrato)


def _soql_paginado(dataset_id: str, filtros: list[tuple], page: int, page_size: int) -> dict:
    base = SoQLQuery(dataset_id)
    for field, value in filtros:
        if value:
            base = base.where(f"{field} = '{value}'")
    total = base.fetch_count()
    items = base.copy().limit(page_size).offset((page - 1) * page_size).fetch()
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "pages": ceil(total / page_size) if total else 0}


def listar_contratos_socrata(page: int, page_size: int,
                              estado: Optional[str], departamento: Optional[str]) -> dict:
    return _soql_paginado(
        ContratosDataset.ID,
        [(ContratosDataset.ESTADO_CONTRATO, estado), (ContratosDataset.DEPARTAMENTO, departamento)],
        page, page_size,
    )


def listar_archivos_socrata(page: int, page_size: int,
                             extension: Optional[str], entidad: Optional[str]) -> dict:
    return _soql_paginado(
        ArchivosDataset.ID,
        [(ArchivosDataset.EXTENSION, extension), (ArchivosDataset.ENTIDAD, entidad)],
        page, page_size,
    )
