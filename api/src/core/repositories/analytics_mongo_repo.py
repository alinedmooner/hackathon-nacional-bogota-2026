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


# ⚡ Bolt: Pushed parsing and grouping to Mongo Aggregation Pipelines for anomaly detection.
# Avoids reading all documents into Python memory, replacing O(N) memory footprint with O(1) by calculating
# stats (avg, stdDev, Q1, Q3) and fetching top anomalies entirely inside the database engine.
def anomalias_financieras() -> dict:
    base_pipeline = [
        {"$match": {"valor_del_contrato": {"$exists": True, "$ne": None}}},
        {"$addFields": {"_valor": _TO_DOUBLE}},
        {"$match": {"_valor": {"$gt": 0}}}
    ]

    stats_pipeline = base_pipeline + [
        {"$group": {
            "_id": None,
            "media": {"$avg": "$_valor"},
            "stdDev": {"$stdDevPop": "$_valor"},
            "count": {"$sum": 1}
        }}
    ]

    stats_res = list(_col().aggregate(stats_pipeline))
    if not stats_res or stats_res[0]["count"] == 0:
        return {"estadisticas": None, "top_3_anomalos": []}

    stats = stats_res[0]
    n = stats["count"]
    media = stats["media"]
    std = stats.get("stdDev", 0)

    q1_pipeline = base_pipeline + [
        {"$sort": {"_valor": 1}},
        {"$skip": n // 4},
        {"$limit": 1},
        {"$project": {"_valor": 1}}
    ]
    q1_res = list(_col().aggregate(q1_pipeline, allowDiskUse=True))
    q1 = q1_res[0]["_valor"] if q1_res else 0

    q3_pipeline = base_pipeline + [
        {"$sort": {"_valor": 1}},
        {"$skip": 3 * n // 4},
        {"$limit": 1},
        {"$project": {"_valor": 1}}
    ]
    q3_res = list(_col().aggregate(q3_pipeline, allowDiskUse=True))
    q3 = q3_res[0]["_valor"] if q3_res else 0

    umbral = q3 + 3 * (q3 - q1)

    anomalos_pipeline = base_pipeline + [
        {"$match": {"_valor": {"$gt": umbral}}},
        {"$sort": {"_valor": -1}},
        {"$limit": 3},
        {"$project": {
            "id_contrato": 1,
            "nombre_entidad": 1,
            "tipo_de_contrato": 1,
            "estado_contrato": 1,
            "_valor": 1
        }}
    ]

    anomalos_docs = list(_col().aggregate(anomalos_pipeline, allowDiskUse=True))

    return {
        "estadisticas": {
            "media": round(media, 2),
            "desviacion_std": round(std, 2),
            "q1": round(q1, 2),
            "q3": round(q3, 2),
            "umbral_anomalia": round(umbral, 2)
        },
        "top_3_anomalos": [
            {
                "posicion": i + 1,
                "id_contrato": d.get("id_contrato"),
                "entidad": d.get("nombre_entidad"),
                "tipo": d.get("tipo_de_contrato"),
                "estado": d.get("estado_contrato"),
                "valor": round(d.get("_valor", 0), 2),
                "es_anomalo": True,
                "sustento": f"Valor {round(d.get('_valor', 0)/umbral,1)}x por encima del umbral IQR" if umbral > 0 else "Valor por encima del umbral IQR"
            }
            for i, d in enumerate(anomalos_docs)
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
