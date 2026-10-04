"""
Dedicated Single Model Inference component.
Runs a selected Ollama model against an uploaded or preset dataset of process logs,
evaluating the criteria checklist across all records and reporting performance.
"""
from typing import List, Dict, Any
import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
from src.presets import PRESET_SNIPPETS, DEFAULT_MANUFACTURING_QUESTIONS
from src.config import get_available_models, get_default_model, get_default_threshold


def get_dataset_results_headers(questions: List[Any] = None) -> List[str]:
    """Generates dynamic table headers based on the active questions schema."""
    headers = ["Record ID"]
    if questions:
        for q in questions:
            name = q.name if hasattr(q, "name") else q.get("name", "Gate")
            headers.append(f"Gate: {name}")
    else:
        headers.extend(["Yield Target", "Line Stoppage", "Param Drift", "Primary Defect Mode"])
    headers.extend(["Gate Decision", "Latency"])
    return headers


def render_results_table_rows(evaluation_results: List[Dict[str, Any]], questions: List[Any] = None):
    """Renders table rows for inference results based on the active questions schema."""
    headers = get_dataset_results_headers(questions)
    if not evaluation_results:
        placeholder_row = ["-" for _ in range(len(headers))]
        mid = max(1, len(headers) // 2)
        placeholder_row[mid] = "Click 'Run Model on Dataset' to begin evaluation"
        return [placeholder_row]

    rows = []
    for i, res in enumerate(evaluation_results):
        eval_map = res.get("eval_map", {})
        rec_id = res.get("record_id", f"REC_{i+1:03d}")
        row = [rec_id]
        if questions:
            for q in questions:
                q_name = q.name if hasattr(q, "name") else q.get("name", "")
                q_type = q.type if hasattr(q, "type") else q.get("type", "bool")
                gate_eval = eval_map.get(q_name, {})
                if q_type == "choice":
                    val_str = gate_eval.get("selected_choice", "-")
                else:
                    passed = gate_eval.get("passed", False)
                    p_val = gate_eval.get("p_true", 0.0)
                    val_str = f"{'Pass' if passed else 'Hold'} ({p_val*100:.0f}%)"
                row.append(val_str)
        else:
            yield_gate = eval_map.get("yield_target_met", {})
            stoppage_gate = eval_map.get("line_stoppage_flag", {})
            drift_gate = eval_map.get("parameter_drift", {})
            defect_gate = eval_map.get("primary_defect_type", {})
            p_yield = yield_gate.get("p_true", 0.0) * 100
            yield_str = f"P(true) = {p_yield:.0f}%"
            stoppage_str = "0 min (Pass)" if stoppage_gate.get("passed", False) else "Stoppage (Fail)"
            drift_str = "Within Spec" if drift_gate.get("passed", False) else "Excursion (Drift)"
            defect_str = defect_gate.get("selected_choice", "none")
            row.extend([yield_str, stoppage_str, drift_str, defect_str])

        decision_str = "APPROVED" if res.get("overall_passed") else "QUALITY HOLD"
        row.append(decision_str)
        row.append(f"{res.get('latency_ms', 0):.0f} ms")
        rows.append(row)
    return rows


def create_inference(
    installed_models: List[Dict[str, Any]],
    selected_model: str = None,
    dataset_records: List[Dict[str, Any]] = None,
    evaluation_results: List[Dict[str, Any]] = None,
    questions: List[Any] = None,
):
    active_questions = questions if questions is not None else DEFAULT_MANUFACTURING_QUESTIONS
    # Only list models defined and maintained in config.yaml
    config_models = get_available_models()
    def_model = get_default_model()
    if selected_model is None:
        selected_model = def_model if def_model in config_models else (config_models[0] if config_models else def_model)
    model_options = [{"value": name, "label": name} for name in config_models]
    if not any(m["value"] == selected_model for m in model_options) and model_options:
        selected_model = model_options[0]["value"]

    records = dataset_records or [
        {"id": f"REC_{i+1:03d}", "title": s.title, "category": s.category, "text": s.content}
        for i, s in enumerate(PRESET_SNIPPETS)
    ]

    total_count = len(records)
    has_results = bool(evaluation_results)
    passed_count = sum(1 for r in (evaluation_results or []) if r.get("overall_passed"))
    pass_rate = round((passed_count / total_count * 100), 1) if (has_results and total_count) else 0.0
    avg_latency = round(sum(r.get("latency_ms", 0) for r in (evaluation_results or [])) / max(1, len(evaluation_results or [])), 1)

    table_rows = render_results_table_rows(evaluation_results, questions=active_questions)

    return html.Div(
        className="inference-container",
        children=[
            # Top Control Bar
            dmc.Paper(
                p="md",
                radius="sm",
                className="panel-card",
                children=[
                    dmc.Group(
                        justify="space-between",
                        children=[
                            # Model selection
                            dmc.Group([
                                dmc.Text("TARGET MODEL:", size="xs", fw=700, c="#64748b"),
                                dmc.Select(
                                    id="inference-model-select",
                                    data=model_options,
                                    value=selected_model,
                                    allowDeselect=False,
                                    size="xs",
                                    style={"width": "190px"},
                                ),
                            ], gap="md"),

                            # Threshold & Run action
                            dmc.Group([
                                html.Div(
                                    className="threshold-container",
                                    children=[
                                        dmc.Text(id="inference-threshold-label", children=f"Gate Threshold: ≥ {int(get_default_threshold())}%", size="xs", c="#94a3b8"),
                                        html.Div(
                                            style={"width": "90px"},
                                            children=[
                                                dmc.Slider(
                                                    id="inference-threshold-slider",
                                                    value=int(get_default_threshold()),
                                                    min=50,
                                                    max=99,
                                                    step=1,
                                                    size="xs",
                                                    color="gray",
                                                    showLabelOnHover=False,
                                                )
                                            ]
                                        ),
                                    ]
                                ),
                                dmc.Button(
                                    id="run-inference-btn",
                                    children="Run Model on Dataset",
                                    leftSection=DashIconify(icon="tabler:player-play-filled", width=14, color="#94a3b8"),
                                    size="sm",
                                    color="gray",
                                    variant="filled",
                                    style={"backgroundColor": "#1e2430", "color": "#f8fafc", "fontWeight": 600},
                                ),
                            ], gap="md"),
                        ]
                    )
                ]
            ),

            # Metrics row
            dmc.SimpleGrid(
                cols=4,
                spacing="md",
                children=[
                    dmc.Paper(
                        p="sm",
                        radius="sm",
                        className="panel-card",
                        children=[
                            dmc.Text("DATASET SIZE", size="xs", c="#64748b", fw=600),
                            dmc.Text(id="inference-total-count", children=f"{total_count} Process Logs", fw=700, size="lg", c="#f8fafc"),
                        ]
                    ),
                    dmc.Paper(
                        p="sm",
                        radius="sm",
                        className="panel-card",
                        children=[
                            dmc.Text("LOT PASS RATE", size="xs", c="#64748b", fw=600),
                            dmc.Text(
                                id="inference-pass-rate-text",
                                children=f"{pass_rate}%" if has_results else "--",
                                fw=700,
                                size="lg",
                                c="#22c55e" if pass_rate >= 80 else "#ef4444",
                            ),
                        ]
                    ),
                    dmc.Paper(
                        p="sm",
                        radius="sm",
                        className="panel-card",
                        children=[
                            dmc.Text("EXCURSION / HOLD COUNT", size="xs", c="#64748b", fw=600),
                            dmc.Text(
                                id="inference-hold-count-text",
                                children=f"{total_count - passed_count}" if has_results else "--",
                                fw=700,
                                size="lg",
                                c="#f97316" if (total_count - passed_count) > 0 else "#94a3b8",
                            ),
                        ]
                    ),
                    dmc.Paper(
                        p="sm",
                        radius="sm",
                        className="panel-card",
                        children=[
                            dmc.Text("AVG INFERENCE SPEED", size="xs", c="#64748b", fw=600),
                            dmc.Text(
                                id="inference-speed-text",
                                children=f"{avg_latency:.0f} ms / log" if has_results else "--",
                                fw=700,
                                size="lg",
                                c="#94a3b8",
                            ),
                        ]
                    ),
                ]
            ),

            # Dataset Upload & Checklist Grid
            dmc.Grid(
                gutter="md",
                children=[
                    # Left: Dataset source & preview
                    dmc.GridCol(
                        span=7,
                        children=[
                            dmc.Paper(
                                p="md",
                                radius="sm",
                                className="panel-card",
                                children=[
                                    dmc.Group(
                                        justify="space-between",
                                        children=[
                                            dmc.Group([
                                                dmc.Text("UPLOADED PROCESS DATASET", fw=600, size="xs", c="#cbd5e1"),
                                                dmc.Badge(id="inference-badge-count", children=f"{len(records)} Items Loaded", size="xs", variant="outline", color="gray"),
                                            ], gap=8),
                                            dmc.Group([
                                                dcc.Upload(
                                                    id="upload-dataset-file",
                                                    children=dmc.Button(
                                                        "Upload File (CSV/JSON/TXT)",
                                                        leftSection=DashIconify(icon="tabler:upload", width=14, color="#94a3b8"),
                                                        variant="subtle",
                                                        color="gray",
                                                        size="xs",
                                                    ),
                                                ),
                                                dmc.Button(
                                                    "Load Sample Set",
                                                    id="load-sample-dataset-btn",
                                                    variant="subtle",
                                                    color="gray",
                                                    size="xs",
                                                ),
                                                dmc.Tooltip(
                                                    label="Load clean reference template schema and records",
                                                    children=dmc.Button(
                                                        "Load Template",
                                                        id="load-template-dataset-btn",
                                                        variant="subtle",
                                                        color="gray",
                                                        size="xs",
                                                    ),
                                                ),
                                            ], gap=6),
                                        ],
                                        mb="sm",
                                    ),
                                    # Dataset records preview table
                                    html.Div(
                                        id="inference-preview-table-container",
                                        children=[
                                            dmc.Table(
                                                striped=True,
                                                highlightOnHover=True,
                                                data={
                                                    "head": ["Record ID", "Process Line / Context", "Snippet Preview"],
                                                    "body": [
                                                        [
                                                            r["id"],
                                                            r["title"][:38] + "...",
                                                            r["text"][:65] + "...",
                                                        ]
                                                        for r in records[:8]
                                                    ]
                                                },
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ]
                    ),

                    # Right: State / Questions checklist
                    dmc.GridCol(
                        span=5,
                        children=[
                            dmc.Paper(
                                p="md",
                                radius="sm",
                                className="panel-card",
                                style={"height": "100%"},
                                children=[
                                    dmc.Group(
                                        justify="space-between",
                                        children=[
                                            dmc.Text("EVALUATION CHECKLIST (STATE TO QUERY)", fw=600, size="xs", c="#cbd5e1"),
                                            dmc.Badge(f"{len(active_questions)} Gates Active", size="xs", variant="light", color="gray"),
                                        ],
                                        mb="sm",
                                    ),
                                    dmc.Stack(
                                        gap="xs",
                                        children=[
                                            dmc.Paper(
                                                p="xs",
                                                radius="xs",
                                                style={"background": "rgba(255,255,255,0.02)", "border": "1px solid #1f2430"},
                                                children=[
                                                    dmc.Group([
                                                        dmc.Badge(
                                                            "REQ" if (getattr(q, "required", True) if hasattr(q, "required") else q.get("required", True)) else "OPT",
                                                            color="red" if (getattr(q, "required", True) if hasattr(q, "required") else q.get("required", True)) else "gray",
                                                            size="xs",
                                                            variant="light"
                                                        ),
                                                        dmc.Badge(
                                                            str(getattr(q, "type", "noul")).upper(),
                                                            color="blue" if str(getattr(q, "type", "noul")).lower() == "choice" else "teal",
                                                            size="xs",
                                                            variant="outline",
                                                        ),
                                                        dmc.Text(
                                                            getattr(q, "name", "") if hasattr(q, "name") else q.get("name", ""),
                                                            fw=600,
                                                            size="xs",
                                                            style={"fontFamily": "'JetBrains Mono', monospace"}
                                                        ),
                                                    ], gap=6),
                                                    dmc.Text(
                                                        getattr(q, "instructions", getattr(q, "prompt", "")) if hasattr(q, "instructions") else (q.get("instructions") or q.get("prompt", "")),
                                                        size="xs",
                                                        c="#94a3b8",
                                                        mt=2
                                                    ),
                                                    *(
                                                        [
                                                            dmc.Group(
                                                                [
                                                                    dmc.Badge(
                                                                        c_opt,
                                                                        size="xs",
                                                                        variant="outline",
                                                                        color="gray",
                                                                        style={"fontSize": "10px", "textTransform": "none"}
                                                                    )
                                                                    for c_opt in (getattr(q, "choices", []) if hasattr(q, "choices") else q.get("choices", []))[:3]
                                                                ],
                                                                gap=4,
                                                                mt=4,
                                                            )
                                                        ]
                                                        if (getattr(q, "choices", []) if hasattr(q, "choices") else q.get("choices", []))
                                                        else []
                                                    )
                                                ]
                                            )
                                            for q in active_questions
                                        ]
                                    ),
                                ]
                            )
                        ]
                    ),
                ]
            ),

            # Results Table (when evaluated)
            dmc.Paper(
                p="md",
                radius="sm",
                className="panel-card",
                children=[
                    dmc.Group(
                        justify="space-between",
                        children=[
                            dmc.Group([
                                dmc.Text("EVALUATION LOG & DECISION TRACE", fw=600, size="xs", c="#cbd5e1"),
                                dmc.Badge(
                                    id="inference-eval-status-badge",
                                    children=f"Status: {len(evaluation_results)} Evaluated" if has_results else "Status: Ready to Run",
                                    size="xs",
                                    variant="dot",
                                    color="green" if has_results else "gray",
                                ),
                            ], gap=8),
                            dmc.Group([
                                dmc.Button(
                                    "Download Native JSON (types.py Schema)",
                                    id="export-native-json-btn",
                                    leftSection=DashIconify(icon="tabler:braces", width=14, color="#94a3b8"),
                                    size="xs",
                                    variant="subtle",
                                    color="gray",
                                    disabled=not has_results,
                                ),
                                dcc.Download(id="download-native-json"),
                                dmc.Button(
                                    "Download Original + States (CSV)",
                                    id="export-decisions-csv-btn",
                                    leftSection=DashIconify(icon="tabler:table", width=14, color="#94a3b8"),
                                    size="xs",
                                    variant="subtle",
                                    color="gray",
                                    disabled=not has_results,
                                ),
                                dcc.Download(id="download-decisions-csv"),
                            ], gap=4),
                        ],
                        mb="sm",
                    ),
                    html.Div(
                        id="inference-results-table-container",
                        children=[
                            dmc.Table(
                                striped=True,
                                highlightOnHover=True,
                                data={
                                    "head": get_dataset_results_headers(active_questions),
                                    "body": table_rows,
                                },
                            )
                        ]
                    ),
                ]
            ),
        ]
    )
