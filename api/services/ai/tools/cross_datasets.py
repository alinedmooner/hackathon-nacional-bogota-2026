"""Tool: cross_datasets · cruza un proceso entre contratos y archivos."""

from typing import Any

from config import settings
from datasets import ArchivosDataset, ContratosDataset
from soql_query import SoQLQuery


def run(args: dict[str, Any]) -> dict:
    proceso = args.get("proceso_de_compra")
    if not proceso:
        return {"error": "proceso_de_compra es obligatorio"}

    contrato_q = (
        SoQLQuery(ContratosDataset.ID)
        .where(f"{ContratosDataset.PROCESO_DE_COMPRA} = '{proceso}'")
        .limit(1)
    )
    contrato_rows = contrato_q.fetch(app_token=settings.socrata_app_token)

    archivos_q = (
        SoQLQuery(ArchivosDataset.ID)
        .where(f"{ArchivosDataset.PROCESO} = '{proceso}'")
        .order_by(ArchivosDataset.FECHA_CARGA, desc=True)
        .limit(50)
    )
    archivos_rows = archivos_q.fetch(app_token=settings.socrata_app_token)

    return {
        "proceso_de_compra": proceso,
        "contrato": contrato_rows[0] if contrato_rows else None,
        "documentos": archivos_rows,
        "documentos_count": len(archivos_rows),
        "soql_contrato_url": contrato_q.url(),
        "soql_archivos_url": archivos_q.url(),
    }
