"""
Carga el CSV de Contratos Electrónicos SECOP II a MongoDB.
Uso:
    python scripts/csv_to_mongo.py --file data/SECOP_II_-_Contratos_Electrónicos_20260506.csv
"""
import argparse
import math
import sys
from pathlib import Path

import pandas as pd
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

from config import settings

COLLECTION = "contratos-electronicos"
BATCH_SIZE = 5_000


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # Normalizar nombres de columnas: minúsculas, espacios → _, sin caracteres especiales
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s/\\]+", "_", regex=True)
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    # Reemplazar NaN por None para que Mongo no los rechace
    return df.where(df.notna(), other=None)


def load(csv_path: Path, mongo_uri: str, drop: bool = False) -> None:
    client = MongoClient(mongo_uri)
    db = client["secop"]
    col = db[COLLECTION]

    if drop:
        col.drop()
        print(f"Colección '{COLLECTION}' eliminada.")

    col.create_index("id_contrato", unique=True, sparse=True)

    total_rows = sum(1 for _ in open(csv_path, encoding="utf-8")) - 1
    total_batches = math.ceil(total_rows / BATCH_SIZE)
    print(f"Archivo : {csv_path.name}")
    print(f"Registros: {total_rows:,}  |  Lotes: {total_batches}  |  Colección: {COLLECTION}\n")

    inserted = updated = errors = 0
    chunk_iter = pd.read_csv(
        csv_path,
        chunksize=BATCH_SIZE,
        dtype=str,          # Todo como string para evitar problemas de tipos
        encoding="utf-8",
        on_bad_lines="skip",
    )

    for i, chunk in enumerate(chunk_iter, 1):
        chunk = clean(chunk)
        records = chunk.to_dict(orient="records")

        with_id    = [r for r in records if r.get("id_contrato")]
        without_id = [r for r in records if not r.get("id_contrato")]

        try:
            if with_id:
                ops = [
                    UpdateOne(
                        {"id_contrato": r["id_contrato"]},
                        {"$set": r},
                        upsert=True,
                    )
                    for r in with_id
                ]
                result = col.bulk_write(ops, ordered=False)
                inserted += result.upserted_count
                updated  += result.modified_count

            if without_id:
                col.insert_many(without_id, ordered=False)
                inserted += len(without_id)

        except BulkWriteError as e:
            errors += len(e.details.get("writeErrors", []))

        pct = i / total_batches * 100
        print(f"  Lote {i:>4}/{total_batches}  ({pct:5.1f}%)  "
              f"insertados={inserted:,}  actualizados={updated:,}  errores={errors}", end="\r")

    print("\n\nListo.")
    print(f"  Insertados : {inserted:,}")
    print(f"  Actualizados: {updated:,}")
    print(f"  Errores    : {errors:,}")
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Ruta al archivo CSV")
    parser.add_argument("--mongo-uri", default=settings.mongo_uri, help="URI de MongoDB")
    parser.add_argument("--drop", action="store_true", help="Eliminar la colección antes de cargar")
    args = parser.parse_args()

    csv_path = Path(args.file)
    if not csv_path.exists():
        print(f"Archivo no encontrado: {csv_path}", file=sys.stderr)
        sys.exit(1)

    load(csv_path, args.mongo_uri, drop=args.drop)
