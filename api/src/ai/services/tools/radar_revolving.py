"""Tool: check_revolving_door · puerta giratoria (declarante → contratista)."""

from typing import Any

from src.core.repositories import radar_repo


def run(args: dict[str, Any]) -> dict:
    documento   = (args.get("documento") or "").strip()
    entity_nit  = (args.get("entity_nit") or "").strip()
    entity_name = (args.get("entity_name") or "").strip().lower()
    confianza   = (args.get("confianza") or "").strip().lower()
    limit       = int(args.get("limit") or 20)

    todos = radar_repo.puerta_giratoria(limit=500)

    if documento:
        doc_norm = "".join(c for c in documento if c.isdigit())
        todos = [h for h in todos if "".join(c for c in (h.get("documento") or "") if c.isdigit()) == doc_norm]

    if entity_nit:
        nit_norm = "".join(c for c in entity_nit if c.isdigit())
        todos = [h for h in todos if "".join(c for c in (h.get("nit_entidad") or "") if c.isdigit()) == nit_norm]

    if entity_name:
        todos = [
            h for h in todos
            if entity_name in (h.get("entidad_contratante") or "").lower()
            or entity_name in (h.get("entidad_donde_trabaja") or "").lower()
        ]

    if confianza in ("alta", "media"):
        todos = [h for h in todos if h.get("confianza") == confianza]

    hallazgos = todos[:limit]

    personas  = len({h.get("documento") for h in hallazgos})
    valor_total = sum(h.get("valor_contrato") or 0 for h in hallazgos)

    return {
        "tipo_alerta": "ALERTA_AMARILLA",
        "descripcion": (
            "Funcionarios con declaración patrimonial que aparecen como "
            "contratistas de la misma entidad después de declarar."
        ),
        "resumen": {
            "total_personas": personas,
            "total_contratos": len(hallazgos),
            "valor_total_cop": valor_total,
        },
        "hallazgos": hallazgos,
        "fuente": "Declaraciones patrimoniales + SECOP II",
        "nota": (
            "confianza=alta → entidad coincide exactamente. "
            "confianza=media → señal indirecta (participa en sociedades)."
        ),
    }
