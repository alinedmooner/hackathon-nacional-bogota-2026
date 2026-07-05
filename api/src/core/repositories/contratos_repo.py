from math import ceil
from typing import Any, Optional
from src.database import get_db

COLLECTION = "contratos-electronicos"


def _col():
    return get_db()[COLLECTION]


def _serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


def listar(
    page: int,
    page_size: int,
    estado: Optional[str] = None,
    departamento: Optional[str] = None,
    tipo_de_contrato: Optional[str] = None,
) -> dict[str, Any]:
    filtro = {}
    if estado:
        filtro["estado_contrato"] = estado
    if departamento:
        filtro["departamento"] = departamento
    if tipo_de_contrato:
        filtro["tipo_de_contrato"] = tipo_de_contrato

    col = _col()
    # ⚡ Bolt: Optimize by using estimated_document_count when no filter is applied
    if not filtro:
        total = col.estimated_document_count()
    else:
        total = col.count_documents(filtro)

    items = [
        _serialize(doc)
        for doc in col.find(filtro).skip((page - 1) * page_size).limit(page_size)
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if total else 0,
    }
