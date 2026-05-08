"""Definiciones de tools en formato OpenAI + dispatcher."""

from typing import Any, Callable

from . import query_secop, lookup, cross_datasets, text_search, render_chart


TOOLS_OPENAI: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "query_secop",
            "description": (
                "Consulta el dataset SECOP via SoQL. Usar para preguntas agregadas, "
                "filtradas o de ranking. Devuelve filas como lista de objetos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset": {
                        "type": "string",
                        "enum": ["contratos", "archivos"],
                        "description": "Cuál dataset consultar.",
                    },
                    "select": {
                        "type": "string",
                        "description": "Campos a seleccionar separados por coma. Ej: 'id_contrato, valor_del_contrato'. Para conteos: 'count(*) as total'.",
                    },
                    "where": {
                        "type": "string",
                        "description": "Filtro WHERE en SoQL. Ej: estado_contrato = 'Cerrado'. Strings con comillas simples. Fechas ISO.",
                    },
                    "group_by": {
                        "type": "string",
                        "description": "Campo(s) por los que agrupar. Ej: 'departamento'.",
                    },
                    "order": {
                        "type": "string",
                        "description": "Orden. Ej: 'valor_del_contrato DESC'.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Cantidad máxima de filas. Default 100, máximo 1000.",
                    },
                },
                "required": ["dataset", "select"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_record",
            "description": "Busca un registro por su ID exacto en uno de los datasets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset": {"type": "string", "enum": ["contratos", "archivos"]},
                    "id_value": {"type": "string", "description": "Valor del id (id_contrato o id_documento)."},
                },
                "required": ["dataset", "id_value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cross_datasets",
            "description": (
                "Cruza un proceso entre los dos datasets: devuelve el contrato + la lista de "
                "documentos asociados a ese proceso de compra."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "proceso_de_compra": {"type": "string", "description": "Código del proceso (ej: CO1.BDOS.123456)."},
                },
                "required": ["proceso_de_compra"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "text_search",
            "description": (
                "Búsqueda LIKE en campos de texto libre. Útil para encontrar contratos por tema "
                "(ej: 'aulas', 'medicamentos')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset": {"type": "string", "enum": ["contratos", "archivos"]},
                    "field": {"type": "string", "description": "Campo donde buscar. Ej: objeto_del_contrato, descripci_n, nombre_archivo."},
                    "query": {"type": "string", "description": "Término a buscar (case-insensitive)."},
                    "limit": {"type": "integer", "description": "Default 20, máximo 100."},
                },
                "required": ["dataset", "field", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_chart",
            "description": (
                "Genera un gráfico Chart.js a partir de datos previamente obtenidos. "
                "Devuelve un spec JSON que el frontend renderiza con ng2-charts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "enum": ["bar", "line", "doughnut", "pie"],
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Etiquetas del eje X o de las categorías.",
                    },
                    "values": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Valores numéricos correspondientes a labels.",
                    },
                    "dataset_label": {"type": "string", "description": "Nombre de la serie (ej: 'Total contratos')."},
                    "title": {"type": "string"},
                },
                "required": ["chart_type", "labels", "values", "title"],
            },
        },
    },
]


# Dispatcher: nombre → callable que recibe un dict de args y devuelve un dict
DISPATCH: dict[str, Callable[[dict[str, Any]], dict]] = {
    "query_secop": query_secop.run,
    "lookup_record": lookup.run,
    "cross_datasets": cross_datasets.run,
    "text_search": text_search.run,
    "render_chart": render_chart.run,
}


def run_tool(name: str, arguments: dict[str, Any]) -> dict:
    """Ejecuta una tool por nombre. Devuelve un dict con el resultado o error."""
    fn = DISPATCH.get(name)
    if fn is None:
        return {"error": f"tool '{name}' no existe"}
    try:
        return fn(arguments)
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
