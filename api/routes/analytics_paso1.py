from datetime import datetime
from fastapi import APIRouter, Depends
import pandas as pd
from security import get_current_user
from datasets import ArchivosDataset
from soql_query import SoQLQuery

router = APIRouter(prefix="/paso1/analytics", tags=["paso1-analytics"])

A = ArchivosDataset


def _q() -> SoQLQuery:
    return SoQLQuery(A.ID)


def _count_total() -> int:
    df = _q().select("COUNT(*) AS total").fetch()
    return int(df["total"].iloc[0])


def _median_numeric(field: str, total_no_nulos: int) -> float | None:
    """Calcula la mediana via ORDER BY + OFFSET en SoQL (solo campos numéricos)."""
    if total_no_nulos == 0:
        return None
    base = _q().select(field).where(f"{field} IS NOT NULL").order_by(field)
    if total_no_nulos % 2 == 1:
        df = base.limit(1).offset(total_no_nulos // 2).fetch()
        vals = df[field].tolist()
        return float(vals[0]) if vals else None
    else:
        df = base.limit(2).offset(total_no_nulos // 2 - 1).fetch()
        vals = [float(v) for v in df[field].tolist() if v is not None]
        return sum(vals) / len(vals) if len(vals) == 2 else (vals[0] if vals else None)


def _num_stats(field: str) -> dict:
    df = _q().select(
        f"max({field}) AS max_val",
        f"min({field}) AS min_val",
        f"avg({field}) AS avg_val",
        f"COUNT({field}) AS no_nulos",
    ).fetch()
    row = df.iloc[0]
    total_no_nulos = int(row["no_nulos"])
    mediana = _median_numeric(field, total_no_nulos)
    return {
        "max": float(row["max_val"]) if row.get("max_val") is not None else None,
        "min": float(row["min_val"]) if row.get("min_val") is not None else None,
        "media": round(float(row["avg_val"]), 4) if row.get("avg_val") is not None else None,
        "mediana": round(mediana, 4) if mediana is not None else None,
        "registros_no_nulos": total_no_nulos,
    }


# ──────────────────────────────────────────────────────────────
# Q1 — Total registros
# ──────────────────────────────────────────────────────────────
@router.get("/total-registros")
def total_registros(current_user: dict = Depends(get_current_user)):
    total = _count_total()
    return {"pregunta": 1, "dataset": A.ID, "total_registros": total}


# ──────────────────────────────────────────────────────────────
# Q2 — Total columnas
# ──────────────────────────────────────────────────────────────
@router.get("/total-columnas")
def total_columnas(current_user: dict = Depends(get_current_user)):
    df = _q().limit(1).fetch()
    cols = list(df.columns)
    return {"pregunta": 2, "total_columnas": len(cols), "columnas": cols}


# ──────────────────────────────────────────────────────────────
# Q3 — Nulos en descripción
# ──────────────────────────────────────────────────────────────
@router.get("/nulos-descripcion")
def nulos_descripcion(current_user: dict = Depends(get_current_user)):
    total = _count_total()
    df = _q().select(f"COUNT({A.DESCRIPCION}) AS no_nulos").fetch()
    no_nulos = int(df["no_nulos"].iloc[0])
    nulos = total - no_nulos
    return {
        "pregunta": 3,
        "campo": A.DESCRIPCION,
        "total_registros": total,
        "no_nulos": no_nulos,
        "nulos": nulos,
        "porcentaje_nulos": round(nulos / total * 100, 2) if total else 0,
    }


# ──────────────────────────────────────────────────────────────
# Q4 — Nulos en proceso
# ──────────────────────────────────────────────────────────────
@router.get("/nulos-proceso")
def nulos_proceso(current_user: dict = Depends(get_current_user)):
    total = _count_total()
    df = _q().select(f"COUNT({A.PROCESO}) AS no_nulos").fetch()
    no_nulos = int(df["no_nulos"].iloc[0])
    nulos = total - no_nulos
    return {
        "pregunta": 4,
        "campo": A.PROCESO,
        "total_registros": total,
        "no_nulos": no_nulos,
        "nulos": nulos,
        "porcentaje_nulos": round(nulos / total * 100, 2) if total else 0,
    }


# ──────────────────────────────────────────────────────────────
# Q5 y Q6 — Tipos de columnas (int64 vs str)
# ──────────────────────────────────────────────────────────────
@router.get("/tipos-columnas")
def tipos_columnas(current_user: dict = Depends(get_current_user)):
    df = _q().limit(300).fetch()
    int_cols, float_cols, str_cols = [], [], []

    for col in df.columns:
        serie = df[col].dropna()
        if serie.empty:
            str_cols.append(col)
            continue
        try:
            numeric = pd.to_numeric(serie, errors="raise")
            if (numeric % 1 == 0).all():
                int_cols.append(col)
            else:
                float_cols.append(col)
        except (ValueError, TypeError):
            str_cols.append(col)

    return {
        "pregunta": "5 y 6",
        "int64": {"columnas": int_cols, "total": len(int_cols)},
        "float64": {"columnas": float_cols, "total": len(float_cols)},
        "str_object": {"columnas": str_cols, "total": len(str_cols)},
    }


# ──────────────────────────────────────────────────────────────
# Q7 — Stats ID documento
# ──────────────────────────────────────────────────────────────
@router.get("/stats-id-documento")
def stats_id_documento(current_user: dict = Depends(get_current_user)):
    stats = _num_stats(A.ID_DOCUMENTO)
    return {"pregunta": 7, "campo": A.ID_DOCUMENTO, **stats}


# ──────────────────────────────────────────────────────────────
# Q8 — Stats tamaño archivo
# ──────────────────────────────────────────────────────────────
@router.get("/stats-tamano-archivo")
def stats_tamano_archivo(current_user: dict = Depends(get_current_user)):
    stats = _num_stats(A.TAMANNO_ARCHIVO)
    return {"pregunta": 8, "campo": A.TAMANNO_ARCHIVO, "unidad": "bytes", **stats}


# ──────────────────────────────────────────────────────────────
# Q9 — Stats nit_entidad
# ──────────────────────────────────────────────────────────────
@router.get("/stats-nit-entidad")
def stats_nit_entidad(current_user: dict = Depends(get_current_user)):
    stats = _num_stats(A.NIT_ENTIDAD)
    return {
        "pregunta": 9,
        "campo": A.NIT_ENTIDAD,
        "nota": "NIT es un identificador; estadísticas son orientativas",
        **stats,
    }


# ──────────────────────────────────────────────────────────────
# Q10 y Q11 — Máx/mín y rango de fecha_carga
# ──────────────────────────────────────────────────────────────
@router.get("/rango-fecha-carga")
def rango_fecha_carga(current_user: dict = Depends(get_current_user)):
    df = _q().select(
        f"max({A.FECHA_CARGA}) AS max_fecha",
        f"min({A.FECHA_CARGA}) AS min_fecha",
    ).fetch()
    row = df.iloc[0]
    max_f: str = row["max_fecha"]
    min_f: str = row["min_fecha"]

    rango_dias = None
    rango_str = None
    try:
        def parse_iso(s: str) -> datetime:
            return datetime.fromisoformat(s.replace("Z", "+00:00").rstrip("0").rstrip(".") or s[:19])
        max_dt = parse_iso(max_f)
        min_dt = parse_iso(min_f)
        delta = max_dt - min_dt
        rango_dias = delta.days
        years, rem = divmod(delta.days, 365)
        months, days = divmod(rem, 30)
        rango_str = f"{years} años, {months} meses, {days} días"
    except Exception:
        pass

    return {
        "pregunta": "10 y 11",
        "campo": A.FECHA_CARGA,
        "fecha_maxima": max_f,
        "fecha_minima": min_f,
        "rango_dias": rango_dias,
        "rango": rango_str,
    }


# ──────────────────────────────────────────────────────────────
# Q12 — nombre_archivo y fecha_carga para ID Documento dado
# ──────────────────────────────────────────────────────────────
@router.get("/documento-por-id")
def documento_por_id(
    id_documento: int = 756926574,
    current_user: dict = Depends(get_current_user),
):
    df = _q().select(
        A.ID_DOCUMENTO,
        A.NOMBRE_ARCHIVO,
        A.FECHA_CARGA,
        A.EXTENSION,
        A.TAMANNO_ARCHIVO,
        A.ENTIDAD,
    ).where(f"{A.ID_DOCUMENTO} = {id_documento}").fetch()

    if df.empty:
        return {"pregunta": 12, "id_documento": id_documento, "resultado": None, "mensaje": "No encontrado"}

    row = df.iloc[0]
    return {
        "pregunta": 12,
        "id_documento": id_documento,
        "nombre_archivo": row.get(A.NOMBRE_ARCHIVO),
        "fecha_carga": row.get(A.FECHA_CARGA),
        "extension": row.get(A.EXTENSION),
        "tamano_archivo_bytes": row.get(A.TAMANNO_ARCHIVO),
        "entidad": row.get(A.ENTIDAD),
    }
