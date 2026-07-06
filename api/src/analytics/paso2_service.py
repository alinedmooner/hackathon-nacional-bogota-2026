from src.core.repositories import duckdb_repo as duck
from src.core.repositories import analytics_mongo_repo as mongo
from src.core import cache_service as cache
from src.core.datasets import ContratosDataset


def total_registros() -> dict:
    def compute():
        total = duck.total_registros() if duck.available() else mongo.total_registros()
        return {"pregunta": 3, "total_registros": total}
    return cache.cached("total_registros", compute)


def total_variables() -> dict:
    def compute():
        campos = duck.variables() if duck.available() else mongo.variables()
        return {"pregunta": 4, "total_variables": len(campos), "variables": campos}
    return cache.cached("total_variables", compute)


def registros_2025() -> dict:
    def compute():
        total = duck.registros_2025() if duck.available() else mongo.registros_2025()
        return {"pregunta": 5, "registros_2025": total}
    return cache.cached("registros_2025", compute)


def pymes() -> dict:
    def compute():
        d = duck.pymes() if duck.available() else mongo.pymes()
        total, pyme_count = d["total"], d["pymes"]
        pct = round(pyme_count / total * 100, 2) if total else 0
        return {"pregunta": "6 y 7", "total_contratos": total,
                "contratos_pyme": pyme_count, "porcentaje_pyme": pct}
    return cache.cached("pymes", compute)


def top_departamentos() -> dict:
    def compute():
        resultado = duck.top_departamentos() if duck.available() else mongo.top_departamentos()
        posicion_6 = resultado[5] if len(resultado) >= 6 else None
        return {"pregunta": "8 y 9", "top_10": resultado, "posicion_6": posicion_6}
    return cache.cached("top_departamentos", compute)


def modalidad_preferida() -> dict:
    def compute():
        resultado = duck.modalidad_preferida() if duck.available() else mongo.modalidad_preferida()
        return {"pregunta": "10 y 11",
                "modalidad_preferida": resultado[0] if resultado else None,
                "top_5_modalidades": resultado}
    return cache.cached("modalidad_preferida", compute)


def top_entidades_dinero() -> dict:
    def compute():
        top3 = duck.top_entidades_dinero() if duck.available() else mongo.top_entidades_dinero()
        return {"pregunta": 12, "top_3": top3}
    return cache.cached("top_entidades_dinero", compute)


def tipos_contrato() -> dict:
    def compute():
        if duck.available():
            d = duck.tipos_contrato()
            top5, pct = d["top_5"], d["pct_mayor"]
        else:
            d = mongo.tipos_contrato()
            top5, pct = d["top_5"], d["pct_mayor"]
        return {"pregunta": "13 y 14", "top_5": top5,
                "tipo_mayor": top5[0]["tipo"] if top5 else None,
                "porcentaje_tipo_mayor": pct}
    return cache.cached("tipos_contrato", compute)


def anomalias_financieras() -> dict:
    def compute():
        d = duck.anomalias_financieras() if duck.available() else mongo.anomalias_financieras()
        return {"pregunta": 15, **d}
    return cache.cached("anomalias_financieras", compute)


def pagos_adelantados() -> dict:
    def compute():
        d = duck.pagos_adelantados() if duck.available() else mongo.pagos_adelantados()
        total, con_anticipo = d["total"], d["con_anticipo"]
        pct = round(con_anticipo / total * 100, 2) if total else 0
        return {"pregunta": 16, "total_contratos": total,
                "con_pago_adelantado": con_anticipo, "porcentaje": pct}
    return cache.cached("pagos_adelantados", compute)


def obligaciones_ambientales() -> dict:
    def compute():
        d = duck.obligaciones_ambientales() if duck.available() else mongo.obligaciones_ambientales()
        total, con_ambiental = d["total"], d["con_ambiental"]
        pct = round(con_ambiental / total * 100, 2) if total else 0
        return {"pregunta": 17, "total_contratos": total,
                "con_obligacion_ambiental": con_ambiental, "porcentaje": pct}
    return cache.cached("obligaciones_ambientales", compute)


def pareto() -> dict:
    def compute():
        d = duck.pareto() if duck.available() else mongo.pareto()
        n, top_20_n, pct, se_cumple = (
            d["n_entidades"], d["top_20_pct_n"], d["pct_valor_top_20"], d["se_cumple"]
        )
        return {
            "pregunta": 18, "total_entidades": n, "top_20_pct_entidades": top_20_n,
            "pct_valor_concentrado_en_top_20": pct, "se_cumple_pareto": se_cumple,
            "sustento": (
                f"El {top_20_n} ({20}%) de entidades concentra el {pct}% del valor total. "
                f"{'Se cumple' if se_cumple else 'No se cumple estrictamente'} el principio 80/20."
            ),
        }
    return cache.cached("pareto", compute)


def brecha_genero() -> dict:
    def compute():
        resumen = duck.brecha_genero() if duck.available() else mongo.brecha_genero()
        hombre = next((r for r in resumen if "hombre" in r["genero"].lower()), None)
        mujer = next((r for r in resumen if "mujer" in r["genero"].lower()), None)
        brecha = None
        if hombre and mujer and mujer["valor_total"] > 0:
            brecha = round((hombre["valor_total"] - mujer["valor_total"]) / mujer["valor_total"] * 100, 2)
        return {
            "pregunta": 19, "por_genero": resumen,
            "brecha_porcentual_hombre_vs_mujer": brecha,
            "sustento": (
                f"Género masculino: {hombre['pct_valor'] if hombre else '?'}% del valor. "
                f"Femenino: {mujer['pct_valor'] if mujer else '?'}%. Brecha: {brecha}%."
                if brecha is not None else "No hay datos suficientes."
            ),
        }
    return cache.cached("brecha_genero", compute)


def anomalias_tipos_datos() -> dict:
    return {
        "pregunta": 20,
        "anomalias": [
            {"campo": "valor_del_contrato", "tipo_almacenado": "string",
             "tipo_correcto": "float / decimal",
             "problema": "Contiene símbolo '$' y comas. Ej: '$40,825,000'"},
            {"campo": "fecha_de_firma", "tipo_almacenado": "string",
             "tipo_correcto": "date (ISODate)",
             "problema": "Formato MM/DD/YYYY en lugar de ISO 8601."},
            {"campo": "es_pyme / habilita_pago_adelantado / reversion",
             "tipo_almacenado": "string ('Si' / 'No')", "tipo_correcto": "boolean",
             "problema": "Campos binarios almacenados como texto."},
            {"campo": "codigo_entidad / codigo_proveedor / nit_entidad",
             "tipo_almacenado": "string con comas. Ej: '703,932,673'",
             "tipo_correcto": "string sin formato o integer",
             "problema": "Códigos numéricos formateados como moneda."},
            {"campo": "dias_adicionados / saldo_cdp / saldo_vigencia",
             "tipo_almacenado": "string", "tipo_correcto": "integer / float",
             "problema": "Valores numéricos almacenados como texto."},
        ],
    }


def api_doc() -> dict:
    from src.database import get_db
    col = get_db()["contratos-electronicos"]
    total_mongo = col.estimated_document_count()
    campos = mongo.variables()
    base_url = "https://www.datos.gov.co/resource"
    contratos_id = ContratosDataset.ID
    archivos_id = "dmgg-8hin"
    return {
        "pregunta": 21,
        "swagger": "/docs", "redoc": "/redoc",
        "motor_analytics": "DuckDB + Parquet" if duck.available() else "MongoDB aggregation",
        "cache_activo": True,
        "fuente_local_mongo": {
            "coleccion": "contratos-electronicos",
            "total_registros": total_mongo,
            "num_variables": len(campos), "variables": campos,
        },
        "fuente_datos_abiertos": {
            "contratos_electronicos": {"dataset_id": contratos_id,
                                       "url_base": f"{base_url}/{contratos_id}.json"},
            "archivos_descarga": {"dataset_id": archivos_id,
                                  "url_base": f"{base_url}/{archivos_id}.json"},
        },
    }
