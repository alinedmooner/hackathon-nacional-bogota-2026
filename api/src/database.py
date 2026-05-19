from functools import lru_cache
from pymongo import MongoClient
from pymongo.database import Database

from src.core.config import settings


@lru_cache(maxsize=1)
def get_client() -> MongoClient:
    return MongoClient(settings.mongo_uri)

def get_db() -> Database:
    return get_client()["secop"]
