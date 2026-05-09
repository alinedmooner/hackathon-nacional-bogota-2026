"""Descarga un dataset de Socrata (datos.gov.co) y lo guarda como parquet.

Uso:
    python scripts/socrata_to_parquet.py --dataset-id iaeu-rcn6 --output data/siri.parquet
    python scripts/socrata_to_parquet.py --dataset-id 4n4q-k399 --output data/multas_secop1.parquet
    python scripts/socrata_to_parquet.py --dataset-id 8tz7-h3eu --output data/patrimoniales.parquet

Las transformaciones específicas por dataset se aplican automáticamente según --dataset-id.
Requiere ejecutar desde api/ con PYTHONPATH=.
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://www.datos.gov.co/resource/{dataset_id}.json"
PAGE_SIZE = 50_000


def _fetch_page(dataset_id: str, offset: int, token: str) -> list[dict]:
    url = BASE_URL.format(dataset_id=dataset_id)
    headers = {"X-App-Token": token} if token else {}
    r = requests.get(
        url,
        params={"$limit": PAGE_SIZE, "$offset": offset, "$order": ":id"},
        headers=headers,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def _download(dataset_id: str, token: str) -> pd.DataFrame:
    rows: list[dict] = []
    offset = 0
    while True:
        print(f"  página offset={offset:,} ...", end=" ", flush=True)
        t0 = time.time()
        batch = _fetch_page(dataset_id, offset, token)
        elapsed = time.time() - t0
        if not batch:
            print("vacía — fin de descarga")
            break
        rows.extend(batch)
        print(f"{len(batch):,} registros ({elapsed:.1f}s)")
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return pd.DataFrame(rows)


# ── transformaciones por dataset ──────────────────────────────────────────────

def _normalize_doc(series: pd.Series) -> pd.Series:
    """Quita todo excepto dígitos. Equivale al REGEXP_REPLACE de DuckDB."""
    return series.astype(str).str.strip().str.replace(r"[^0-9]", "", regex=True)


def _transform_siri(df: pd.DataFrame) -> pd.DataFrame:
    """SIRI iaeu-rcn6: parsea fechas DD/MM/YYYY, duraciones a int, normaliza doc."""
    df["fecha_efectos_juridicos"] = pd.to_datetime(
        df.get("fecha_efectos_juridicos", pd.Series(dtype=str)),
        format="%d/%m/%Y",
        errors="coerce",
    )
    for col in ("duracion_anos", "duracion_mes", "duracion_dias"):
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0).astype(int)

    df["numero_identificacion"] = _normalize_doc(df.get("numero_identificacion", pd.Series(dtype=str)))

    # fecha_fin calculada: solo cuando duracion_anos > 0
    from dateutil.relativedelta import relativedelta

    def _calc_fin(row):
        if pd.isna(row["fecha_efectos_juridicos"]):
            return pd.NaT
        if row["duracion_anos"] == 0 and row["duracion_mes"] == 0 and row["duracion_dias"] == 0:
            return pd.NaT
        return row["fecha_efectos_juridicos"] + relativedelta(
            years=int(row["duracion_anos"]),
            months=int(row["duracion_mes"]),
            days=int(row["duracion_dias"]),
        )

    print("  Calculando fecha_fin_sancion ...", flush=True)
    df["fecha_fin_sancion"] = df.apply(_calc_fin, axis=1)
    return df


def _transform_multas(df: pd.DataFrame) -> pd.DataFrame:
    """Multas SECOP I 4n4q-k399: normaliza documento y valor."""
    df["documento_contratista"] = _normalize_doc(df.get("documento_contratista", pd.Series(dtype=str)))
    df["valor_sancion"] = pd.to_numeric(df.get("valor_sancion", 0), errors="coerce").fillna(0)
    for col in ("fecha_de_publicacion", "fecha_de_firmeza", "fecha_de_cargue"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _transform_patrimoniales(df: pd.DataFrame) -> pd.DataFrame:
    """Declaraciones patrimoniales 8tz7-h3eu: normaliza documento."""
    df["numero_documento"] = _normalize_doc(df.get("numero_documento", pd.Series(dtype=str)))
    if "fecha_publicac_declarac" in df.columns:
        df["fecha_publicac_declarac"] = pd.to_datetime(df["fecha_publicac_declarac"], errors="coerce")
    return df


_TRANSFORMS = {
    "iaeu-rcn6": _transform_siri,
    "4n4q-k399": _transform_multas,
    "8tz7-h3eu": _transform_patrimoniales,
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s/\\]+", "_", regex=True)
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    return df


def main():
    parser = argparse.ArgumentParser(description="Descarga dataset Socrata → parquet")
    parser.add_argument("--dataset-id", required=True, help="ID del dataset en datos.gov.co")
    parser.add_argument("--output", required=True, help="Ruta de salida del parquet")
    parser.add_argument("--token", default="", help="App Token de Socrata (opcional, evita throttling)")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Descargando dataset {args.dataset_id} → {output}")
    df = _download(args.dataset_id, args.token)

    if df.empty:
        print("ERROR: no se descargaron registros.", file=sys.stderr)
        sys.exit(1)

    print(f"  {len(df):,} registros, {len(df.columns)} columnas")

    df = _normalize_columns(df)

    transform = _TRANSFORMS.get(args.dataset_id)
    if transform:
        print(f"  Aplicando transformaciones para {args.dataset_id} ...")
        df = transform(df)
    else:
        print(f"  Sin transformaciones específicas para {args.dataset_id}.")

    df.to_parquet(output, index=False, compression="snappy")
    size_mb = output.stat().st_size / 1024 / 1024
    print(f"Parquet guardado: {output} ({size_mb:.1f} MB) — {len(df):,} registros")


if __name__ == "__main__":
    main()
