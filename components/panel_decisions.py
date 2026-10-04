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


def render_evaluation_bar(
    ev: QuestionEvaluation,
    threshold_percent: float,
    model_color: str,
    ground_truth: Optional[Any] = None,
):
    """Renders a single question probability meter with vertical threshold indicator and ground truth badge."""
    q_type = str(getattr(ev, "question_type", "noul")).lower()
    is_score = (q_type in ("score", "ordinal"))
    is_choice = (q_type in ("choice", "categorical"))

    if is_score:
        score_val = ev.score if ev.score is not None else ev.p_true
        p_pct = min(100.0, max(0.0, (score_val / 3.0) * 100.0))
        metric_str = f"Score = {score_val:.1f}"
    elif is_choice:
        p_pct = ev.confidence * 100.0
        metric_str = f"P = {p_pct:.1f}%"
    else:
        p_pct = ev.p_true * 100.0
        metric_str = f"P(true) = {p_pct:.1f}%"

    bar_color = "teal" if ev.passed else ("red" if ev.required else "orange")
    status_badge_color = "green" if ev.passed else ("red" if ev.required else "orange")
    status_text = "PASS" if ev.passed else ("FAIL (REQ)" if ev.required else "FLAGGED")

    # Render Ground Truth Badge if template is active and has ground truth
    gt_badge = None
    if ground_truth is not None:
        if is_score:
            gt_num = float(ground_truth)
            is_match = abs((ev.score if ev.score is not None else ev.p_true) - gt_num) < 0.6
            gt_badge = dmc.Badge(
                f"Truth: Level {int(gt_num)}",
                color="teal" if is_match else "blue",
                variant="light",
                size="xs",
                style={"fontFamily": "'JetBrains Mono', monospace"},
            )
        elif is_choice:
            gt_str = str(ground_truth)
            is_match = (ev.selected_choice == gt_str)
            gt_badge = dmc.Badge(
                f"Truth: {gt_str}",
                color="teal" if is_match else "orange",
                variant="light",
                size="xs",
                style={"fontFamily": "'JetBrains Mono', monospace", "textTransform": "none"},
            )
        else:  # noul / boolean
            gt_bool = bool(ground_truth)
            model_pred_bool = (ev.p_true >= 0.5)
            is_match = (model_pred_bool == gt_bool)
            gt_badge = dmc.Badge(
                f"Truth: {gt_bool}",
                color="teal" if is_match else "orange",
                variant="light",
                size="xs",
                style={"fontFamily": "'JetBrains Mono', monospace"},
            )

    return html.Div(
        style={"marginBottom": "10px", "padding": "7px 10px", "background": "rgba(255,255,255,0.015)", "borderRadius": "4px", "border": "1px solid rgba(255,255,255,0.03)"},
        children=[
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Group([
                        dmc.Text(ev.question_name, fw=600, size="xs", style={"fontFamily": "'JetBrains Mono', monospace", "color": "#f8fafc"}),
                        dmc.Badge(status_text, color=status_badge_color, size="xs", variant="light"),
                    ], gap=8),
                    dmc.Group([
                        dmc.Text(
                            metric_str,
                            size="xs",
                            fw=600,
                            c="#e2e8f0" if ev.passed else "#f87171",
                            style={"fontFamily": "'JetBrains Mono', monospace"},
                        ),
                        gt_badge if gt_badge else html.Span(),
                    ], gap=6),
                ]
            ),
            # Probability bar with threshold line
            html.Div(
                className="prob-meter-container",
                children=[
                    dmc.Progress(value=p_pct, color=bar_color, size="sm", radius="xs"),
                    # Threshold vertical line marker
                    html.Div(
                        className="threshold-marker",
                        style={"left": f"{threshold_percent}%"},
                    ),
                ]
            ),
            # Evidence snippet
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Text(
                        f"Evidence: \"{ev.evidence}\"" if ev.evidence else ev.rationale,
                        size="xs",
                        c="#94a3b8",
                        style={"fontStyle": "italic", "maxWidth": "85%", "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"},
                    ),
                    dmc.Text(ev.selected_choice if ev.selected_choice else "", size="xs", c="cyan", fw=500),
                ]
            ),
        ]
    )


def render_model_decision_card(
    model_result: ModelResult,
    threshold_percent: float,
    ground_truth_map: Optional[Dict[str, Any]] = None,
):
    """Renders a decisions card for a single model with its distinct color identity and GT comparisons."""
    passed_count = sum(1 for e in model_result.evaluations if e.passed)
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
                    dmc.Text(f"{passed_count}/{total_count} Passed", size="xs", c="dimmed"),
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
