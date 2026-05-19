"""Tool: get_person_profile · perfil unificado de un contratista en todos los datasets."""

from typing import Any

from src.core.repositories import radar_repo


def run(args: dict[str, Any]) -> dict:
    documento = (args.get("documento") or "").strip()
    if not documento:
        return {"error": "El campo 'documento' (cédula o NIT) es obligatorio."}

    perfil = radar_repo.perfil_documento(documento)

    if "error" in perfil:
        return perfil

    # Resumen compacto para el agente (el detalle completo está en perfil)
    secop = perfil.get("secop", {})
    siri = perfil.get("siri", [])
    multas = perfil.get("multas", [])
    patrimonio = perfil.get("patrimonio", [])

    alertas = []
    for s in siri:
        alertas.append(
            f"INHABILITACIÓN {s.get('sanciones')} desde {s.get('fecha_inicio')} "
            f"hasta {s.get('fecha_fin') or 'indeterminado'} — {s.get('autoridad')}"
        )
    for m in multas:
        alertas.append(
            f"MULTA de ${m.get('valor_sancion'):,.0f} COP el {m.get('fecha_multa')} "
            f"por {m.get('entidad')} — ver: {m.get('url_evidencia')}"
        )

    return {
        "documento": perfil.get("documento"),
        "nivel_alerta": perfil.get("nivel_alerta"),
        "alertas_activas": alertas,
        "secop_resumen": {
            "total_contratos": secop.get("total_contratos", 0),
            "valor_total_cop": secop.get("valor_total_cop", 0),
            "ultimos_contratos": secop.get("contratos", [])[:5],
        },
        "siri": siri,
        "multas": multas,
        "patrimonio": patrimonio[:3],
    }
