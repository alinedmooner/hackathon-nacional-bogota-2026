"""Persistencia de conversaciones · Mongo si está disponible, fallback a memoria."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from config import settings

logger = logging.getLogger(__name__)

# Fallback en memoria si Mongo no está disponible
_memory_conversations: dict[str, dict] = {}

_db = None
_mongo_unavailable = False


def _get_collection(name: str):
    """Devuelve la colección Mongo o None si Mongo no está disponible."""
    global _db, _mongo_unavailable
    if _mongo_unavailable:
        return None
    if _db is None:
        try:
            client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            _db = client["ai_analyzer"]
            logger.info("Mongo conectado para persistencia IA")
        except (ServerSelectionTimeoutError, PyMongoError) as exc:
            logger.warning("Mongo no disponible (%s) — usando memoria", exc)
            _mongo_unavailable = True
            return None
    return _db[name]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_conversation(user_sub: str, title: str | None = None) -> str:
    conv_id = str(uuid.uuid4())
    doc = {
        "_id": conv_id,
        "user_sub": user_sub,
        "title": title or "Nueva conversación",
        "created_at": _now(),
        "updated_at": _now(),
        "messages": [],
    }
    coll = _get_collection("ai_conversations")
    if coll is not None:
        try:
            coll.insert_one(doc)
        except PyMongoError as exc:
            logger.warning("insert_one falló (%s) — fallback memoria", exc)
            _memory_conversations[conv_id] = doc
    else:
        _memory_conversations[conv_id] = doc
    return conv_id


def get_conversation(conv_id: str, user_sub: str) -> dict | None:
    coll = _get_collection("ai_conversations")
    if coll is not None:
        try:
            return coll.find_one({"_id": conv_id, "user_sub": user_sub})
        except PyMongoError:
            pass
    doc = _memory_conversations.get(conv_id)
    if doc and doc.get("user_sub") == user_sub:
        return doc
    return None


def append_messages(conv_id: str, user_sub: str, messages: list[dict]) -> None:
    coll = _get_collection("ai_conversations")
    update = {
        "$push": {"messages": {"$each": messages}},
        "$set": {"updated_at": _now()},
    }
    if coll is not None:
        try:
            coll.update_one({"_id": conv_id, "user_sub": user_sub}, update)
            return
        except PyMongoError:
            pass
    doc = _memory_conversations.get(conv_id)
    if doc:
        doc["messages"].extend(messages)
        doc["updated_at"] = _now()


def list_conversations(user_sub: str, limit: int = 50) -> list[dict]:
    coll = _get_collection("ai_conversations")
    if coll is not None:
        try:
            cursor = coll.find(
                {"user_sub": user_sub},
                {"messages": 0},
            ).sort("updated_at", -1).limit(limit)
            return [_serialize(d) for d in cursor]
        except PyMongoError:
            pass
    items = [
        d for d in _memory_conversations.values() if d.get("user_sub") == user_sub
    ]
    items.sort(key=lambda d: d.get("updated_at"), reverse=True)
    return [_serialize({**d, "messages": []}) for d in items[:limit]]


def _serialize(doc: dict[str, Any]) -> dict:
    out = dict(doc)
    out["conversation_id"] = out.pop("_id", None)
    for key in ("created_at", "updated_at"):
        if key in out and isinstance(out[key], datetime):
            out[key] = out[key].isoformat()
    return out
