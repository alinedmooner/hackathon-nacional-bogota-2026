"""Tool: get_alert_summary · KPIs globales de los tres tipos de alerta Veridia."""

from typing import Any

from src.core.repositories import radar_repo


def run(args: dict[str, Any]) -> dict:
    resumen = radar_repo.resumen_global()

    san = resumen.get("sancionados_activos", {})
    mul = resumen.get("multados_activos", {})
    pue = resumen.get("puerta_giratoria", {})

    return {
        "descripcion": "Resumen ejecutivo de alertas Veridia sobre el dataset SECOP II cargado",
        "sancionados_activos": {
            **san,
            "interpretacion": (
                f"{san.get('total_personas', 0)} personas con inhabilitación vigente (SIRI) "
                f"firmaron {san.get('total_contratos', 0)} contratos "
                f"por ${san.get('valor_total_cop', 0):,.0f} COP"
            ),
        },
        "multados_activos": {
            **mul,
            "interpretacion": (
                f"{mul.get('total_contratistas', 0)} contratistas sancionados con multa "
                f"siguieron recibiendo {mul.get('total_contratos', 0)} contratos "
                f"por ${mul.get('valor_total_cop', 0):,.0f} COP"
            ),
        },
        "puerta_giratoria": {
            **pue,
            "interpretacion": (
                f"{pue.get('total_personas', 0)} personas con declaración patrimonial activa "
                f"aparecen como contratistas — {pue.get('total_contratos', 0)} contratos "
                f"por ${pue.get('valor_total_cop', 0):,.0f} COP"
            ),
            "nota": "Incluye señal débil (particip_corp_socied_asoc=SI). Filtrar por confianza='alta' para casos verificados.",
        },
        "disponibilidad_datasets": resumen.get("disponibilidad_datasets", {}),
    }
