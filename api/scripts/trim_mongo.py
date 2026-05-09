import argparse
from pymongo import MongoClient

parser = argparse.ArgumentParser()
parser.add_argument("--mongo-uri", default="mongodb://localhost:27017")
parser.add_argument("--limit", type=int, default=100000)
args = parser.parse_args()

col = MongoClient(args.mongo_uri)["ai_analyzer"]["contratos-electronicos"]
total = col.count_documents({})
print(f"Total antes: {total}")

if total <= args.limit:
    print("No hay nada que borrar.")
else:
    ids = [d["_id"] for d in col.find({}, {"_id": 1}).skip(args.limit)]
    result = col.delete_many({"_id": {"$in": ids}})
    print(f"Eliminados: {result.deleted_count}")
    print(f"Quedaron: {col.count_documents({})}")
