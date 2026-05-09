"""Repositorio de detección de alertas para Veridia.

Usa DuckDB con threading.local (mismo patrón que duckdb_repo.py).
Las vistas se crean al primer uso por thread; requiere que los parquets
ya existan en disco. Si falta un parquet, las funciones que lo necesitan
devuelven lista vacía o dict vacío en lugar de lanzar excepción.

Parquets requeridos (rutas configurables por env):
  PARQUET_PATH        → data/contratos.parquet  (existente)
  SIRI_PARQUET_PATH   → data/siri.parquet
  MULTAS_PARQUET_PATH → data/multas_secop1.parquet
  PATRIMONIO_PATH     → data/patrimoniales.parquet
"""
import datetime
import os
import threading
from typing import Any

import duckdb


def _serialize(row: dict) -> dict:
    """Convierte datetime.date/datetime a ISO string para que BSON/JSON lo acepte."""
    return {
        k: v.isoformat() if isinstance(v, (datetime.date, datetime.datetime)) else v
        for k, v in row.items()
    }

CONTRATOS_PATH = os.getenv("PARQUET_PATH", "data/contratos.parquet")
SIRI_PATH = os.getenv("SIRI_PARQUET_PATH", "data/siri.parquet")
MULTAS_PATH = os.getenv("MULTAS_PARQUET_PATH", "data/multas_secop1.parquet")
PATRIMONIO_PATH = os.getenv("PATRIMONIO_PARQUET_PATH", "data/patrimoniales.parquet")

# valor_del_contrato en contratos.parquet viene como string "$40,825,000" del CSV exportado
_VALOR = "TRY_CAST(REGEXP_REPLACE(REGEXP_REPLACE(c.valor_del_contrato, '\\$', ''), ',', '', 'g') AS DOUBLE)"

# fecha_de_firma en contratos.parquet viene como "MM/DD/YYYY" del CSV exportado
_FIRMA_DATE = (
    "CAST("
    "  SUBSTR(c.fecha_de_firma, 7, 4) || '-' ||"
    "  SUBSTR(c.fecha_de_firma, 1, 2) || '-' ||"
    "  SUBSTR(c.fecha_de_firma, 4, 2)"
    "  AS DATE"
    ")"
)

_local = threading.local()


def _get_con() -> duckdb.DuckDBPyConnection:
    if not hasattr(_local, "con"):
        con = duckdb.connect()
        for view, path in (
            ("contratos", CONTRATOS_PATH),
            ("siri", SIRI_PATH),
            ("multas", MULTAS_PATH),
            ("patrimonio", PATRIMONIO_PATH),
        ):
            if os.path.exists(path):
                con.execute(f"CREATE VIEW {view} AS SELECT * FROM read_parquet('{path}')")
        _local.con = con
    return _local.con


def _view_exists(name: str) -> bool:
    try:
        _get_con().execute(f"SELECT 1 FROM {name} LIMIT 0")
        return True
    except Exception:
        return False


def available() -> dict[str, bool]:
    return {
        "contratos": os.path.exists(CONTRATOS_PATH),
        "siri": os.path.exists(SIRI_PATH),
        "multas": os.path.exists(MULTAS_PATH),
        "patrimonio": os.path.exists(PATRIMONIO_PATH),
    }


# ── UC-01: Sancionados activos ────────────────────────────────────────────────

_SQL_SANCIONADOS = f"""
SELECT
    s.numero_identificacion                                   AS documento,
    TRIM(
        COALESCE(s.primer_nombre, '') || ' ' ||
        COALESCE(s.segundo_nombre, '') || ' ' ||
        COALESCE(s.primer_apellido, '') || ' ' ||
        COALESCE(s.segundo_apellido, '')
    )                                                         AS nombre_sancionado,
    s.sanciones,
    s.entidad_sancionado,
    s.autoridad,
    CAST(s.fecha_efectos_juridicos AS DATE)                   AS fecha_inicio_sancion,
    CAST(s.fecha_fin_sancion AS DATE)                         AS fecha_fin_sancion,
    s.duracion_anos,
    c.id_contrato,
    c.fecha_de_firma,
    {_FIRMA_DATE}                                             AS fecha_firma_date,
    {_VALOR}                                                  AS valor_contrato,
    c.proveedor_adjudicado,
    c.nombre_entidad,
    c.nit_entidad,
    c.tipo_de_contrato,
    c.estado_contrato,
    CASE WHEN s.duracion_anos > 0 THEN 'alta' ELSE 'media' END AS confianza
FROM siri s
JOIN contratos c
  ON REGEXP_REPLACE(s.numero_identificacion, '[^0-9]', '', 'g')
   = REGEXP_REPLACE(c.documento_proveedor,   '[^0-9]', '', 'g')
WHERE s.sanciones LIKE '%INHABILIDAD%'
  AND c.documento_proveedor IS NOT NULL
  AND c.fecha_de_firma IS NOT NULL
  AND LENGTH(c.fecha_de_firma) >= 10
  AND {_FIRMA_DATE} >= CAST(s.fecha_efectos_juridicos AS DATE)
  AND (
    s.duracion_anos = 0
    OR {_FIRMA_DATE} <= CAST(
          CAST(s.fecha_efectos_juridicos AS DATE)
          + (CAST(s.duracion_anos AS VARCHAR) || ' years')::INTERVAL
        AS DATE)
  )
"""


def sancionados_activos(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    if not _view_exists("siri") or not _view_exists("contratos"):
        return []
    sql = f"{_SQL_SANCIONADOS} ORDER BY valor_contrato DESC NULLS LAST LIMIT {limit} OFFSET {offset}"
    rows = _get_con().execute(sql).fetchall()
    cols = [
        "documento", "nombre_sancionado", "sanciones", "entidad_sancionado",
        "autoridad", "fecha_inicio_sancion", "fecha_fin_sancion", "duracion_anos",
        "id_contrato", "fecha_de_firma", "fecha_firma_date", "valor_contrato",
        "proveedor_adjudicado", "nombre_entidad", "nit_entidad",
        "tipo_de_contrato", "estado_contrato", "confianza",
    ]
    return [_serialize(dict(zip(cols, r))) for r in rows]


def sancionados_activos_resumen() -> dict[str, Any]:
    if not _view_exists("siri") or not _view_exists("contratos"):
        return {"total_personas": 0, "total_contratos": 0, "valor_total_cop": 0}
    sql = f"""
    SELECT
        COUNT(DISTINCT s.numero_identificacion) AS total_personas,
        COUNT(*)                                AS total_contratos,
        SUM({_VALOR})                           AS valor_total
    FROM ({_SQL_SANCIONADOS}) t
    """
    # _SQL_SANCIONADOS no tiene alias de tabla para siri/contratos cuando se usa en subquery.
    # Re-ejecutamos el conteo directamente:
    sql = f"""
    SELECT
        COUNT(DISTINCT s.numero_identificacion) AS total_personas,
        COUNT(*)                                AS total_contratos,
        COALESCE(SUM({_VALOR}), 0)             AS valor_total
    FROM siri s
    JOIN contratos c
      ON REGEXP_REPLACE(s.numero_identificacion, '[^0-9]', '', 'g')
       = REGEXP_REPLACE(c.documento_proveedor,   '[^0-9]', '', 'g')
    WHERE s.sanciones LIKE '%INHABILIDAD%'
      AND c.documento_proveedor IS NOT NULL
      AND c.fecha_de_firma IS NOT NULL
      AND LENGTH(c.fecha_de_firma) >= 10
      AND {_FIRMA_DATE} >= CAST(s.fecha_efectos_juridicos AS DATE)
      AND (
        s.duracion_anos = 0
        OR {_FIRMA_DATE} <= CAST(
              CAST(s.fecha_efectos_juridicos AS DATE)
              + (CAST(s.duracion_anos AS VARCHAR) || ' years')::INTERVAL
            AS DATE)
      )
    """
    row = _get_con().execute(sql).fetchone()
    return {
        "total_personas": int(row[0] or 0),
        "total_contratos": int(row[1] or 0),
        "valor_total_cop": float(row[2] or 0),
    }


# ── UC-02: Multados activos ────────────────────────────────────────────────────

_SQL_MULTADOS = f"""
SELECT
    m.documento_contratista                                   AS documento,
    m.nombre_contratista,
    m.valor_sancion,
    m.nombre_entidad                                          AS entidad_que_multo,
    m.numero_de_resolucion,
    CAST(m.fecha_de_firmeza AS DATE)                          AS fecha_multa,
    m.ruta_de_proceso                                         AS url_evidencia,
    c.id_contrato,
    c.fecha_de_firma,
    {_FIRMA_DATE}                                             AS fecha_firma_date,
    {_VALOR}                                                  AS valor_contrato,
    c.nombre_entidad                                          AS entidad_contratante,
    c.nit_entidad,
    c.tipo_de_contrato,
    c.estado_contrato,
    'alta'                                                    AS confianza
FROM multas m
JOIN contratos c
  ON REGEXP_REPLACE(m.documento_contratista, '[^0-9]', '', 'g')
   = REGEXP_REPLACE(c.documento_proveedor,   '[^0-9]', '', 'g')
WHERE c.documento_proveedor IS NOT NULL
  AND c.fecha_de_firma IS NOT NULL
  AND LENGTH(c.fecha_de_firma) >= 10
  AND {_FIRMA_DATE} > CAST(m.fecha_de_firmeza AS DATE)
"""


def multados_activos(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    if not _view_exists("multas") or not _view_exists("contratos"):
        return []
    sql = f"{_SQL_MULTADOS} ORDER BY valor_contrato DESC NULLS LAST LIMIT {limit} OFFSET {offset}"
    rows = _get_con().execute(sql).fetchall()
    cols = [
        "documento", "nombre_contratista", "valor_sancion", "entidad_que_multo",
        "numero_de_resolucion", "fecha_multa", "url_evidencia",
        "id_contrato", "fecha_de_firma", "fecha_firma_date", "valor_contrato",
        "entidad_contratante", "nit_entidad", "tipo_de_contrato", "estado_contrato",
        "confianza",
    ]
    return [_serialize(dict(zip(cols, r))) for r in rows]


def multados_activos_resumen() -> dict[str, Any]:
    if not _view_exists("multas") or not _view_exists("contratos"):
        return {"total_contratistas": 0, "total_contratos": 0, "valor_total_cop": 0}
    sql = f"""
    SELECT
        COUNT(DISTINCT m.documento_contratista) AS total_contratistas,
        COUNT(*)                                AS total_contratos,
        COALESCE(SUM({_VALOR}), 0)             AS valor_total
    FROM multas m
    JOIN contratos c
      ON REGEXP_REPLACE(m.documento_contratista, '[^0-9]', '', 'g')
       = REGEXP_REPLACE(c.documento_proveedor,   '[^0-9]', '', 'g')
    WHERE c.documento_proveedor IS NOT NULL
      AND c.fecha_de_firma IS NOT NULL
      AND LENGTH(c.fecha_de_firma) >= 10
      AND {_FIRMA_DATE} > CAST(m.fecha_de_firmeza AS DATE)
    """
    row = _get_con().execute(sql).fetchone()
    return {
        "total_contratistas": int(row[0] or 0),
        "total_contratos": int(row[1] or 0),
        "valor_total_cop": float(row[2] or 0),
    }


# ── UC-03: Puerta giratoria ───────────────────────────────────────────────────

_SQL_PUERTA = f"""
SELECT
    p.numero_documento                                        AS documento,
    TRIM(
        COALESCE(p.primer_nombre_declarante, '') || ' ' ||
        COALESCE(p.segundo_nombre_declarante, '') || ' ' ||
        COALESCE(p.primer_apellido_declarante, '') || ' ' ||
        COALESCE(p.segundo_apellido_declarante, '')
    )                                                         AS nombre_declarante,
    p.cargo_declarante,
    p.nombre_entidad                                          AS entidad_donde_trabaja,
    p.tipo_declaracion,
    CAST(p.fecha_publicac_declarac AS DATE)                   AS fecha_declaracion,
    p.particip_corp_socied_asoc                               AS participa_en_sociedades,
    c.id_contrato,
    c.fecha_de_firma,
    {_FIRMA_DATE}                                             AS fecha_firma_date,
    {_VALOR}                                                  AS valor_contrato,
    c.nombre_entidad                                          AS entidad_contratante,
    c.nit_entidad,
    c.tipo_de_contrato,
    c.modalidad_de_contratacion,
    CASE
        WHEN LOWER(TRIM(p.nombre_entidad)) = LOWER(TRIM(c.nombre_entidad)) THEN 'alta'
        ELSE 'media'
    END                                                       AS confianza
FROM patrimonio p
JOIN contratos c
  ON REGEXP_REPLACE(p.numero_documento, '[^0-9]', '', 'g')
   = REGEXP_REPLACE(c.documento_proveedor, '[^0-9]', '', 'g')
WHERE p.estado_declaracion = 'FINALIZADO'
  AND p.numero_documento IS NOT NULL
  AND c.documento_proveedor IS NOT NULL
  AND c.fecha_de_firma IS NOT NULL
  AND LENGTH(c.fecha_de_firma) >= 10
  AND {_FIRMA_DATE} > CAST(p.fecha_publicac_declarac AS DATE)
  AND (
    LOWER(TRIM(p.nombre_entidad)) = LOWER(TRIM(c.nombre_entidad))
    OR p.particip_corp_socied_asoc = 'SI'
  )
"""


def puerta_giratoria(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    if not _view_exists("patrimonio") or not _view_exists("contratos"):
        return []
    sql = f"{_SQL_PUERTA} ORDER BY valor_contrato DESC NULLS LAST LIMIT {limit} OFFSET {offset}"
    rows = _get_con().execute(sql).fetchall()
    cols = [
        "documento", "nombre_declarante", "cargo_declarante", "entidad_donde_trabaja",
        "tipo_declaracion", "fecha_declaracion", "participa_en_sociedades",
        "id_contrato", "fecha_de_firma", "fecha_firma_date", "valor_contrato",
        "entidad_contratante", "nit_entidad", "tipo_de_contrato",
        "modalidad_de_contratacion", "confianza",
    ]
    return [_serialize(dict(zip(cols, r))) for r in rows]


def puerta_giratoria_resumen() -> dict[str, Any]:
    if not _view_exists("patrimonio") or not _view_exists("contratos"):
        return {"total_personas": 0, "total_contratos": 0, "valor_total_cop": 0}
    sql = f"""
    SELECT
        COUNT(DISTINCT p.numero_documento) AS total_personas,
        COUNT(*)                           AS total_contratos,
        COALESCE(SUM({_VALOR}), 0)        AS valor_total
    FROM patrimonio p
    JOIN contratos c
      ON REGEXP_REPLACE(p.numero_documento, '[^0-9]', '', 'g')
       = REGEXP_REPLACE(c.documento_proveedor, '[^0-9]', '', 'g')
    WHERE p.estado_declaracion = 'FINALIZADO'
      AND p.numero_documento IS NOT NULL
      AND c.documento_proveedor IS NOT NULL
      AND c.fecha_de_firma IS NOT NULL
      AND LENGTH(c.fecha_de_firma) >= 10
      AND {_FIRMA_DATE} > CAST(p.fecha_publicac_declarac AS DATE)
      AND (
        LOWER(TRIM(p.nombre_entidad)) = LOWER(TRIM(c.nombre_entidad))
        OR p.particip_corp_socied_asoc = 'SI'
      )
    """
    row = _get_con().execute(sql).fetchone()
    return {
        "total_personas": int(row[0] or 0),
        "total_contratos": int(row[1] or 0),
        "valor_total_cop": float(row[2] or 0),
    }


# ── Grafo relacional por entidad ──────────────────────────────────────────────

def grafo_entidad(nit: str, limit: int = 40) -> dict[str, Any]:
    """Grafo vis-network: entidad central + top contratistas coloreados por alerta.

    Returns:
        {
            "nodes": [{id, label, group, value, title}],
            "edges": [{from, to, value, title}],
            "meta":  {entidad, nit, total_contratistas, alertas_rojo, alertas_naranja}
        }
    El campo `group` mapea a colores en vis-network:
        entidad     → azul
        contratista → verde
        sancionado  → rojo   (inhabilitado SIRI)
        multado     → naranja (multa SECOP I)
        alto_riesgo → granate (inhabilitado + multado)
    """
    if not _view_exists("contratos"):
        return {"error": "Dataset contratos no disponible"}

    nit_norm = "".join(c for c in nit if c.isdigit())
    con = _get_con()
    _valor_solo = _VALOR.replace("c.valor_del_contrato", "valor_del_contrato")

    # Nombre de la entidad
    row = con.execute(
        "SELECT nombre_entidad FROM contratos "
        "WHERE REGEXP_REPLACE(nit_entidad,'[^0-9]','','g') = ? LIMIT 1",
        [nit_norm],
    ).fetchone()
    if not row:
        return {"error": f"Entidad NIT {nit} no encontrada en SECOP"}
    nombre_entidad: str = row[0] or nit

    # Top contratistas por valor total para esta entidad
    rows = con.execute(f"""
        SELECT
            REGEXP_REPLACE(documento_proveedor, '[^0-9]', '', 'g') AS doc_norm,
            MAX(proveedor_adjudicado)                               AS nombre,
            COUNT(*)                                                AS n_contratos,
            COALESCE(SUM({_valor_solo}), 0)                        AS valor_total
        FROM contratos
        WHERE REGEXP_REPLACE(nit_entidad, '[^0-9]', '', 'g') = ?
          AND documento_proveedor IS NOT NULL
          AND REGEXP_REPLACE(documento_proveedor, '[^0-9]', '', 'g') != ''
        GROUP BY doc_norm
        ORDER BY valor_total DESC
        LIMIT {limit}
    """, [nit_norm]).fetchall()

    entity_node_id = f"e_{nit_norm}"
    if not rows:
        return {
            "nodes": [{"id": entity_node_id, "label": nombre_entidad[:40],
                       "group": "entidad", "value": 1,
                       "title": f"<b>{nombre_entidad}</b><br>NIT: {nit}<br>Sin proveedores"}],
            "edges": [],
            "meta": {"entidad": nombre_entidad, "nit": nit,
                     "total_contratistas": 0, "alertas_rojo": 0, "alertas_naranja": 0},
        }

    contratistas = [
        {"doc": r[0], "nombre": (r[1] or r[0] or "Sin nombre"),
         "n_contratos": int(r[2]), "valor": float(r[3])}
        for r in rows
    ]
    docs = [c["doc"] for c in contratistas if c["doc"]]
    # docs son solo dígitos → sin riesgo de inyección
    docs_literal = ", ".join(f"'{d}'" for d in docs)

    # Documentos con inhabilitación SIRI
    sanctioned: set[str] = set()
    if _view_exists("siri") and docs_literal:
        siri_rows = con.execute(f"""
            SELECT DISTINCT REGEXP_REPLACE(numero_identificacion, '[^0-9]', '', 'g')
            FROM siri
            WHERE sanciones LIKE '%INHABILIDAD%'
              AND REGEXP_REPLACE(numero_identificacion, '[^0-9]', '', 'g') IN ({docs_literal})
        """).fetchall()
        sanctioned = {r[0] for r in siri_rows}

    # Documentos con multa SECOP I
    fined: set[str] = set()
    if _view_exists("multas") and docs_literal:
        multa_rows = con.execute(f"""
            SELECT DISTINCT REGEXP_REPLACE(documento_contratista, '[^0-9]', '', 'g')
            FROM multas
            WHERE REGEXP_REPLACE(documento_contratista, '[^0-9]', '', 'g') IN ({docs_literal})
        """).fetchall()
        fined = {r[0] for r in multa_rows}

    # Construir nodos y aristas
    total_contratos_entidad = sum(c["n_contratos"] for c in contratistas)
    nodes: list[dict] = [
        {
            "id": entity_node_id,
            "label": nombre_entidad[:40],
            "group": "entidad",
            "value": total_contratos_entidad,
            "title": (
                f"<b>{nombre_entidad}</b><br>"
                f"NIT: {nit}<br>"
                f"{total_contratos_entidad} contratos · top {len(contratistas)} proveedores"
            ),
        }
    ]
    edges: list[dict] = []
    alertas_rojo = 0
    alertas_naranja = 0

    for c in contratistas:
        doc = c["doc"]
        is_san = doc in sanctioned
        is_fin = doc in fined

        if is_san and is_fin:
            group = "alto_riesgo"
            alertas_rojo += 1
            alertas_naranja += 1
        elif is_san:
            group = "sancionado"
            alertas_rojo += 1
        elif is_fin:
            group = "multado"
            alertas_naranja += 1
        else:
            group = "contratista"

        valor_fmt = f"${c['valor']:,.0f}"
        alerts_html = ""
        if is_san:
            alerts_html += "<br><span style='color:#c0392b'>⚠ INHABILITADO SIRI</span>"
        if is_fin:
            alerts_html += "<br><span style='color:#e67e22'>⚠ MULTADO SECOP I</span>"

        nodes.append({
            "id": f"c_{doc}",
            "label": c["nombre"][:35],
            "group": group,
            "value": c["n_contratos"],
            "title": (
                f"<b>{c['nombre']}</b><br>"
                f"Doc: {doc}<br>"
                f"{c['n_contratos']} contratos · {valor_fmt} COP"
                + alerts_html
            ),
        })
        edges.append({
            "from": entity_node_id,
            "to": f"c_{doc}",
            "value": c["n_contratos"],
            "title": f"{c['n_contratos']} contratos · {valor_fmt} COP",
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "entidad": nombre_entidad,
            "nit": nit,
            "total_contratistas": len(contratistas),
            "alertas_rojo": alertas_rojo,
            "alertas_naranja": alertas_naranja,
        },
    }


# ── Dashboard global ───────────────────────────────────────────────────────────

def resumen_global() -> dict[str, Any]:
    return {
        "disponibilidad": available(),
        "sancionados_activos": sancionados_activos_resumen(),
        "multados_activos": multados_activos_resumen(),
        "puerta_giratoria": puerta_giratoria_resumen(),
    }


# ── Perfil unificado por documento ────────────────────────────────────────────

def perfil_documento(documento: str) -> dict[str, Any]:
    """Agrega toda la información disponible de un documento (cédula/NIT)."""
    doc_norm = "".join(c for c in documento if c.isdigit())
    if not doc_norm:
        return {"error": "documento inválido"}

    perfil: dict[str, Any] = {"documento": doc_norm}
    con = _get_con()

    # _VALOR y _FIRMA_DATE usan alias 'c.' que solo aplica en JOINs.
    # Acá la tabla va sin alias, así que reemplazamos el prefijo.
    _valor_solo = _VALOR.replace("c.valor_del_contrato", "valor_del_contrato")
    if _view_exists("contratos"):
        rows = con.execute(f"""
            SELECT id_contrato, nombre_entidad, nit_entidad,
                   fecha_de_firma, {_valor_solo} AS valor, tipo_de_contrato,
                   estado_contrato, proveedor_adjudicado
            FROM contratos
            WHERE REGEXP_REPLACE(documento_proveedor, '[^0-9]', '', 'g') = ?
            ORDER BY fecha_de_firma DESC
            LIMIT 20
        """, [doc_norm]).fetchall()
        secop_cols = ["id_contrato", "nombre_entidad", "nit_entidad",
                      "fecha_de_firma", "valor", "tipo_de_contrato",
                      "estado_contrato", "proveedor_adjudicado"]
        contratos_list = [_serialize(dict(zip(secop_cols, r))) for r in rows]
        valor_total = sum(r["valor"] or 0 for r in contratos_list)
        perfil["secop"] = {
            "total_contratos": len(contratos_list),
            "valor_total_cop": valor_total,
            "contratos": contratos_list,
        }

    if _view_exists("siri"):
        rows = con.execute("""
            SELECT sanciones, fecha_efectos_juridicos, fecha_fin_sancion,
                   duracion_anos, entidad_sancionado, autoridad
            FROM siri
            WHERE REGEXP_REPLACE(numero_identificacion, '[^0-9]', '', 'g') = ?
        """, [doc_norm]).fetchall()
        siri_cols = ["sanciones", "fecha_inicio", "fecha_fin", "duracion_anos",
                     "entidad_sancionado", "autoridad"]
        perfil["siri"] = [_serialize(dict(zip(siri_cols, r))) for r in rows]

    if _view_exists("multas"):
        rows = con.execute("""
            SELECT nombre_contratista, valor_sancion, nombre_entidad,
                   fecha_de_firmeza, ruta_de_proceso
            FROM multas
            WHERE REGEXP_REPLACE(documento_contratista, '[^0-9]', '', 'g') = ?
        """, [doc_norm]).fetchall()
        multas_cols = ["nombre_contratista", "valor_sancion", "entidad",
                       "fecha_multa", "url_evidencia"]
        perfil["multas"] = [_serialize(dict(zip(multas_cols, r))) for r in rows]

    if _view_exists("patrimonio"):
        rows = con.execute("""
            SELECT primer_nombre_declarante, primer_apellido_declarante,
                   cargo_declarante, nombre_entidad, tipo_declaracion,
                   fecha_publicac_declarac, particip_corp_socied_asoc
            FROM patrimonio
            WHERE REGEXP_REPLACE(numero_documento, '[^0-9]', '', 'g') = ?
            ORDER BY fecha_publicac_declarac DESC
            LIMIT 5
        """, [doc_norm]).fetchall()
        pat_cols = ["primer_nombre", "primer_apellido", "cargo", "entidad",
                    "tipo_declaracion", "fecha_declaracion", "participa_en_sociedades"]
        perfil["patrimonio"] = [_serialize(dict(zip(pat_cols, r))) for r in rows]

    # Nivel de alerta agregado
    tiene_sancion = bool(perfil.get("siri"))
    tiene_multa = bool(perfil.get("multas"))
    if tiene_sancion:
        perfil["nivel_alerta"] = "rojo"
    elif tiene_multa:
        perfil["nivel_alerta"] = "naranja"
    elif perfil.get("patrimonio"):
        perfil["nivel_alerta"] = "amarillo"
    else:
        perfil["nivel_alerta"] = "verde"

    return perfil
