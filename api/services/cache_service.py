import threading
from datetime import datetime
from db import get_db

_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _get_lock(key: str) -> threading.Lock:
    with _locks_guard:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]


def _is_valid(result: dict) -> bool:
    lists = [v for v in result.values() if isinstance(v, list)]
    if not lists:
        return True
    return any(len(lst) > 0 for lst in lists)


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
        return {**hit, "_cache": "hit", "_cache_id": key}

    with _get_lock(key):
        hit = get(key)
        if hit is not None:
            return {**hit, "_cache": "hit", "_cache_id": key}

        result = compute()
        if _is_valid(result):
            set(key, result)
        return {**result, "_cache": "miss", "_cache_id": key}


def clear_all() -> int:
    return get_db()["analytics_cache"].delete_many({}).deleted_count


def delete_one(cache_id: str) -> bool:
    result = get_db()["analytics_cache"].delete_one({"_id": cache_id})
    return result.deleted_count > 0
