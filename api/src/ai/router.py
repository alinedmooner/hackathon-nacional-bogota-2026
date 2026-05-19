"""Router del agente IA · /ai/*."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.core.datasets import ArchivosDataset, ContratosDataset
from src.core.models.ai_chat import (
    ChartItem,
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationSummary,
    DatasetInfo,
    FieldInfo,
    ToolCallLog,
    Usage,
)
from src.core.security import get_current_user
from src.ai.services import orchestrator, persistence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])


def _user_sub(user: dict) -> str:
    return user.get("sub", "anonymous")


def _history_for_llm(conv: dict | None) -> list[dict]:
    """Reconstruye el historial para el LLM: solo texto user/assistant final.

    Descarta tool_calls/charts/etc para evitar pares tool_call sin tool_result.
    """
    if not conv:
        return []
    out: list[dict] = []
    for m in conv.get("messages", []):
        role = m.get("role")
        content = m.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content:
            out.append({"role": role, "content": content})
    return out


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_sub = _user_sub(current_user)

    # Cargar conversación existente o crear nueva
    if body.conversation_id:
        conv = persistence.get_conversation(body.conversation_id, user_sub)
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="conversation_id no encontrada",
            )
        history = _history_for_llm(conv)
        conv_id = body.conversation_id
    else:
        conv_id = persistence.create_conversation(
            user_sub=user_sub,
            title=body.message[:60],
        )
        history = []

    try:
        result = orchestrator.chat(user_message=body.message, history=history)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    # Persistir solo los mensajes nuevos (user + asistente final)
    new_messages = [
        {"role": "user", "content": body.message},
        {
            "role": "assistant",
            "content": result["answer"],
            "tool_calls": result["tool_calls"],
            "charts": result["charts"],
        },
    ]
    persistence.append_messages(conv_id, user_sub, new_messages)

    return ChatResponse(
        conversation_id=conv_id,
        answer=result["answer"],
        tool_calls=[ToolCallLog(**tc) for tc in result["tool_calls"]],
        charts=[ChartItem(**c) for c in result["charts"]],
        usage=Usage(**result["usage"]),
        latency_ms=result["latency_ms"],
    )


@router.post("/chat/stream")
def chat_stream(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Streaming SSE del razonamiento del agente.

    Emite eventos Server-Sent Events con el tipo:
      thinking   → el agente está pensando (iteración N)
      tool_call  → nombre y args de la tool que se va a ejecutar
      tool_result→ resumen del resultado
      chart      → spec Chart.js listo para renderizar
      answer     → texto final del agente
      done       → métricas finales (usage, latency_ms)
    """
    user_sub = _user_sub(current_user)

    if body.conversation_id:
        conv = persistence.get_conversation(body.conversation_id, user_sub)
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="conversation_id no encontrada",
            )
        history = _history_for_llm(conv)
        conv_id = body.conversation_id
    else:
        conv_id = persistence.create_conversation(
            user_sub=user_sub,
            title=body.message[:60],
        )
        history = []

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"

    def generate():
        yield _sse({"type": "init", "conversation_id": conv_id})

        answer_text = ""
        final_tool_calls: list[dict] = []
        final_charts: list[dict] = []
        final_usage: dict = {}
        final_latency: int = 0

        try:
            for event in orchestrator.chat_stream(
                user_message=body.message, history=history
            ):
                if event["type"] == "answer":
                    answer_text = event["text"]
                    yield _sse(event)
                elif event["type"] == "done":
                    final_tool_calls = event["tool_calls"]
                    final_charts = event["charts"]
                    final_usage = event["usage"]
                    final_latency = event["latency_ms"]
                    # Persistir antes de emitir done
                    new_messages = [
                        {"role": "user", "content": body.message},
                        {
                            "role": "assistant",
                            "content": answer_text,
                            "tool_calls": final_tool_calls,
                            "charts": final_charts,
                        },
                    ]
                    try:
                        persistence.append_messages(conv_id, user_sub, new_messages)
                    except Exception as exc:
                        logger.warning("stream: error al persistir: %s", exc)
                    yield _sse({
                        "type": "done",
                        "conversation_id": conv_id,
                        "usage": final_usage,
                        "latency_ms": final_latency,
                    })
                else:
                    yield _sse(event)
        except Exception as exc:
            logger.exception("stream: error en orchestrator")
            yield _sse({"type": "error", "detail": str(exc)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/datasets", response_model=list[DatasetInfo])
def datasets(current_user: dict = Depends(get_current_user)):
    return [
        DatasetInfo(
            id=ContratosDataset.ID,
            name="SECOP – Contratos",
            fields=[
                FieldInfo(name=v, type=_guess_type(v))
                for k, v in vars(ContratosDataset).items()
                if isinstance(v, str) and not k.startswith("_") and k.isupper() and k != "ID"
            ][:60],
        ),
        DatasetInfo(
            id=ArchivosDataset.ID,
            name="SECOP – Documentos",
            fields=[
                FieldInfo(name=v, type=_guess_type(v))
                for k, v in vars(ArchivosDataset).items()
                if isinstance(v, str) and not k.startswith("_") and k.isupper() and k != "ID"
            ],
        ),
    ]


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(current_user: dict = Depends(get_current_user)):
    user_sub = _user_sub(current_user)
    return [ConversationSummary(**c) for c in persistence.list_conversations(user_sub)]


@router.get("/conversations/{conv_id}", response_model=ConversationDetail)
def get_conversation(conv_id: str, current_user: dict = Depends(get_current_user)):
    user_sub = _user_sub(current_user)
    conv = persistence.get_conversation(conv_id, user_sub)
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no encontrada")
    return ConversationDetail(
        conversation_id=conv["_id"],
        title=conv.get("title", ""),
        messages=conv.get("messages", []),
        created_at=_to_iso(conv.get("created_at")),
        updated_at=_to_iso(conv.get("updated_at")),
    )


def _guess_type(field: str) -> str:
    f = field.lower()
    if "valor" in f or "saldo" in f or "tamanno" in f or "dias" in f:
        return "number"
    if "fecha" in f:
        return "datetime"
    if f.startswith("url") or f.endswith("url"):
        return "url"
    return "string"


def _to_iso(dt) -> str | None:
    if dt is None:
        return None
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    return str(dt)
