"""Tool: check_fines · cruza Multas SECOP I × SECOP II para detectar multados que siguen contratando."""

from typing import Any

from src.core.repositories import radar_repo


def run(args: dict[str, Any]) -> dict:
    documento = (args.get("documento") or "").strip()
    entity_nit = (args.get("entity_nit") or "").strip()
    entity_name = (args.get("entity_name") or "").lower().strip()
    limit = min(int(args.get("limit") or 20), 100)

    if not radar_repo.available().get("multas"):
        return {"error": "Dataset Multas SECOP I no disponible."}

    all_rows = radar_repo.multados_activos(limit=500, offset=0)

    if documento:
        doc_norm = "".join(c for c in documento if c.isdigit())
        all_rows = [r for r in all_rows if r.get("documento") == doc_norm]
    if entity_nit:
        nit_norm = "".join(c for c in entity_nit if c.isdigit())
        all_rows = [r for r in all_rows
                    if "".join(c for c in (r.get("nit_entidad") or "") if c.isdigit()) == nit_norm]
    if entity_name:
        all_rows = [r for r in all_rows
                    if entity_name in (r.get("entidad_contratante") or "").lower()
                    or entity_name in (r.get("entidad_que_multo") or "").lower()]

    hallazgos = all_rows[:limit]
    valor_multas = sum(r.get("valor_sancion") or 0 for r in hallazgos)
    valor_contratos = sum(r.get("valor_contrato") or 0 for r in hallazgos)

    return {
        "tipo_alerta": "multado_activo",
        "descripcion": "Contratistas sancionados con multa en SECOP I que firmaron nuevos contratos después de la multa",
        "resumen": {
            "total_contratistas": len({r["documento"] for r in hallazgos}),
            "total_contratos_posteriores": len(hallazgos),
            "valor_total_multas_cop": round(valor_multas, 0),
            "valor_total_contratos_posteriores_cop": round(valor_contratos, 0),
        },
        "hallazgos": hallazgos,
        "fuente": "Multas SECOP I × SECOP II",
        "nota": "url_evidencia en cada hallazgo apunta directamente al proceso en contratos.gov.co",
    }
