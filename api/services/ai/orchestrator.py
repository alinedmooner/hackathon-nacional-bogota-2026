"""Orquestador del agente · loop tool-use (blocking + streaming SSE)."""

import json
import logging
import time
from typing import Any, Generator

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


def chat_stream(
    user_message: str,
    history: list[dict] | None = None,
    temperature: float = 0.1,
) -> Generator[dict, None, None]:
    """Variante streaming: yield dicts de eventos SSE.

    Tipos de evento:
      thinking   → {type, iteration}
      tool_call  → {type, tool, args}
      tool_result→ {type, tool, summary}
      chart      → {type, chart:{id,title,chart_js_spec}}
      answer     → {type, text}
      done       → {type, tool_calls, charts, messages, usage, latency_ms}
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
    answer = ""

    for iteration in range(MAX_TOOL_ITERATIONS):
        yield {"type": "thinking", "iteration": iteration + 1}

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

        if not msg.tool_calls:
            answer = msg.content or ""
            messages.append({"role": "assistant", "content": answer})
            yield {"type": "answer", "text": answer}
            break

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

        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError as e:
                tool_args = {}
                tool_result = {"error": f"argumentos JSON inválidos: {e}"}
            else:
                yield {"type": "tool_call", "tool": tool_name, "args": tool_args}
                logger.info("stream tool_call %s args=%s", tool_name, tool_args)
                tool_result = run_tool(tool_name, tool_args)

            summary = _summarize(tool_result)
            yield {"type": "tool_result", "tool": tool_name, "summary": summary}

            if tool_name == "render_chart" and "chart_js_spec" in tool_result:
                chart_item = {
                    "id": tool_result.get("chart_id"),
                    "title": tool_result.get("title", ""),
                    "chart_js_spec": tool_result["chart_js_spec"],
                }
                charts.append(chart_item)
                yield {"type": "chart", "chart": chart_item}

            tool_calls_log.append({
                "tool": tool_name,
                "input": tool_args,
                "result_summary": summary,
                "soql_url": tool_result.get("soql_url"),
            })

            compact_result = _compact_for_llm(tool_name, tool_result)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(compact_result, ensure_ascii=False, default=str),
            })
    else:
        answer = "(El agente alcanzó el máximo de iteraciones de tools sin terminar.)"
        messages.append({"role": "assistant", "content": answer})
        yield {"type": "answer", "text": answer}

    yield {
        "type": "done",
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
    # Veridia tools
    if "resumen" in result and "tipo_alerta" in result:
        r = result["resumen"]
        n = r.get("total_contratos") or r.get("total_contratos_posteriores", 0)
        return f"{result['tipo_alerta']}: {n} contratos detectados"
    if "nivel_alerta" in result:
        return f"perfil nivel={result['nivel_alerta']}"
    if "sancionados_activos" in result:
        n = result["sancionados_activos"].get("total_personas", 0)
        return f"resumen global: {n} sancionados activos"
    if "tipo_alerta" in result and result.get("tipo_alerta") == "ALERTA_AMARILLA":
        r = result.get("resumen", {})
        return f"puerta giratoria: {r.get('total_personas', 0)} personas, {r.get('total_contratos', 0)} contratos"
    return "ok"


def _compact_for_llm(tool_name: str, result: dict) -> dict:
    """Reduce el tamaño del resultado para no gastar tokens en payloads enormes."""
    if "error" in result:
        return result
    if tool_name == "render_chart":
        return {"chart_id": result.get("chart_id"), "rendered": True}
    if "rows" in result:
        rows = result["rows"]
        compact_rows = [_truncate_strings(r) for r in rows[:30]]
        return {
            "row_count": result.get("row_count"),
            "rows": compact_rows,
            "truncated": len(rows) > 30,
        }
    # Resultados de tools Veridia: compactar lista hallazgos
    if tool_name in ("check_active_sanctions", "check_fines", "check_revolving_door"):
        hallazgos = result.get("hallazgos", [])
        return {
            "tipo_alerta": result.get("tipo_alerta"),
            "resumen": result.get("resumen"),
            "fuente": result.get("fuente"),
            "hallazgos": [_truncate_strings(h) for h in hallazgos[:15]],
            "truncated": len(hallazgos) > 15,
        }
    if tool_name == "get_person_profile":
        # Devolver perfil completo pero truncar listas largas
        r = dict(result)
        if "secop_resumen" in r:
            contratos = r["secop_resumen"].get("ultimos_contratos", [])
            r["secop_resumen"]["ultimos_contratos"] = contratos[:5]
        return r
    return result


def _truncate_strings(row: dict, max_len: int = 200) -> dict:
    out = {}
    for k, v in row.items():
        if isinstance(v, str) and len(v) > max_len:
            out[k] = v[:max_len] + "…"
        else:
            out[k] = v
    return out
