"""
Batch evaluation and benchmark tab component.
Displays a static shell on load; benchmark runs only when the user clicks 'Run Benchmark'.
"""
from typing import List, Optional
import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from src.config import get_available_models, get_default_model, get_default_threshold


def create_batch_tab(threshold_percent: Optional[float] = None, models: Optional[List[str]] = None):
    """Renders the Batch tab shell — results are populated via callback on demand."""
    if threshold_percent is None:
        threshold_percent = get_default_threshold()

    avail = get_available_models()
    if not models:
        models = avail[:2] if len(avail) >= 2 else (avail if avail else [get_default_model()])

    model_options = [{"value": m, "label": m} for m in avail]
    m1 = models[0] if models else get_default_model()
    m2 = models[1] if len(models) > 1 else m1

    return html.Div(
        style={"padding": "16px", "maxWidth": "1250px", "margin": "0 auto", "display": "flex", "flexDirection": "column", "gap": "16px"},
        children=[
            # Control bar
            dmc.Paper(
                p="md",
                radius="xs",
                className="panel-card",
                children=[
                    dmc.Group(
                        justify="space-between",
                        children=[
                            dmc.Group([
                                dmc.Text("MODEL A:", size="xs", fw=700, c="#64748b"),
                                dmc.Select(
                                    id="batch-model-a-select",
                                    data=model_options,
                                    value=m1,
                                    size="xs",
                                    style={"width": "160px"},
                                ),
                                dmc.Text("vs", size="xs", c="dimmed"),
                                dmc.Text("MODEL B:", size="xs", fw=700, c="#64748b"),
                                dmc.Select(
                                    id="batch-model-b-select",
                                    data=model_options,
                                    value=m2,
                                    size="xs",
                                    style={"width": "160px"},
                                ),
                                html.Div(
                                    className="threshold-container",
                                    children=[
                                        dmc.Text(
                                            id="batch-threshold-label",
                                            children=f"Threshold: ≥ {int(threshold_percent)}%",
                                            size="xs", c="#94a3b8",
                                        ),
                                        dmc.Slider(
                                            id="batch-threshold-slider",
                                            value=int(threshold_percent),
                                            min=50, max=99, step=1,
                                            size="xs", color="gray",
                                            showLabelOnHover=False,
                                            style={"width": "80px"},
                                        ),
                                    ],
                                ),
                            ], gap="md"),
                            dmc.Button(
                                "Run Benchmark",
                                id="run-batch-btn",
                                leftSection=DashIconify(icon="tabler:player-play-filled", width=13, color="#94a3b8"),
                                size="sm",
                                color="gray",
                                variant="filled",
                                style={"backgroundColor": "#1e2430", "color": "#f8fafc", "fontWeight": 600},
                            ),
                        ]
                    )
                ]
            ),

            # Results area (populated by callback)
            html.Div(id="batch-results-area", children=[
                dmc.Paper(
                    p="xl",
                    radius="xs",
                    className="panel-card",
                    children=[
                        dmc.Stack(
                            align="center",
                            gap="xs",
                            children=[
                                DashIconify(icon="tabler:chart-dots", width=36, color="#334155"),
                                dmc.Text("Select models and click Run Benchmark", size="sm", c="dimmed"),
                                dmc.Text("Results will appear here", size="xs", c="#475569"),
                            ]
                        )
                    ]
                )
            ]),
        ]
    )


def render_batch_results(batch_data, threshold_percent, models):
    """Renders the charts and table after evaluation completes."""
    from src.benchmark import create_sensitivity_figure

    m1 = models[0]
    m2 = models[1] if len(models) > 1 else models[0]

    fig = create_sensitivity_figure(batch_data["sweep_data"], threshold_percent)

    table_body = []
    for i, item in enumerate(batch_data["results_by_model"][m1]):
        m2_item = batch_data["results_by_model"][m2][i] if m2 in batch_data["results_by_model"] else item
        match = (item["passed"] == m2_item["passed"])
        table_body.append([
            item["doc_title"],
            item["category"],
            "APPROVED" if item["passed"] else "QUALITY HOLD",
            "APPROVED" if m2_item["passed"] else "QUALITY HOLD",
            "✓ CONSENSUS" if match else "✗ DIVERGENCE",
        ])

    return [
        # Metrics
        dmc.SimpleGrid(
            cols=3,
            spacing="md",
            children=[
                dmc.Paper(p="sm", radius="xs", className="panel-card", children=[
                    dmc.Group([
                        DashIconify(icon="tabler:database", width=22, color="#94a3b8"),
                        dmc.Stack([
                            dmc.Text("Manufacturing Process Logs", size="xs", c="dimmed"),
                            dmc.Text(str(batch_data["total_documents"]), fw=700, size="lg", c="white"),
                        ], gap=0),
                    ], gap="md"),
                ]),
                dmc.Paper(p="sm", radius="xs", className="panel-card", children=[
                    dmc.Group([
                        DashIconify(icon="tabler:scale", width=22, color="#94a3b8"),
                        dmc.Stack([
                            dmc.Text("Model Consensus", size="xs", c="dimmed"),
                            dmc.Text(
                                f"{sum(1 for r in table_body if '✓' in r[4])}/{len(table_body)} Agreement",
                                fw=700, size="lg", c="#22c55e",
                            ),
                        ], gap=0),
                    ], gap="md"),
                ]),
                dmc.Paper(p="sm", radius="xs", className="panel-card", children=[
                    dmc.Group([
                        DashIconify(icon="tabler:bolt", width=22, color="#94a3b8"),
                        dmc.Stack([
                            dmc.Text("Benchmarked Models", size="xs", c="dimmed"),
                            dmc.Text(
                                " vs ".join(models), fw=700, size="xs", c="white",
                                style={"fontFamily": "'JetBrains Mono', monospace"},
                            ),
                        ], gap=0),
                    ], gap="md"),
                ]),
            ]
        ),
        # Chart + Table
        dmc.Grid(
            gutter="md",
            children=[
                dmc.GridCol(span=7, children=[
                    dmc.Paper(p="md", radius="xs", className="panel-card", children=[
                        dmc.Group(justify="space-between", children=[
                            dmc.Text("Quality Gate Threshold vs Auto-Clearance Rate", fw=600, size="xs", c="white"),
                            dmc.Badge("Sensitivity Sweep", size="xs", variant="outline", color="gray"),
                        ], mb="sm"),
                        dcc.Graph(
                            id="sensitivity-graph",
                            figure=fig,
                            config={"displayModeBar": False},
                            style={"height": "320px"},
                        ),
                    ])
                ]),
                dmc.GridCol(span=5, children=[
                    dmc.Paper(p="md", radius="xs", className="panel-card", style={"height": "100%"}, children=[
                        dmc.Text("Batch Benchmark Decisions", fw=600, size="xs", c="white", mb="sm"),
                        dmc.Table(
                            striped=True,
                            highlightOnHover=True,
                            data={
                                "head": ["Process Run", "Sector", m1, m2, "Consensus"],
                                "body": table_body,
                            },
                        ),
                    ])
                ]),
            ]
        ),
    ]
