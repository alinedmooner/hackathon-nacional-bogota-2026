"""Tool: lookup_record · busca un registro por ID exacto."""

from typing import Any

from config import settings
from datasets import ArchivosDataset, ContratosDataset
from soql_query import SoQLQuery

CONFIG = {
    "contratos": (ContratosDataset.ID, ContratosDataset.ID_CONTRATO),
    "archivos": (ArchivosDataset.ID, ArchivosDataset.ID_DOCUMENTO),
}


def run(args: dict[str, Any]) -> dict:
    dataset_key = args.get("dataset")
    id_value = args.get("id_value")

    if dataset_key not in CONFIG:
        return {"error": f"dataset '{dataset_key}' inválido"}
    if not id_value:
        return {"error": "id_value es obligatorio"}

    dataset_id, id_field = CONFIG[dataset_key]
    q = SoQLQuery(dataset_id).where(f"{id_field} = '{id_value}'").limit(1)
    rows = q.fetch(app_token=settings.socrata_app_token)

    if not rows:
        return {"found": False, "message": f"No se encontró {id_field}={id_value}"}
    return {"found": True, "record": rows[0], "soql_url": q.url()}
