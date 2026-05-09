import os
import threading
import duckdb

PARQUET_PATH = os.getenv("PARQUET_PATH", "data/contratos.parquet")

_VALOR = "TRY_CAST(REGEXP_REPLACE(REGEXP_REPLACE(valor_del_contrato, '\\$', ''), ',', '', 'g') AS DOUBLE)"

_lock = threading.Lock()
_con: duckdb.DuckDBPyConnection | None = None


def _get_con() -> duckdb.DuckDBPyConnection:
    global _con
    if _con is None:
        with _lock:
            if _con is None:
                c = duckdb.connect()
                c.execute(f"CREATE VIEW contratos AS SELECT * FROM read_parquet('{PARQUET_PATH}')")
                _con = c
    return _con


def available() -> bool:
    return os.path.exists(PARQUET_PATH)


def total_registros() -> int:
    return _get_con().execute("SELECT COUNT(*) FROM contratos").fetchone()[0]


def registros_2025() -> int:
    return _get_con().execute(
        "SELECT COUNT(*) FROM contratos WHERE fecha_de_firma LIKE '%/2025'"
    ).fetchone()[0]


def pymes() -> dict:
    row = _get_con().execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN es_pyme = 'Si' THEN 1 ELSE 0 END)
        FROM contratos
    """).fetchone()
    return {"total": row[0], "pymes": row[1]}


def top_departamentos() -> list:
    rows = _get_con().execute("""
        SELECT departamento, COUNT(*) AS total
        FROM contratos
        GROUP BY departamento
        ORDER BY total DESC
        LIMIT 10
    """).fetchall()
    return [{"departamento": r[0], "total": r[1]} for r in rows]


def modalidad_preferida() -> list:
    rows = _get_con().execute("""
        SELECT modalidad_de_contratacion, COUNT(*) AS total
        FROM contratos
        GROUP BY modalidad_de_contratacion
        ORDER BY total DESC
        LIMIT 5
    """).fetchall()
    return [{"modalidad": r[0], "total": r[1]} for r in rows]


def top_entidades_dinero() -> list:
    rows = _get_con().execute(f"""
        SELECT nombre_entidad, SUM({_VALOR}) AS valor_total
        FROM contratos
        WHERE valor_del_contrato IS NOT NULL
        GROUP BY nombre_entidad
        ORDER BY valor_total DESC NULLS LAST
        LIMIT 3
    """).fetchall()
    return [{"posicion": i + 1, "entidad": r[0], "valor_total": round(r[1] or 0, 2)}
            for i, r in enumerate(rows)]


def tipos_contrato() -> dict:
    rows = _get_con().execute("""
        SELECT tipo_de_contrato, COUNT(*) AS total
        FROM contratos
        GROUP BY tipo_de_contrato
        ORDER BY total DESC
        LIMIT 5
    """).fetchall()
    total = _get_con().execute("SELECT COUNT(*) FROM contratos").fetchone()[0]
    top5 = [{"tipo": r[0], "total": r[1]} for r in rows]
    pct = round(top5[0]["total"] / total * 100, 2) if top5 and total else 0
    return {"top_5": top5, "total": total, "pct_mayor": pct}


def anomalias_financieras() -> dict:
    stats = _get_con().execute(f"""
        WITH vals AS (SELECT {_VALOR} AS v FROM contratos WHERE valor_del_contrato IS NOT NULL),
        filtered AS (SELECT v FROM vals WHERE v > 0)
        SELECT AVG(v), STDDEV(v),
               QUANTILE_CONT(v, 0.25),
               QUANTILE_CONT(v, 0.75)
        FROM filtered
    """).fetchone()

    if not stats or stats[0] is None:
        return {"estadisticas": None, "top_3_anomalos": []}

    media, std, q1, q3 = stats
    umbral = q3 + 3 * (q3 - q1)

    rows = _get_con().execute(f"""
        SELECT id_contrato, nombre_entidad, tipo_de_contrato, estado_contrato,
               {_VALOR} AS valor
        FROM contratos
        WHERE valor_del_contrato IS NOT NULL AND {_VALOR} > {umbral}
        ORDER BY {_VALOR} DESC
        LIMIT 3
    """).fetchall()

    return {
        "estadisticas": {
            "media": round(media, 2), "desviacion_std": round(std, 2),
            "q1": round(q1, 2), "q3": round(q3, 2),
            "umbral_anomalia": round(umbral, 2),
        },
        "top_3_anomalos": [
            {
                "posicion": i + 1, "id_contrato": r[0], "entidad": r[1],
                "tipo": r[2], "estado": r[3], "valor": round(r[4], 2),
                "es_anomalo": True,
                "sustento": f"Valor {round(r[4] / umbral, 1)}x por encima del umbral IQR (Q3 + 3×IQR = ${umbral:,.0f})",
            }
            for i, r in enumerate(rows)
        ],
    }


def pagos_adelantados() -> dict:
    row = _get_con().execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN habilita_pago_adelantado = 'Si' THEN 1 ELSE 0 END)
        FROM contratos
    """).fetchone()
    return {"total": row[0], "con_anticipo": row[1]}


def obligaciones_ambientales() -> dict:
    row = _get_con().execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN obligacin_ambiental = 'Si' THEN 1 ELSE 0 END)
        FROM contratos
    """).fetchone()
    return {"total": row[0], "con_ambiental": row[1]}


def pareto() -> dict:
    row = _get_con().execute(f"""
        WITH ent AS (
            SELECT nombre_entidad, SUM({_VALOR}) AS valor
            FROM contratos
            WHERE valor_del_contrato IS NOT NULL AND nombre_entidad IS NOT NULL
            GROUP BY nombre_entidad
        )
        SELECT COUNT(*), SUM(valor) FROM ent
    """).fetchone()
    n_entidades, valor_total = row
    top_20_n = max(1, int(n_entidades * 0.20))

    valor_top_20 = _get_con().execute(f"""
        SELECT SUM(valor) FROM (
            SELECT SUM({_VALOR}) AS valor
            FROM contratos
            WHERE valor_del_contrato IS NOT NULL AND nombre_entidad IS NOT NULL
            GROUP BY nombre_entidad
            ORDER BY valor DESC
            LIMIT {top_20_n}
        )
    """).fetchone()[0] or 0

    pct = round(valor_top_20 / valor_total * 100, 2) if valor_total else 0
    return {"n_entidades": n_entidades, "top_20_pct_n": top_20_n,
            "pct_valor_top_20": pct, "se_cumple": pct >= 75}


def brecha_genero() -> list:
    rows = _get_con().execute(f"""
        SELECT gnero_representante_legal,
               COUNT(*) AS num_contratos,
               SUM({_VALOR}) AS valor_total
        FROM contratos
        WHERE gnero_representante_legal IS NOT NULL AND valor_del_contrato IS NOT NULL
        GROUP BY gnero_representante_legal
        ORDER BY valor_total DESC
    """).fetchall()
    total_valor = sum(r[2] or 0 for r in rows)
    return [
        {
            "genero": r[0], "num_contratos": r[1],
            "valor_total": round(r[2] or 0, 2),
            "pct_valor": round((r[2] or 0) / total_valor * 100, 2) if total_valor else 0,
        }
        for r in rows
    ]
