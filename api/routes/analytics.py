import re
from fastapi import APIRouter, Depends
from db import get_db
from security import get_current_user
from datasets import ContratosDataset

router = APIRouter(prefix="/paso2/analytics", tags=["paso2-analytics"])

COLLECTION = "contratos-electronicos"


def parse_money(value: str) -> float:
    """'$40,825,000' → 40825000.0"""
    if not value:
        return 0.0
    return float(re.sub(r"[^\d.]", "", str(value)) or 0)


def get_col():
    return get_db()[COLLECTION]


# ──────────────────────────────────────────────────────────────
# Q3 — Número de registros
# ──────────────────────────────────────────────────────────────
@router.get("/total-registros")
def total_registros(current_user: dict = Depends(get_current_user)):
    total = get_col().count_documents({})
    return {"pregunta": 3, "total_registros": total}


# ──────────────────────────────────────────────────────────────
# Q4 — Número de variables
# ──────────────────────────────────────────────────────────────
@router.get("/total-variables")
def total_variables(current_user: dict = Depends(get_current_user)):
    doc = get_col().find_one()
    if doc is None:
        return {"pregunta": 4, "total_variables": 0, "variables": [], "mensaje": "Colección vacía"}
    campos = [k for k in doc.keys() if k != "_id"]
    return {"pregunta": 4, "total_variables": len(campos), "variables": campos}


# ──────────────────────────────────────────────────────────────
# Q5 — Registros del 2025
# ──────────────────────────────────────────────────────────────
@router.get("/registros-2025")
def registros_2025(current_user: dict = Depends(get_current_user)):
    total = get_col().count_documents({"fecha_de_firma": {"$regex": "/2025$"}})
    return {"pregunta": 5, "registros_2025": total}


# ──────────────────────────────────────────────────────────────
# Q6 y Q7 — Proporción de contratos Pymes
# ──────────────────────────────────────────────────────────────
@router.get("/pymes")
def pymes(current_user: dict = Depends(get_current_user)):
    col = get_col()
    total = col.count_documents({})
    pyme_count = col.count_documents({"es_pyme": "Si"})
    porcentaje = round(pyme_count / total * 100, 2) if total else 0
    return {
        "pregunta": "6 y 7",
        "total_contratos": total,
        "contratos_pyme": pyme_count,
        "porcentaje_pyme": porcentaje,
    }


# ──────────────────────────────────────────────────────────────
# Q8 y Q9 — Top 10 departamentos por número de contratos
# ──────────────────────────────────────────────────────────────
@router.get("/top-departamentos")
def top_departamentos(current_user: dict = Depends(get_current_user)):
    pipeline = [
        {"$group": {"_id": "$departamento", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 10},
        {"$project": {"_id": 0, "departamento": "$_id", "total": 1}},
    ]
    resultado = list(get_col().aggregate(pipeline))
    posicion_6 = resultado[5] if len(resultado) >= 6 else None
    return {
        "pregunta": "8 y 9",
        "top_10": resultado,
        "posicion_6": posicion_6,
    }


# ──────────────────────────────────────────────────────────────
# Q10 y Q11 — Modalidad de contratación preferida
# ──────────────────────────────────────────────────────────────
@router.get("/modalidad-preferida")
def modalidad_preferida(current_user: dict = Depends(get_current_user)):
    pipeline = [
        {"$group": {"_id": "$modalidad_de_contratacion", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 5},
        {"$project": {"_id": 0, "modalidad": "$_id", "total": 1}},
    ]
    resultado = list(get_col().aggregate(pipeline))
    return {
        "pregunta": "10 y 11",
        "modalidad_preferida": resultado[0] if resultado else None,
        "top_5_modalidades": resultado,
    }


# ──────────────────────────────────────────────────────────────
# Q12 — Top 3 entidades que más dinero ejecutaron
# ──────────────────────────────────────────────────────────────
@router.get("/top-entidades-dinero")
def top_entidades_dinero(current_user: dict = Depends(get_current_user)):
    docs = get_col().find(
        {"valor_del_contrato": {"$exists": True, "$ne": None}},
        {"nombre_entidad": 1, "valor_del_contrato": 1}
    )
    totales: dict = {}
    for doc in docs:
        entidad = doc.get("nombre_entidad") or "Sin nombre"
        valor = parse_money(doc.get("valor_del_contrato"))
        totales[entidad] = totales.get(entidad, 0) + valor

    top3 = sorted(totales.items(), key=lambda x: x[1], reverse=True)[:3]
    return {
        "pregunta": 12,
        "top_3": [
            {"posicion": i + 1, "entidad": e, "valor_total": round(v, 2)}
            for i, (e, v) in enumerate(top3)
        ],
    }


# ──────────────────────────────────────────────────────────────
# Q13 y Q14 — Top 5 tipos de contrato
# ──────────────────────────────────────────────────────────────
@router.get("/tipos-contrato")
def tipos_contrato(current_user: dict = Depends(get_current_user)):
    col = get_col()
    pipeline = [
        {"$group": {"_id": "$tipo_de_contrato", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 5},
        {"$project": {"_id": 0, "tipo": "$_id", "total": 1}},
    ]
    top5 = list(col.aggregate(pipeline))
    total_registros = col.count_documents({})
    pct_mayor = round(top5[0]["total"] / total_registros * 100, 2) if top5 else 0

    return {
        "pregunta": "13 y 14",
        "top_5": top5,
        "tipo_mayor": top5[0]["tipo"] if top5 else None,
        "porcentaje_tipo_mayor": pct_mayor,
    }


# ──────────────────────────────────────────────────────────────
# Q15 — Top 3 valores anómalos financieros
# ──────────────────────────────────────────────────────────────
@router.get("/anomalias-financieras")
def anomalias_financieras(current_user: dict = Depends(get_current_user)):
    docs = list(get_col().find(
        {"valor_del_contrato": {"$exists": True, "$ne": None}},
        {"id_contrato": 1, "nombre_entidad": 1, "valor_del_contrato": 1,
         "tipo_de_contrato": 1, "estado_contrato": 1}
    ))

    valores = [(parse_money(d.get("valor_del_contrato")), d) for d in docs]
    valores = [(v, d) for v, d in valores if v > 0]

    nums = [v for v, _ in valores]
    n = len(nums)
    if n == 0:
        return {"pregunta": 15, "mensaje": "Sin datos numéricos de valor_del_contrato aún", "top_3_anomalos": []}
    media = sum(nums) / n
    std = (sum((x - media) ** 2 for x in nums) / n) ** 0.5
    sorted_nums = sorted(nums)
    q1 = sorted_nums[n // 4]
    q3 = sorted_nums[3 * n // 4]
    iqr = q3 - q1
    umbral = q3 + 3 * iqr

    anomalos = sorted(
        [(v, d) for v, d in valores if v > umbral],
        key=lambda x: x[0],
        reverse=True
    )[:3]

    return {
        "pregunta": 15,
        "estadisticas": {
            "media": round(media, 2),
            "desviacion_std": round(std, 2),
            "q1": round(q1, 2),
            "q3": round(q3, 2),
            "umbral_anomalia": round(umbral, 2),
        },
        "top_3_anomalos": [
            {
                "posicion": i + 1,
                "id_contrato": d.get("id_contrato"),
                "entidad": d.get("nombre_entidad"),
                "tipo": d.get("tipo_de_contrato"),
                "estado": d.get("estado_contrato"),
                "valor": round(v, 2),
                "es_anomalo": True,
                "sustento": f"Valor {round(v/umbral, 1)}x por encima del umbral IQR (Q3 + 3×IQR = ${umbral:,.0f})",
            }
            for i, (v, d) in enumerate(anomalos)
        ],
    }


# ──────────────────────────────────────────────────────────────
# Q16 — Porcentaje de contratos con pagos adelantados
# ──────────────────────────────────────────────────────────────
@router.get("/pagos-adelantados")
def pagos_adelantados(current_user: dict = Depends(get_current_user)):
    col = get_col()
    total = col.count_documents({})
    con_anticipo = col.count_documents({"habilita_pago_adelantado": "Si"})
    pct = round(con_anticipo / total * 100, 2) if total else 0
    return {
        "pregunta": 16,
        "total_contratos": total,
        "con_pago_adelantado": con_anticipo,
        "porcentaje": pct,
    }


# ──────────────────────────────────────────────────────────────
# Q17 — Contratos con obligaciones ambientales
# ──────────────────────────────────────────────────────────────
@router.get("/obligaciones-ambientales")
def obligaciones_ambientales(current_user: dict = Depends(get_current_user)):
    col = get_col()
    total = col.count_documents({})
    con_ambiental = col.count_documents({"obligacin_ambiental": "Si"})
    pct = round(con_ambiental / total * 100, 2) if total else 0
    return {
        "pregunta": 17,
        "total_contratos": total,
        "con_obligacion_ambiental": con_ambiental,
        "porcentaje": pct,
    }


# ──────────────────────────────────────────────────────────────
# Q18 — Principio de Pareto (80/20)
# ──────────────────────────────────────────────────────────────
@router.get("/pareto")
def pareto(current_user: dict = Depends(get_current_user)):
    docs = get_col().find(
        {"valor_del_contrato": {"$exists": True, "$ne": None},
         "nombre_entidad": {"$exists": True, "$ne": None}},
        {"nombre_entidad": 1, "valor_del_contrato": 1}
    )

    totales: dict = {}
    for doc in docs:
        entidad = doc.get("nombre_entidad") or "Sin nombre"
        valor = parse_money(doc.get("valor_del_contrato"))
        totales[entidad] = totales.get(entidad, 0) + valor

    entidades_ordenadas = sorted(totales.values(), reverse=True)
    n_entidades = len(entidades_ordenadas)
    valor_total = sum(entidades_ordenadas)
    top_20_pct_n = max(1, int(n_entidades * 0.20))
    valor_top_20 = sum(entidades_ordenadas[:top_20_pct_n])
    pct_valor_top_20 = round(valor_top_20 / valor_total * 100, 2) if valor_total else 0

    se_cumple = pct_valor_top_20 >= 75

    return {
        "pregunta": 18,
        "total_entidades": n_entidades,
        "top_20_pct_entidades": top_20_pct_n,
        "pct_valor_concentrado_en_top_20": pct_valor_top_20,
        "se_cumple_pareto": se_cumple,
        "sustento": (
            f"El {top_20_pct_n} ({20}%) de entidades con mayor contratación concentra el "
            f"{pct_valor_top_20}% del valor total contratado. "
            f"{'Se cumple' if se_cumple else 'No se cumple estrictamente'} el principio 80/20."
        ),
    }


# ──────────────────────────────────────────────────────────────
# Q19 — Brecha de género financiera
# ──────────────────────────────────────────────────────────────
@router.get("/brecha-genero")
def brecha_genero(current_user: dict = Depends(get_current_user)):
    docs = get_col().find(
        {"gnero_representante_legal": {"$exists": True, "$ne": None},
         "valor_del_contrato": {"$exists": True, "$ne": None}},
        {"gnero_representante_legal": 1, "valor_del_contrato": 1}
    )

    totales: dict = {}
    conteos: dict = {}
    for doc in docs:
        genero = doc.get("gnero_representante_legal") or "No definido"
        valor = parse_money(doc.get("valor_del_contrato"))
        totales[genero] = totales.get(genero, 0) + valor
        conteos[genero] = conteos.get(genero, 0) + 1

    valor_total = sum(totales.values())
    resumen = sorted(
        [
            {
                "genero": g,
                "num_contratos": conteos[g],
                "valor_total": round(totales[g], 2),
                "pct_valor": round(totales[g] / valor_total * 100, 2) if valor_total else 0,
            }
            for g in totales
        ],
        key=lambda x: x["valor_total"],
        reverse=True,
    )

    hombre = next((r for r in resumen if "hombre" in r["genero"].lower()), None)
    mujer  = next((r for r in resumen if "mujer"  in r["genero"].lower()), None)
    brecha = None
    if hombre and mujer and mujer["valor_total"] > 0:
        brecha = round((hombre["valor_total"] - mujer["valor_total"]) / mujer["valor_total"] * 100, 2)

    return {
        "pregunta": 19,
        "por_genero": resumen,
        "brecha_porcentual_hombre_vs_mujer": brecha,
        "sustento": (
            f"Los representantes legales de género masculino gestionan el "
            f"{hombre['pct_valor'] if hombre else '?'}% del valor contratado, "
            f"versus {mujer['pct_valor'] if mujer else '?'}% del femenino. "
            f"Brecha relativa: {brecha}%." if brecha is not None
            else "No hay datos suficientes para calcular la brecha."
        ),
    }


# ──────────────────────────────────────────────────────────────
# Q20 — Anomalías en tipos de datos
# ──────────────────────────────────────────────────────────────
@router.get("/anomalias-tipos-datos")
def anomalias_tipos_datos(current_user: dict = Depends(get_current_user)):
    return {
        "pregunta": 20,
        "anomalias": [
            {
                "campo": "valor_del_contrato",
                "tipo_almacenado": "string",
                "tipo_correcto": "float / decimal",
                "problema": "Contiene símbolo '$' y comas como separador de miles. Ej: '$40,825,000'",
            },
            {
                "campo": "fecha_de_firma",
                "tipo_almacenado": "string",
                "tipo_correcto": "date (ISODate)",
                "problema": "Formato MM/DD/YYYY en lugar de ISO 8601. Impide ordenar y filtrar por rango de fechas eficientemente.",
            },
            {
                "campo": "es_pyme / habilita_pago_adelantado / reversion",
                "tipo_almacenado": "string ('Si' / 'No')",
                "tipo_correcto": "boolean",
                "problema": "Campos binarios almacenados como texto. Dificultan filtros y aumentan tamaño.",
            },
            {
                "campo": "codigo_entidad / codigo_proveedor / nit_entidad",
                "tipo_almacenado": "string con comas como separador de miles. Ej: '703,932,673'",
                "tipo_correcto": "string sin formato o integer",
                "problema": "Códigos numéricos formateados como moneda, impiden joins y búsquedas exactas.",
            },
            {
                "campo": "dias_adicionados / saldo_cdp / saldo_vigencia",
                "tipo_almacenado": "string",
                "tipo_correcto": "integer / float",
                "problema": "Valores numéricos almacenados como texto. Impiden operaciones aritméticas directas en Mongo.",
            },
        ],
    }


# ──────────────────────────────────────────────────────────────
# Q21 — Documentación de endpoints y API de datos abiertos
# ──────────────────────────────────────────────────────────────
@router.get("/api-doc")
def api_doc(current_user: dict = Depends(get_current_user)):
    col = get_col()
    total_mongo = col.count_documents({})
    doc = col.find_one()
    campos = [k for k in doc.keys() if k != "_id"] if doc else []

    base_url = "https://www.datos.gov.co/resource"
    contratos_id = ContratosDataset.ID
    archivos_id  = "dmgg-8hin"

    return {
        "pregunta": 21,
        "swagger": "/docs",
        "redoc": "/redoc",
        "fuente_local_mongo": {
            "coleccion": "contratos-electronicos",
            "total_registros": total_mongo,
            "num_variables": len(campos),
            "variables": campos,
            "endpoints_disponibles": {
                "listar_paginado": "GET /contratos-local?page=1&page_size=20",
                "filtrar_estado": "GET /contratos-local?estado=En ejecución",
                "filtrar_departamento": "GET /contratos-local?departamento=ANTIOQUIA",
                "analytics": "GET /paso2/analytics/<endpoint>",
            },
        },
        "fuente_datos_abiertos": {
            "contratos_electronicos": {
                "dataset_id": contratos_id,
                "url_base": f"{base_url}/{contratos_id}.json",
                "ejemplos_soql": {
                    "contar": f"{base_url}/{contratos_id}.json?$select=COUNT(*)",
                    "filtrar_estado": f"{base_url}/{contratos_id}.json?$where=estado_contrato='En ejecuci%C3%B3n'&$limit=10",
                    "top_entidades": f"{base_url}/{contratos_id}.json?$select=nombre_entidad,COUNT(*)&$group=nombre_entidad&$order=COUNT(*) DESC&$limit=10",
                },
            },
            "archivos_descarga": {
                "dataset_id": archivos_id,
                "url_base": f"{base_url}/{archivos_id}.json",
                "ejemplos_soql": {
                    "contar": f"{base_url}/{archivos_id}.json?$select=COUNT(*)",
                    "filtrar_pdf": f"{base_url}/{archivos_id}.json?$where=extensi_n='pdf'&$limit=10",
                },
            },
        },
    }
