"""
Runs tab component.
Shows session history of decision evaluations and model benchmarks.
"""
from typing import List, Dict, Any
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify
from src.config import get_default_threshold


def create_runs_tab(run_history: List[Dict[str, Any]]):
    if not run_history:
        return html.Div(
            style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
                "justifyContent": "center",
                "height": "60vh",
                "color": "#64748b",
            },
            children=[
                DashIconify(icon="tabler:history", width=42, color="#334155"),
                dmc.Text("No execution logs in this session.", size="sm", fw=500, c="#94a3b8", mt="md"),
                dmc.Text("Trigger runs in the 'Compare' or 'Inference' tabs to audit model performance here.", size="xs", c="dimmed", mt=4),
            ]
        )

    default_thresh = int(get_default_threshold())
    rows = []
    for r in reversed(run_history):
        models_str = ", ".join(r.get("models", []))
        passed = r.get("overall_passed", False)
        rows.append([
            r.get("timestamp", "-"),
            r.get("doc_title", "Custom Process Log")[:45],
            models_str,
            f"{r.get('threshold', default_thresh)}%",
            "APPROVED" if passed else "QUALITY HOLD",
            f"{r.get('avg_latency_ms', 0):.0f} ms",
        ])

    return html.Div(
        style={"padding": "16px", "maxWidth": "1250px", "margin": "0 auto"},
        children=[
            dmc.Paper(
                p="md",
                radius="xs",
                className="panel-card",
                children=[
                    dmc.Group(
                        justify="space-between",
                        children=[
                            dmc.Group([
                                DashIconify(icon="tabler:history", width=18, color="#94a3b8"),
                                dmc.Text("Decision Audit Log", fw=700, size="sm", c="white"),
                            ], gap=8),
                            dmc.Badge(f"{len(run_history)} Records", variant="outline", color="gray", size="xs"),
                        ],
                        mb="md",
                    ),
                    dmc.Table(
                        striped=True,
                        highlightOnHover=True,
                        data={
                            "head": ["Timestamp", "Process Target", "Evaluated Models", "Threshold", "Gate Outcome", "Latency"],
                            "body": rows,
                        },
                    ),
                ]
            )
        ]
    )
