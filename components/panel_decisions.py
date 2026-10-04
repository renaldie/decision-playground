"""
Decisions panel component (Right Column).
Displays the automated process verdict, side-by-side model predictions for up to 4 models,
probability meters with threshold markers, extracted evidence, ground truth comparison badges,
and the engineering action dispatch.
Includes expandable/collapsible card controls to occupy full screen or hide to side ribbon.
"""
from typing import List, Dict, Any, Optional
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify
from src.types import ModelResult, QuestionEvaluation


def render_empty_decisions():
    """Initial placeholder before run."""
    return html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "height": "70%",
            "color": "#64748b",
            "textAlign": "center",
        },
        children=[
            DashIconify(icon="tabler:cpu", width=42, color="#334155"),
            dmc.Text("Select a process snippet and press Run.", size="sm", fw=500, c="#94a3b8", mt="md"),
            dmc.Text("Evaluates side-by-side Ollama models against your manufacturing criteria.", size="xs", c="dimmed", mt=4),
        ]
    )


def check_is_match(ev: QuestionEvaluation, ground_truth: Optional[Any]) -> Optional[bool]:
    """Determines whether the model prediction matches the ground truth."""
    if ground_truth is None:
        return None
    q_type = str(getattr(ev, "question_type", "noul")).lower()
    if q_type in ("score", "ordinal"):
        try:
            gt_num = float(ground_truth)
            pred_score = float(ev.score if ev.score is not None else ev.p_true)
            return abs(pred_score - gt_num) < 0.6
        except (ValueError, TypeError):
            return False
    elif q_type in ("choice", "categorical"):
        gt_str = str(ground_truth).strip().lower()
        pred_choice = str(ev.selected_choice or "").strip().lower()
        return pred_choice == gt_str
    else:  # noul / bool
        if isinstance(ground_truth, str):
            gt_bool = ground_truth.strip().lower() in ("true", "1", "yes")
        else:
            gt_bool = bool(ground_truth)
        pred_bool = (float(ev.p_true) >= 0.5)
        return pred_bool == gt_bool


def render_evaluation_bar(
    ev: QuestionEvaluation,
    threshold_percent: float,
    model_color: str,
    ground_truth: Optional[Any] = None,
):
    """Renders a single question evaluation row comparing prediction directly against truth without PASS/FAIL status badges."""
    q_type = str(getattr(ev, "question_type", "noul")).lower()
    is_score = (q_type in ("score", "ordinal"))
    is_choice = (q_type in ("choice", "categorical"))

    is_match = check_is_match(ev, ground_truth)

    if is_score:
        score_val = float(ev.score if ev.score is not None else ev.p_true)
        p_pct = min(100.0, max(0.0, (score_val / 3.0) * 100.0))
        pred_label = f"Level {int(round(score_val))}"
        pred_detail = f"Score {score_val:.1f}"
        truth_label = f"Level {int(float(ground_truth))}" if ground_truth is not None else None
        metric_str = f"Rubric 0-3"
    elif is_choice:
        p_pct = float(ev.confidence) * 100.0
        choice_text = ev.selected_choice or "-"
        pred_label = choice_text
        pred_detail = f"{p_pct:.1f}%"
        truth_label = str(ground_truth) if ground_truth is not None else None
        metric_str = f"Choice: {choice_text}"
    else:  # noul / bool
        p_val = float(ev.p_true)
        pred_bool = (p_val >= 0.5)
        conf_pct = (p_val if pred_bool else (1.0 - p_val)) * 100.0
        pred_label = "True" if pred_bool else "False"
        pred_detail = f"{conf_pct:.1f}%"
        truth_label = str(bool(ground_truth)) if ground_truth is not None else None
        p_pct = p_val * 100.0
        metric_str = f"P(true) = {p_val * 100:.1f}%"

    # Color progress bar: teal if match, orange if diff, cyan if no truth
    if is_match is True:
        bar_color = "teal"
    elif is_match is False:
        bar_color = "orange"
    else:
        bar_color = "cyan"

    # Match badge
    match_badge = None
    if is_match is not None:
        if is_match:
            match_badge = dmc.Badge(
                "✓ Match",
                color="teal",
                variant="light",
                size="xs",
                style={"fontFamily": "'JetBrains Mono', monospace", "fontWeight": 700},
            )
        else:
            match_badge = dmc.Badge(
                "✗ Diff",
                color="orange",
                variant="light",
                size="xs",
                style={"fontFamily": "'JetBrains Mono', monospace", "fontWeight": 700},
            )

    # Prediction tag & Truth tag
    pred_tag = html.Span([
        html.Span("Pred: ", style={"color": "#94a3b8", "fontSize": "11px", "fontWeight": 500}),
        html.Span(
            pred_label,
            style={
                "color": "#34d399" if is_match is True else ("#fb923c" if is_match is False else "#38bdf8"),
                "fontWeight": 700,
                "fontSize": "11.5px",
                "fontFamily": "'JetBrains Mono', monospace",
            },
        ),
        html.Span(
            f" ({pred_detail})" if pred_detail else "",
            style={"color": "#64748b", "fontSize": "10.5px", "marginLeft": "3px", "fontFamily": "'JetBrains Mono', monospace"},
        ),
    ])

    truth_tag = None
    if truth_label is not None:
        truth_tag = html.Span([
            html.Span("Truth: ", style={"color": "#64748b", "fontSize": "11px", "fontWeight": 500}),
            html.Span(
                truth_label,
                style={
                    "color": "#e2e8f0",
                    "fontWeight": 600,
                    "fontSize": "11.5px",
                    "fontFamily": "'JetBrains Mono', monospace",
                    "backgroundColor": "rgba(255,255,255,0.06)",
                    "padding": "1px 6px",
                    "borderRadius": "3px",
                    "border": "1px solid rgba(255,255,255,0.1)",
                },
            ),
        ])

    return html.Div(
        style={
            "marginBottom": "10px",
            "padding": "8px 10px",
            "background": "rgba(255,255,255,0.015)",
            "borderRadius": "4px",
            "border": "1px solid rgba(255,255,255,0.03)",
        },
        children=[
            # Top row: Question Name + Match Badge (left), Pred + Truth (right)
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Group([
                        dmc.Text(
                            ev.question_name,
                            fw=600,
                            size="xs",
                            style={"fontFamily": "'JetBrains Mono', monospace", "color": "#f8fafc"},
                        ),
                        match_badge if match_badge else html.Span(),
                    ], gap=8),
                    dmc.Group([
                        pred_tag,
                        html.Span("•", style={"color": "#334155", "fontSize": "10px"}) if truth_tag else html.Span(),
                        truth_tag if truth_tag else html.Span(),
                    ], gap=8),
                ],
            ),
            # Probability / Confidence meter
            html.Div(
                className="prob-meter-container",
                style={"marginTop": "5px", "marginBottom": "4px"},
                children=[
                    dmc.Progress(value=p_pct, color=bar_color, size="sm", radius="xs"),
                ],
            ),
            # Bottom row: Evidence snippet & raw metric
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Text(
                        f"Evidence: \"{ev.evidence}\"" if ev.evidence else ev.rationale,
                        size="xs",
                        c="#94a3b8",
                        style={
                            "fontStyle": "italic",
                            "maxWidth": "80%",
                            "overflow": "hidden",
                            "textOverflow": "ellipsis",
                            "whiteSpace": "nowrap",
                        },
                    ),
                    dmc.Text(
                        metric_str,
                        size="xs",
                        c="#64748b",
                        fw=500,
                        style={"fontFamily": "'JetBrains Mono', monospace", "fontSize": "10.5px"},
                    ),
                ],
            ),
        ],
    )


def render_model_decision_card(
    model_result: ModelResult,
    threshold_percent: float,
    ground_truth_map: Optional[Dict[str, Any]] = None,
):
    """Renders a decisions card for a single model with prediction vs truth comparison."""
    total_count = len(model_result.evaluations)
    m_color = model_result.model_color

    eval_bars = [
        render_evaluation_bar(
            e,
            threshold_percent,
            m_color,
            ground_truth=(ground_truth_map.get(e.question_name) if ground_truth_map else None),
        )
        for e in model_result.evaluations
    ]

    # Header metric: Accuracy against ground truth if present, otherwise gate count
    if ground_truth_map:
        matches_count = sum(
            1 for e in model_result.evaluations
            if check_is_match(e, ground_truth_map.get(e.question_name))
        )
        acc_pct = (matches_count / total_count * 100) if total_count else 0
        header_metric = dmc.Badge(
            f"{matches_count}/{total_count} Matches ({acc_pct:.0f}%)",
            color="teal" if matches_count == total_count else ("green" if acc_pct >= 60 else "orange"),
            variant="light",
            size="xs",
            style={"fontFamily": "'JetBrains Mono', monospace", "fontWeight": 700},
        )
    else:
        header_metric = dmc.Text(f"{total_count} Gates Evaluated", size="xs", c="dimmed")

    return html.Div(
        className="decisions-card",
        style={"borderLeft": f"3px solid {m_color}"},
        children=[
            # Model Header
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Group([
                        html.Span(
                            className="dot-indicator",
                            style={"backgroundColor": m_color, "boxShadow": f"0 0 6px {m_color}88"}
                        ),
                        dmc.Text(model_result.model_name, fw=700, size="xs", c="white", style={"fontFamily": "'JetBrains Mono', monospace"}),
                        dmc.Badge(
                            f"{model_result.latency_ms:.0f} ms",
                            variant="outline",
                            color="gray",
                            size="xs",
                        ),
                    ], gap=8),
                    header_metric,
                ],
                style={"marginBottom": "10px", "paddingBottom": "6px", "borderBottom": "1px solid rgba(255,255,255,0.06)"},
            ),

            # Evaluation items
            html.Div(eval_bars),
        ]
    )


def render_decisions_content(
    results: List[ModelResult],
    threshold_percent: float,
    ground_truth_map: Optional[Dict[str, Any]] = None,
    is_maximized: bool = False,
):
    """Full rendered decisions content (supports side-by-side comparison for up to 4 models)."""
    if not results:
        return render_empty_decisions()

    model_cards = [render_model_decision_card(r, threshold_percent, ground_truth_map) for r in results]

    # Grid columns layout: if maximized or spacious, display all models completely side-by-side!
    grid_cols = f"repeat({len(model_cards)}, minmax(280px, 1fr))" if is_maximized else ("1fr" if len(model_cards) <= 1 else "repeat(auto-fit, minmax(320px, 1fr))")

    return html.Div(
        style={"display": "flex", "flexDirection": "column", "gap": "10px"},
        children=[
            # Side-by-side or stacked models (supports up to 4 models)
            html.Div(
                id="decisions-models-container",
                style={
                    "display": "grid",
                    "gridTemplateColumns": grid_cols,
                    "gap": "10px",
                },
                children=model_cards,
            ),
        ]
    )


def create_decisions_panel():
    return html.Div(
        id="decisions-panel-wrapper",
        className="panel-wrapper",
        style={"flex": "1.75", "minWidth": "380px"},
        children=[
            # Normal Expanded Card
            html.Div(
                id="decisions-panel-card",
                className="panel-card",
                style={"display": "flex", "height": "100%", "width": "100%"},
                children=[
                    # Header
                    html.Div(
                        className="panel-header",
                        children=[
                            dmc.Group([
                                dmc.Badge("DECISIONS", variant="light", color="gray", size="xs", radius="xs"),
                                dmc.Text(
                                    id="decisions-status-indicator",
                                    children="Awaiting run...",
                                    size="xs",
                                    c="dimmed",
                                ),
                            ], gap="xs"),
                            dmc.Group([
                                dmc.Badge(id="active-models-summary", children="2 Models Active", variant="outline", color="gray", size="xs"),
                                dmc.Tooltip(
                                    label="Collapse to side",
                                    children=dmc.ActionIcon(
                                        id="btn-collapse-decisions",
                                        children=DashIconify(icon="tabler:layout-sidebar-left-collapse", width=14, color="#94a3b8"),
                                        variant="subtle",
                                        color="gray",
                                        size="xs",
                                    ),
                                ),
                                dmc.Tooltip(
                                    label="Maximize to full screen",
                                    children=dmc.ActionIcon(
                                        id="btn-maximize-decisions",
                                        children=DashIconify(icon="tabler:arrows-maximize", width=14, color="#94a3b8"),
                                        variant="subtle",
                                        color="gray",
                                        size="xs",
                                    ),
                                ),
                            ], gap=4),
                        ]
                    ),

                    # Body
                    html.Div(
                        className="panel-body",
                        id="decisions-panel-content",
                        children=render_empty_decisions(),
                    ),
                ]
            ),

            # Collapsed Ribbon (shown when decisions panel is hidden to the left side)
            html.Div(
                id="decisions-panel-collapsed-strip",
                className="collapsed-ribbon",
                style={"display": "none"},
                title="Click to restore Decisions panel",
                children=[
                    dmc.ActionIcon(
                        id="btn-expand-decisions-strip",
                        children=DashIconify(icon="tabler:layout-sidebar-left-expand", width=16, color="#94a3b8"),
                        variant="subtle",
                        color="gray",
                        size="xs",
                    ),
                    html.Span("DECISIONS", className="collapsed-ribbon-text"),
                ]
            ),
        ]
    )
