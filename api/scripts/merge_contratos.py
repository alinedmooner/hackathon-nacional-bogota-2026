"""Merge de múltiples CSVs de SECOP II en un solo contratos.parquet.

Uso:
    python scripts/merge_contratos.py data/*.csv --output data/contratos.parquet

El script normaliza columnas, descarta duplicados por id_contrato
y combina con el parquet existente si ya hay uno.
"""
import argparse
import glob
import sys
from pathlib import Path

import pandas as pd


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s/\\]+", "_", regex=True)
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    return df


def _load_csv(path: str) -> pd.DataFrame:
    print(f"  Leyendo {path}...")
    df = pd.read_csv(
        path, dtype=str, encoding="utf-8",
        on_bad_lines="skip", low_memory=False,
    )
    df = _normalize_cols(df)
    print(f"    {len(df):,} registros, {len(df.columns)} columnas")
    return df


def main():
    parser = argparse.ArgumentParser(description="Merge CSVs SECOP II → contratos.parquet")
    parser.add_argument(
        "csvs", nargs="+",
        help="Uno o más archivos CSV (acepta glob: data/*.csv)",
    )
    parser.add_argument(
        "--output", default="data/contratos.parquet",
        help="Parquet de salida (default: data/contratos.parquet)",
    )
    parser.add_argument(
        "--no-existing", action="store_true",
        help="Ignorar el parquet existente y crear uno nuevo desde cero",
    )
    args = parser.parse_args()

    # Expandir globs manualmente (útil en shells que no los expanden)
    paths: list[str] = []
    for pattern in args.csvs:
        expanded = glob.glob(pattern)
        paths.extend(expanded if expanded else [pattern])

    if not paths:
        print("ERROR: no se encontraron archivos CSV.", file=sys.stderr)
        sys.exit(1)

    frames: list[pd.DataFrame] = []

    # Cargar parquet existente
    output = Path(args.output)
    if output.exists() and not args.no_existing:
        print(f"Cargando parquet existente: {output} ...")
        existing = pd.read_parquet(output)
        print(f"  {len(existing):,} registros existentes")
        frames.append(existing)

    # Cargar cada CSV nuevo
    for p in paths:
        frames.append(_load_csv(p))

    print(f"\nCombinando {len(frames)} fuentes...")
    combined = pd.concat(frames, ignore_index=True)
    print(f"  Total antes de deduplicar: {len(combined):,}")

    # Deduplicar por id_contrato si existe la columna
    if "id_contrato" in combined.columns:
        combined = combined.drop_duplicates(subset=["id_contrato"], keep="last")
        print(f"  Total después de deduplicar: {len(combined):,}")

    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output, index=False, compression="snappy")
    size_mb = output.stat().st_size / 1024 / 1024
    print(f"\n✅ Parquet guardado: {output} ({size_mb:.1f} MB)")
    print(f"   Registros totales: {len(combined):,}")

    # Mostrar rango de fechas si aplica
    if "fecha_de_firma" in combined.columns:
        fechas = combined["fecha_de_firma"].dropna()
        if not fechas.empty:
            print(f"   Fecha mínima: {fechas.min()}")
            print(f"   Fecha máxima: {fechas.max()}")


if __name__ == "__main__":
    main()
