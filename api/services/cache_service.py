from datetime import datetime
from db import get_db


def get(key: str):
    doc = get_db()["analytics_cache"].find_one({"_id": key})
    return doc["data"] if doc else None


def set(key: str, data: dict):
    get_db()["analytics_cache"].replace_one(
        {"_id": key},
        {"_id": key, "data": data, "cached_at": datetime.now()},
        upsert=True,
    )


def cached(key: str, compute):
    hit = get(key)
    if hit is not None:
        return {**hit, "_cache": "hit"}
    result = compute()
    set(key, result)
    return {**result, "_cache": "miss"}


def clear_all() -> int:
    return get_db()["analytics_cache"].delete_many({}).deleted_count
