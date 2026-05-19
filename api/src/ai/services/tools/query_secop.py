"""Tool: query_secop · ejecuta un SoQL parametrizado contra Socrata."""

from typing import Any

from src.core.config import settings
from src.core.datasets import ArchivosDataset, ContratosDataset
from src.core.soql_query import SoQLQuery

DATASETS = {
    "contratos": ContratosDataset.ID,
    "archivos": ArchivosDataset.ID,
}

MAX_LIMIT = 1000
DEFAULT_LIMIT = 100


def run(args: dict[str, Any]) -> dict:
    dataset_key = args.get("dataset")
    if dataset_key not in DATASETS:
        return {"error": f"dataset '{dataset_key}' inválido. Usa 'contratos' o 'archivos'."}

    select = args.get("select")
    if not select:
        return {"error": "el campo 'select' es obligatorio"}

    q = SoQLQuery(DATASETS[dataset_key]).select(select)

    if where := args.get("where"):
        q = q.where(where)
    if group := args.get("group_by"):
        q = q.group_by(*[c.strip() for c in group.split(",") if c.strip()])
    if order := args.get("order"):
        # parse "campo DESC" o "campo"
        parts = order.strip().split()
        col = parts[0]
        desc = len(parts) > 1 and parts[1].upper() == "DESC"
        q = q.order_by(col, desc=desc)

    limit = min(int(args.get("limit") or DEFAULT_LIMIT), MAX_LIMIT)
    q = q.limit(limit)

    rows = q.fetch(app_token=settings.socrata_app_token)
    return {
        "rows": rows,
        "row_count": len(rows),
        "soql_url": q.url(),
    }
