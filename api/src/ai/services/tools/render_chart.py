"""Tool: render_chart · genera un spec Chart.js que el frontend renderiza."""

import uuid
from typing import Any

PALETTE_BAR = [
    "rgba(34, 197, 94, 0.7)",
    "rgba(59, 130, 246, 0.7)",
    "rgba(168, 85, 247, 0.7)",
    "rgba(239, 68, 68, 0.7)",
    "rgba(245, 158, 11, 0.7)",
]

PALETTE_DOUGHNUT = [
    "#22c55e", "#3b82f6", "#a855f7", "#ef4444", "#f59e0b",
    "#06b6d4", "#ec4899",
]


def run(args: dict[str, Any]) -> dict:
    chart_type = args.get("chart_type")
    labels = args.get("labels", [])
    values = args.get("values", [])
    dataset_label = args.get("dataset_label", "Total")
    title = args.get("title", "")

    if chart_type not in {"bar", "line", "doughnut", "pie"}:
        return {"error": f"chart_type '{chart_type}' no soportado"}
    if len(labels) != len(values):
        return {"error": f"labels ({len(labels)}) y values ({len(values)}) no coinciden"}
    if not labels:
        return {"error": "no hay datos para graficar"}

    if chart_type == "bar":
        spec = {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": dataset_label,
                    "data": values,
                    "backgroundColor": PALETTE_BAR[0],
                    "borderColor": PALETTE_BAR[0].replace("0.7", "1"),
                    "borderWidth": 1,
                }],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {"title": {"display": bool(title), "text": title}},
            },
        }
    elif chart_type == "line":
        spec = {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": dataset_label,
                    "data": values,
                    "borderColor": "#3b82f6",
                    "backgroundColor": "rgba(59, 130, 246, 0.2)",
                    "fill": True,
                    "tension": 0.3,
                }],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {"title": {"display": bool(title), "text": title}},
            },
        }
    else:  # doughnut / pie
        spec = {
            "type": chart_type,
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": PALETTE_DOUGHNUT[: len(labels)],
                }],
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {"title": {"display": bool(title), "text": title}},
            },
        }

    chart_id = f"chart_{uuid.uuid4().hex[:8]}"
    return {
        "chart_id": chart_id,
        "title": title,
        "chart_js_spec": spec,
    }
