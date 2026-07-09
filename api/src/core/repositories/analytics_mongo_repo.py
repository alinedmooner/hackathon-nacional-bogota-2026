import re
from src.database import get_db

COLLECTION = "contratos-electronicos"

_TO_DOUBLE = {
    "$toDouble": {
        "$replaceAll": {
            "input": {
                "$replaceAll": {
                    "input": {"$ifNull": ["$valor_del_contrato", "0"]},
                    "find": "$", "replacement": "",
                }
            },
            "find": ",", "replacement": "",
        }
    }
}


def _col():
    return get_db()[COLLECTION]


def parse_money(value: str) -> float:
    if not value:
        return 0.0
    return float(re.sub(r"[^\d.]", "", str(value)) or 0)


def total_registros() -> int:
    return _col().estimated_document_count()


def registros_2025() -> int:
    return _col().count_documents({"fecha_de_firma": {"$regex": "/2025$"}})


def pymes() -> dict:
    col = _col()
    total = col.estimated_document_count()
    pyme_count = col.count_documents({"es_pyme": "Si"})
    return {"total": total, "pymes": pyme_count}


def top_departamentos() -> list:
    pipeline = [
        {"$group": {"_id": "$departamento", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}, {"$limit": 10},
        {"$project": {"_id": 0, "departamento": "$_id", "total": 1}},
    ]
    return list(_col().aggregate(pipeline))


def modalidad_preferida() -> list:
    pipeline = [
        {"$group": {"_id": "$modalidad_de_contratacion", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}, {"$limit": 5},
        {"$project": {"_id": 0, "modalidad": "$_id", "total": 1}},
    ]
    return list(_col().aggregate(pipeline))


def top_entidades_dinero() -> list:
    pipeline = [
        {"$match": {"valor_del_contrato": {"$exists": True, "$ne": None}}},
        {"$addFields": {"_valor": _TO_DOUBLE}},
        {"$match": {"_valor": {"$gt": 0}}},
        {"$group": {"_id": "$nombre_entidad", "valor_total": {"$sum": "$_valor"}}},
        {"$sort": {"valor_total": -1}}, {"$limit": 3},
        {"$project": {"_id": 0, "entidad": "$_id", "valor_total": 1}},
    ]
    return [{"posicion": i + 1, **r} for i, r in enumerate(
        _col().aggregate(pipeline, allowDiskUse=True)
    )]


def tipos_contrato() -> dict:
    col = _col()
    pipeline = [
        {"$group": {"_id": "$tipo_de_contrato", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}, {"$limit": 5},
        {"$project": {"_id": 0, "tipo": "$_id", "total": 1}},
    ]
    top5 = list(col.aggregate(pipeline))
    total = col.estimated_document_count()
    pct = round(top5[0]["total"] / total * 100, 2) if top5 and total else 0
    return {"top_5": top5, "total": total, "pct_mayor": pct}


def anomalias_financieras() -> dict:
    docs = list(_col().find(
        {"valor_del_contrato": {"$exists": True, "$ne": None}},
        {"id_contrato": 1, "nombre_entidad": 1, "valor_del_contrato": 1,
         "tipo_de_contrato": 1, "estado_contrato": 1},
    ))
    valores = [(parse_money(d.get("valor_del_contrato")), d) for d in docs]
    valores = [(v, d) for v, d in valores if v > 0]
    nums = [v for v, _ in valores]
    n = len(nums)
    if n == 0:
        return {"estadisticas": None, "top_3_anomalos": []}
    media = sum(nums) / n
    std = (sum((x - media) ** 2 for x in nums) / n) ** 0.5
    s = sorted(nums)
    q1, q3 = s[n // 4], s[3 * n // 4]
    umbral = q3 + 3 * (q3 - q1)
    anomalos = sorted([(v, d) for v, d in valores if v > umbral],
                      key=lambda x: x[0], reverse=True)[:3]
    return {
        "estadisticas": {"media": round(media, 2), "desviacion_std": round(std, 2),
                         "q1": round(q1, 2), "q3": round(q3, 2),
                         "umbral_anomalia": round(umbral, 2)},
        "top_3_anomalos": [
            {"posicion": i + 1, "id_contrato": d.get("id_contrato"),
             "entidad": d.get("nombre_entidad"), "tipo": d.get("tipo_de_contrato"),
             "estado": d.get("estado_contrato"), "valor": round(v, 2), "es_anomalo": True,
             "sustento": f"Valor {round(v/umbral,1)}x por encima del umbral IQR"}
            for i, (v, d) in enumerate(anomalos)
        ],
    }


def pagos_adelantados() -> dict:
    col = _col()
    total = col.estimated_document_count()
    con_anticipo = col.count_documents({"habilita_pago_adelantado": "Si"})
    return {"total": total, "con_anticipo": con_anticipo}


def obligaciones_ambientales() -> dict:
    col = _col()
    total = col.estimated_document_count()
    con_ambiental = col.count_documents({"obligacin_ambiental": "Si"})
    return {"total": total, "con_ambiental": con_ambiental}


# ⚡ Bolt: Replaced python-side document scanning and summing with an in-database MongoDB aggregation pipeline.
# This shifts the heavy O(N) grouping and summing workload from application memory to the database engine.
def pareto() -> dict:
    pipeline = [
        {"$match": {
            "valor_del_contrato": {"$exists": True, "$ne": None},
            "nombre_entidad": {"$exists": True, "$ne": None}
        }},
        {"$addFields": {"_valor": _TO_DOUBLE}},
        {"$group": {
            "_id": {"$cond": [{"$in": ["$nombre_entidad", ["", None]]}, "Sin nombre", "$nombre_entidad"]},
            "total_valor": {"$sum": "$_valor"}
        }}
    ]
    docs = list(_col().aggregate(pipeline, allowDiskUse=True))
    ordered = sorted([d["total_valor"] for d in docs], reverse=True)
    n_entidades = len(ordered)
    valor_total = sum(ordered)
    top_20_n = max(1, int(n_entidades * 0.20))
    pct = round(sum(ordered[:top_20_n]) / valor_total * 100, 2) if valor_total else 0
    return {"n_entidades": n_entidades, "top_20_pct_n": top_20_n,
            "pct_valor_top_20": pct, "se_cumple": pct >= 75}


# ⚡ Bolt: Replaced python-side document scanning and summing with an in-database MongoDB aggregation pipeline.
# This shifts the heavy O(N) grouping and summing workload from application memory to the database engine.
def brecha_genero() -> list:
    pipeline = [
        {"$match": {
            "gnero_representante_legal": {"$exists": True, "$ne": None},
            "valor_del_contrato": {"$exists": True, "$ne": None}
        }},
        {"$addFields": {"_valor": _TO_DOUBLE}},
        {"$group": {
            "_id": {"$cond": [{"$in": ["$gnero_representante_legal", ["", None]]}, "No definido", "$gnero_representante_legal"]},
            "valor_total": {"$sum": "$_valor"},
            "num_contratos": {"$sum": 1}
        }}
    ]
    docs = list(_col().aggregate(pipeline, allowDiskUse=True))
    valor_total = sum(d["valor_total"] for d in docs)
    return sorted(
        [{"genero": d["_id"], "num_contratos": d["num_contratos"], "valor_total": round(d["valor_total"], 2),
          "pct_valor": round(d["valor_total"] / valor_total * 100, 2) if valor_total else 0}
         for d in docs],
        key=lambda x: x["valor_total"], reverse=True,
    )


def variables() -> list:
    doc = _col().find_one()
    return [k for k in doc.keys() if k != "_id"] if doc else []
