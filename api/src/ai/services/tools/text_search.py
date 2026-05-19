"""Tool: text_search · LIKE case-insensitive sobre un campo."""

from typing import Any

from src.core.config import settings
from src.core.datasets import ArchivosDataset, ContratosDataset
from src.core.soql_query import SoQLQuery

DATASETS = {
    "contratos": ContratosDataset.ID,
    "archivos": ArchivosDataset.ID,
}

MAX_LIMIT = 100


def run(args: dict[str, Any]) -> dict:
    dataset_key = args.get("dataset")
    field = args.get("field")
    query = args.get("query")
    limit = min(int(args.get("limit") or 20), MAX_LIMIT)

    if dataset_key not in DATASETS:
        return {"error": f"dataset '{dataset_key}' inválido"}
    if not field or not query:
        return {"error": "field y query son obligatorios"}

    safe_query = query.replace("'", "''")
    q = (
        SoQLQuery(DATASETS[dataset_key])
        .where(f"upper({field}) like upper('%{safe_query}%')")
        .limit(limit)
    )
    rows = q.fetch(app_token=settings.socrata_app_token)
    return {
        "rows": rows,
        "row_count": len(rows),
        "soql_url": q.url(),
    }
