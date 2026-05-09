import argparse
from pathlib import Path
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True, help="Ruta al CSV de SECOP")
parser.add_argument("--output", default="data/contratos.parquet")
args = parser.parse_args()

print(f"Leyendo {args.file}...")
df = pd.read_csv(args.file, dtype=str, encoding="utf-8", on_bad_lines="skip", low_memory=False)
print(f"  {len(df):,} registros, {len(df.columns)} columnas")

# Misma normalización que csv_to_mongo.py
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(r"[\s/\\]+", "_", regex=True)
    .str.replace(r"[^a-z0-9_]", "", regex=True)
)
print(f"  Columnas normalizadas: {list(df.columns[:5])} ...")

output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(output, index=False, compression="snappy")
print(f"Parquet guardado en {output} ({output.stat().st_size / 1024 / 1024:.1f} MB)")
