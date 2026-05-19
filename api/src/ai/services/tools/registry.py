"""Definiciones de tools en formato OpenAI + dispatcher."""

from typing import Any, Callable

from . import query_secop, lookup, cross_datasets, text_search, render_chart
from . import radar_sanctions, radar_fines, radar_profile, radar_summary, radar_revolving


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
    # ── Veridia: detección de alertas ────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_alert_summary",
            "description": (
                "Devuelve el resumen ejecutivo global de Veridia: cuántas personas inhabilitadas, "
                "multadas y posibles puertas giratorias hay en el dataset cargado, con valor total COP. "
                "Úsalo al inicio de cualquier investigación para tener contexto del universo."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_active_sanctions",
            "description": (
                "Busca contratistas con inhabilitación vigente en el SIRI (Procuraduría) "
                "que firmaron contratos durante ese período. "
                "Filtra opcionalmente por documento, NIT de entidad o nombre de entidad. "
                "Sin filtros devuelve todos los casos detectados (ordenados por valor)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "documento": {
                        "type": "string",
                        "description": "Cédula o NIT del contratista a verificar. Opcional.",
                    },
                    "entity_nit": {
                        "type": "string",
                        "description": "NIT de la entidad pública a revisar. Opcional.",
                    },
                    "entity_name": {
                        "type": "string",
                        "description": "Nombre parcial de la entidad (case-insensitive). Ej: 'JEP', 'Alcaldía'. Opcional.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Máximo de hallazgos a devolver. Default 20.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_fines",
            "description": (
                "Busca contratistas que fueron sancionados con multa en SECOP I "
                "y continuaron recibiendo contratos después de la multa. "
                "Cada hallazgo incluye url_evidencia con enlace directo al expediente."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "documento": {
                        "type": "string",
                        "description": "Cédula o NIT del contratista a verificar. Opcional.",
                    },
                    "entity_nit": {
                        "type": "string",
                        "description": "NIT de la entidad. Opcional.",
                    },
                    "entity_name": {
                        "type": "string",
                        "description": "Nombre parcial de la entidad. Opcional.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Máximo de hallazgos. Default 20.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_person_profile",
            "description": (
                "Devuelve el perfil unificado de una persona o empresa por documento (cédula o NIT). "
                "Agrega: contratos SECOP, sanciones SIRI, multas SECOP I y declaraciones patrimoniales. "
                "Incluye nivel_alerta: rojo (inhabilitado) | naranja (multado) | amarillo | verde."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "documento": {
                        "type": "string",
                        "description": "Cédula o NIT de la persona o empresa.",
                    },
                },
                "required": ["documento"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_revolving_door",
            "description": (
                "Busca casos de 'puerta giratoria': funcionarios con declaración patrimonial "
                "que aparecen como contratistas de la misma entidad donde trabajaban. "
                "Señal AMARILLA. confianza=alta → entidad coincide exactamente; "
                "confianza=media → persona participa en sociedades (señal indirecta)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "documento": {
                        "type": "string",
                        "description": "Cédula del funcionario/contratista. Opcional.",
                    },
                    "entity_nit": {
                        "type": "string",
                        "description": "NIT de la entidad a revisar. Opcional.",
                    },
                    "entity_name": {
                        "type": "string",
                        "description": "Nombre parcial de la entidad (case-insensitive). Opcional.",
                    },
                    "confianza": {
                        "type": "string",
                        "enum": ["alta", "media"],
                        "description": "Filtrar por nivel de confianza. Opcional.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Máximo de hallazgos. Default 20.",
                    },
                },
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
    "get_alert_summary": radar_summary.run,
    "check_active_sanctions": radar_sanctions.run,
    "check_fines": radar_fines.run,
    "get_person_profile": radar_profile.run,
    "check_revolving_door": radar_revolving.run,
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
