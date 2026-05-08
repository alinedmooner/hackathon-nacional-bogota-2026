"""Schemas Pydantic para el agente IA."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class ToolCallLog(BaseModel):
    tool: str
    input: dict[str, Any] = {}
    result_summary: str
    soql_url: Optional[str] = None


class ChartItem(BaseModel):
    id: str
    title: str = ""
    chart_js_spec: dict[str, Any]


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    tool_calls: list[ToolCallLog] = []
    charts: list[ChartItem] = []
    usage: Usage = Usage()
    latency_ms: int = 0


class FieldInfo(BaseModel):
    name: str
    type: str = "string"


class DatasetInfo(BaseModel):
    id: str
    name: str
    fields: list[FieldInfo]


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConversationDetail(BaseModel):
    conversation_id: str
    title: str
    messages: list[dict[str, Any]]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
