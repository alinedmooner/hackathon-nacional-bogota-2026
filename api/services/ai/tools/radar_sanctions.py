"""Tool: check_active_sanctions · cruza SIRI × SECOP para detectar inhabilitados contratando."""

from typing import Any

from repositories import radar_repo


def run(args: dict[str, Any]) -> dict:
    documento = (args.get("documento") or "").strip()
    entity_nit = (args.get("entity_nit") or "").strip()
    entity_name = (args.get("entity_name") or "").lower().strip()
    limit = min(int(args.get("limit") or 20), 100)

    if not radar_repo.available().get("siri"):
        return {"error": "Dataset SIRI no disponible. Ejecuta el script de descarga primero."}

    # Carga todos los matches y filtra en Python (máx 59 registros en total)
    all_rows = radar_repo.sancionados_activos(limit=500, offset=0)

    if documento:
        doc_norm = "".join(c for c in documento if c.isdigit())
        all_rows = [r for r in all_rows if r.get("documento") == doc_norm]
    if entity_nit:
        nit_norm = "".join(c for c in entity_nit if c.isdigit())
        all_rows = [r for r in all_rows
                    if "".join(c for c in (r.get("nit_entidad") or "") if c.isdigit()) == nit_norm]
    if entity_name:
        all_rows = [r for r in all_rows
                    if entity_name in (r.get("nombre_entidad") or "").lower()]

    hallazgos = all_rows[:limit]
    valor_total = sum(r.get("valor_contrato") or 0 for r in hallazgos)
    personas = len({r["documento"] for r in hallazgos})

    # Añadir URL pública verificable en SECOP II (datos abiertos)
    for h in hallazgos:
        cid = (h.get("id_contrato") or "").replace("'", "")
        h["url_secop"] = (
            f"https://www.datos.gov.co/resource/jbjy-vk9h.json"
            f"?$where=id_contrato='{cid}'"
        )

    return {
        "tipo_alerta": "sancionado_activo",
        "descripcion": "Personas con inhabilitación SIRI vigente que firmaron contratos durante ese período",
        "resumen": {
            "total_personas": personas,
            "total_contratos": len(hallazgos),
            "valor_total_cop": round(valor_total, 0),
        },
        "hallazgos": hallazgos,
        "fuente": "SIRI (Procuraduría) × SECOP II",
        "nota_verificacion": "Cada hallazgo incluye url_secop con enlace directo al contrato en datos.gov.co",
    }
