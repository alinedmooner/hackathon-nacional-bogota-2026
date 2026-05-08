"""Orquestador del agente · loop tool-use no-streaming."""

import json
import logging
import time
from typing import Any

from .client import get_client, get_model
from .prompts import build_system_prompt
from .tools.registry import TOOLS_OPENAI, run_tool

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 6


def chat(
    user_message: str,
    history: list[dict] | None = None,
    temperature: float = 0.1,
) -> dict:
    """Ejecuta el loop de tool-use y devuelve la respuesta final.

    Returns:
        {
            "answer": str,
            "tool_calls": [...],
            "charts": [...],
            "messages": [...],          # historial completo actualizado
            "usage": {...},
            "latency_ms": int,
        }
    """
    client = get_client()
    model = get_model()

    messages: list[dict] = [{"role": "system", "content": build_system_prompt()}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    tool_calls_log: list[dict] = []
    charts: list[dict] = []
    total_input_tokens = 0
    total_output_tokens = 0
    start = time.time()

    for iteration in range(MAX_TOOL_ITERATIONS):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS_OPENAI,
            tool_choice="auto",
            temperature=temperature,
        )
        usage = resp.usage
        if usage:
            total_input_tokens += usage.prompt_tokens
            total_output_tokens += usage.completion_tokens

        msg = resp.choices[0].message

        # Si no hay tool_calls, terminamos
        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or ""})
            break

        # Tiene tool calls: registrar el mensaje del asistente
        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        }
        messages.append(assistant_msg)

        # Ejecutar cada tool y devolver su resultado
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError as e:
                tool_args = {}
                tool_result = {"error": f"argumentos JSON inválidos: {e}"}
            else:
                logger.info("tool_call %s args=%s", tool_name, tool_args)
                tool_result = run_tool(tool_name, tool_args)

            # Si la tool fue render_chart, capturar el spec para el response
            if tool_name == "render_chart" and "chart_js_spec" in tool_result:
                charts.append({
                    "id": tool_result.get("chart_id"),
                    "title": tool_result.get("title", ""),
                    "chart_js_spec": tool_result["chart_js_spec"],
                })

            tool_calls_log.append({
                "tool": tool_name,
                "input": tool_args,
                "result_summary": _summarize(tool_result),
                "soql_url": tool_result.get("soql_url"),
            })

            # Compactar el resultado para no inflar tokens
            compact_result = _compact_for_llm(tool_name, tool_result)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(compact_result, ensure_ascii=False, default=str),
            })

    else:
        # Salimos del for sin break: hit max iterations
        messages.append({
            "role": "assistant",
            "content": "(El agente alcanzó el máximo de iteraciones de tools sin terminar.)",
        })

    final_msg = messages[-1]
    answer = final_msg.get("content") or ""

    return {
        "answer": answer,
        "tool_calls": tool_calls_log,
        "charts": charts,
        "messages": messages,
        "usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
        },
        "latency_ms": int((time.time() - start) * 1000),
    }


def _summarize(result: dict) -> str:
    if "error" in result:
        return f"error: {result['error']}"
    if "row_count" in result:
        return f"{result['row_count']} filas"
    if "found" in result:
        return "encontrado" if result["found"] else "no encontrado"
    if "documentos_count" in result:
        return f"contrato + {result['documentos_count']} documentos"
    if "chart_id" in result:
        return f"chart {result['chart_id']}"
    return "ok"


def _compact_for_llm(tool_name: str, result: dict) -> dict:
    """Reduce el tamaño del resultado para no gastar tokens en payloads enormes."""
    if "error" in result:
        return result
    if tool_name == "render_chart":
        # No reenviar el spec completo al modelo, sólo confirmar
        return {"chart_id": result.get("chart_id"), "rendered": True}
    if "rows" in result:
        rows = result["rows"]
        # Limitar a 30 filas y truncar campos largos
        compact_rows = [_truncate_strings(r) for r in rows[:30]]
        return {
            "row_count": result.get("row_count"),
            "rows": compact_rows,
            "truncated": len(rows) > 30,
        }
    return result


def _truncate_strings(row: dict, max_len: int = 200) -> dict:
    out = {}
    for k, v in row.items():
        if isinstance(v, str) and len(v) > max_len:
            out[k] = v[:max_len] + "…"
        else:
            out[k] = v
    return out
