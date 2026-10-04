"""
Decisions panel component (Right Column).
Displays side-by-side model predictions for up to 4 models, calibrated probability
and confidence meters with threshold indicators, and extracted log excerpts.
Includes expandable/collapsible card controls to occupy full screen or hide to side ribbon.
"""
from typing import List, Optional, Any
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify
from src.types import ModelResult, QuestionEvaluation
from src.config import get_available_models, get_default_model


def render_empty_decisions():
    """Initial placeholder before run."""
    return html.Div(
        style={
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
            "height": "100%",
            "minHeight": "240px",
            "color": "#64748b",
            "textAlign": "center",
            "padding": "32px 16px",
        },
        children=[
            html.Div(
                style={
                    "width": "54px",
                    "height": "54px",
                    "borderRadius": "50%",
                    "backgroundColor": "rgba(56, 189, 248, 0.08)",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "marginBottom": "14px",
                    "border": "1px solid rgba(56, 189, 248, 0.18)",
                },
                children=[DashIconify(icon="tabler:cpu", width=26, color="#38bdf8")],
            ),
            dmc.Text("Ready for Decision Inference", size="sm", fw=600, c="#f1f5f9"),
            dmc.Text(
                "Select a state, questions, and one or more models, and click Run.",
                size="xs",
                c="#94a3b8",
                mt=6,
                style={"maxWidth": "320px", "lineHeight": 1.5},
            ),
        ]
    )


NOUL_10_GRADIENT = [
    "#172554",  # 0-10%  (deep dark blue)
    "#1e3a8a",  # 10-20%
    "#1e40af",  # 20-30%
    "#1d4ed8",  # 30-40%
    "#2563eb",  # 40-50%
    "#3b82f6",  # 50-60%
    "#339af0",  # 60-70% (Mantine blue outline font color)
    "#60a5fa",  # 70-80%
    "#93c5fd",  # 80-90%
    "#bfdbfe",  # 90-100% (luminous light blue)
]

CHOICE_10_GRADIENT = [
    "#083344",  # 0-10%  (deep dark cyan)
    "#164e63",  # 10-20%
    "#155e75",  # 20-30%
    "#0e7490",  # 30-40%
    "#0891b2",  # 40-50%
    "#06b6d4",  # 50-60%
    "#15aabf",  # 60-70% (Mantine cyan outline font color)
    "#22d3ee",  # 70-80%
    "#67e8f9",  # 80-90%
    "#cffafe",  # 90-100% (luminous light cyan)
]


def get_score_gradient(num_steps: int) -> List[str]:
    """Generates `num_steps` gradient colors in violet spectrum for Score levels."""
    if num_steps <= 1:
        return ["#8b5cf6"]
    if num_steps == 2:
        return ["#5b21b6", "#c084fc"]
    if num_steps == 3:
        return ["#4c1d95", "#7950f2", "#c084fc"]
    if num_steps == 4:
        # Standard: 4 levels (0, 1, 2, 3) when highest score is 3
        return ["#4c1d95", "#6d28d9", "#7950f2", "#c084fc"]
    if num_steps == 5:
        return ["#4c1d95", "#5b21b6", "#7c3aed", "#8b5cf6", "#c084fc"]

    palette = [
        "#4c1d95", "#581c87", "#5b21b6", "#6d28d9", "#7c3aed",
        "#7950f2", "#8b5cf6", "#a855f7", "#c084fc", "#d8b4fe"
    ]
    indices = [int(round(i * (len(palette) - 1) / (num_steps - 1))) for i in range(num_steps)]
    return [palette[i] for i in indices]


def render_stepped_gradient_meter(
    pct: float,
    num_steps: int,
    gradient_colors: List[str],
) -> html.Div:
    """
    Renders a stepped gradient meter bar with separate capsule segments.
    Each capsule segment represents a discrete level/step with its specific gradient color,
    filling smoothly based on the percentage (0 to 100%).
    """
    clamped_pct = max(0.0, min(100.0, float(pct)))
    ratio = clamped_pct / 100.0

    step_elements = []
    for i in range(num_steps):
        color = gradient_colors[i] if i < len(gradient_colors) else gradient_colors[-1]
        step_min = i / num_steps
        step_max = (i + 1) / num_steps

        if ratio >= step_max:
            fill_pct = 100.0
        elif ratio <= step_min:
            fill_pct = 0.0
        else:
            fill_pct = ((ratio - step_min) / (step_max - step_min)) * 100.0

        is_lit = fill_pct > 0
        step_elements.append(
            html.Div(
                style={
                    "flex": "1",
                    "height": "7px",
                    "backgroundColor": "rgba(255, 255, 255, 0.06)",
                    "borderRadius": "3px",
                    "overflow": "hidden",
                    "position": "relative",
                    "border": "1px solid rgba(255, 255, 255, 0.04)",
                },
                children=[
                    html.Div(
                        style={
                            "width": f"{fill_pct:.1f}%",
                            "height": "100%",
                            "backgroundColor": color,
                            "borderRadius": "2px",
                            "boxShadow": f"0 0 6px {color}88" if is_lit else "none",
                            "transition": "width 0.2s ease",
                        }
                    )
                ]
            )
        )

    return html.Div(
        className="stepped-gradient-meter",
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "3px",
            "width": "100%",
            "marginTop": "7px",
            "marginBottom": "6px",
        },
        children=step_elements,
    )


def render_continuous_gradient_meter(
    pct: float,
    gradient_colors: List[str],
) -> html.Div:
    """Alias for backwards compatibility, redirects to stepped capsule gradient meter."""
    return render_stepped_gradient_meter(pct=pct, num_steps=len(gradient_colors), gradient_colors=gradient_colors)


def render_evaluation_bar(
    ev: QuestionEvaluation,
    threshold_percent: float,
    model_color: str,
    **kwargs,
):
    """Renders a single question decision item with type badge, predicted value, stepped capsule meter, and log excerpt."""
    q_type = str(getattr(ev, "question_type", "noul")).lower()
    is_score = (q_type in ("score", "ordinal"))
    is_choice = (q_type in ("choice", "categorical"))

    if is_score:
        top_level = float(getattr(ev, "metadata", {}).get("top_level", 0.0))
        if top_level <= 0:
            top_level = 3.0
        score_val = float(ev.score if ev.score is not None else ev.p_true)
        p_pct = min(100.0, max(0.0, (score_val / top_level) * 100.0))
        pred_label = f"Score {score_val:.2f} / {int(top_level)}"
        metric_str = f"{ev.confidence*100:.0f}% conf" if ev.confidence > 0 else ""
        type_badge = dmc.Badge(
            "SCORE",
            size="xs",
            variant="outline",
            color="violet",
            style={"fontSize": "9px", "height": "18px", "padding": "0 5px", "fontFamily": "'JetBrains Mono', monospace"},
        )
        pred_badge = dmc.Badge(
            pred_label,
            color="violet",
            variant="light",
            size="xs",
            style={"fontFamily": "'JetBrains Mono', monospace", "height": "20px"},
        )
        num_steps = int(top_level) + 1
        gradient_colors = get_score_gradient(num_steps)
    elif is_choice:
        p_pct = ev.confidence * 100.0
        choice_val = ev.selected_choice if ev.selected_choice else "-"
        metric_str = f"{p_pct:.1f}%"
        type_badge = dmc.Badge(
            "CHOICE",
            size="xs",
            variant="outline",
            color="cyan",
            style={"fontSize": "9px", "height": "18px", "padding": "0 5px", "fontFamily": "'JetBrains Mono', monospace"},
        )
        pred_badge = dmc.Badge(
            choice_val,
            color="cyan",
            variant="light",
            size="xs",
            style={"fontFamily": "'JetBrains Mono', monospace", "textTransform": "none", "height": "20px"},
        )
        num_steps = 10
        gradient_colors = CHOICE_10_GRADIENT
    else:  # noul / boolean
        p_pct = ev.p_true * 100.0
        model_pred_bool = (ev.p_true >= 0.5)
        metric_str = f"{p_pct:.1f}%"
        type_badge = dmc.Badge(
            "NOUL",
            size="xs",
            variant="outline",
            color="blue",
            style={"fontSize": "9px", "height": "18px", "padding": "0 5px", "fontFamily": "'JetBrains Mono', monospace"},
        )
        pred_badge = dmc.Badge(
            "TRUE" if model_pred_bool else "FALSE",
            color="blue",
            variant="light",
            size="xs",
            style={"fontFamily": "'JetBrains Mono', monospace", "fontWeight": 700, "height": "20px"},
        )
        num_steps = 10
        gradient_colors = NOUL_10_GRADIENT

    raw_excerpt = ev.evidence if ev.evidence else ev.rationale
    excerpt_text = raw_excerpt.strip().strip('"').strip("'") if raw_excerpt else ""

    meter_bar = render_stepped_gradient_meter(
        pct=p_pct,
        num_steps=num_steps,
        gradient_colors=gradient_colors,
    )

    return html.Div(
        style={
            "marginBottom": "8px",
            "padding": "9px 12px",
            "background": "rgba(255, 255, 255, 0.02)",
            "borderRadius": "5px",
            "border": "1px solid rgba(255, 255, 255, 0.04)",
            "transition": "border-color 0.15s ease",
        },
        children=[
            # Top row: Type badge + Question Name on left, Prediction badge + Metric on right
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Group([
                        type_badge,
                        dmc.Text(
                            ev.question_name,
                            fw=600,
                            size="xs",
                            style={"fontFamily": "'JetBrains Mono', monospace", "color": "#f1f5f9"},
                        ),
                    ], gap=8),
                    dmc.Group([
                        pred_badge,
                        dmc.Text(
                            metric_str,
                            size="xs",
                            fw=600,
                            c="#94a3b8",
                            style={"fontFamily": "'JetBrains Mono', monospace"},
                        ),
                    ], gap=8),
                ]
            ),
            # Stepped Gradient Meter container
            meter_bar,
            # Log excerpt / rationale
            dmc.Group(
                gap=6,
                style={"marginTop": "4px"},
                children=[
                    DashIconify(icon="tabler:quote", width=12, color="#64748b"),
                    dmc.Text(
                        excerpt_text if excerpt_text else "No log excerpt extracted",
                        size="xs",
                        c="#94a3b8",
                        style={
                            "fontStyle": "italic",
                            "maxWidth": "94%",
                            "overflow": "hidden",
                            "textOverflow": "ellipsis",
                            "whiteSpace": "nowrap",
                            "fontSize": "11.5px",
                        },
                    ),
                ]
            ) if excerpt_text else html.Span(),
        ]
    )


def render_model_decision_card(
    model_result: ModelResult,
    threshold_percent: float,
    **kwargs,
):
    """Renders a decisions card for a single model with its distinct color identity and clean layout."""
    m_color = model_result.model_color
    total_count = len(model_result.evaluations)

    eval_bars = [
        render_evaluation_bar(e, threshold_percent, m_color)
        for e in model_result.evaluations
    ]

    return html.Div(
        className="decisions-card",
        style={
            "borderLeft": f"3px solid {m_color}",
            "background": "linear-gradient(180deg, #11141c 0%, #0d0f16 100%)",
            "border": "1px solid #1f2533",
            "borderLeftWidth": "3px",
            "borderRadius": "6px",
            "padding": "12px 14px",
            "boxShadow": "0 4px 16px rgba(0, 0, 0, 0.25)",
        },
        children=[
            # Model Header
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Group([
                        html.Span(
                            className="dot-indicator",
                            style={"backgroundColor": m_color, "boxShadow": f"0 0 8px {m_color}"}
                        ),
                        dmc.Text(
                            model_result.model_name,
                            fw=700,
                            size="xs",
                            c="white",
                            style={"fontFamily": "'JetBrains Mono', monospace", "letterSpacing": "-0.01em"}
                        ),
                        dmc.Badge(
                            f"{model_result.latency_ms:.0f} ms",
                            variant="outline",
                            color="gray",
                            size="xs",
                            leftSection=DashIconify(icon="tabler:bolt", width=11, color="#94a3b8"),
                            style={"fontFamily": "'JetBrains Mono', monospace"},
                        ),
                    ], gap=8),
                    dmc.Badge(
                        f"{total_count} criteria(s)",
                        variant="light",
                        color="dark",
                        size="xs",
                        style={"fontFamily": "'JetBrains Mono', monospace", "color": "#94a3b8"},
                    ),
                ],
                style={"marginBottom": "10px", "paddingBottom": "8px", "borderBottom": "1px solid rgba(255, 255, 255, 0.06)"},
            ),

            # Evaluation items
            html.Div(eval_bars),
        ]
    )


def render_decisions_content(
    results: List[ModelResult],
    threshold_percent: float,
    ground_truth_map: Optional[Any] = None,
    is_maximized: bool = False,
):
    """Full rendered decisions content (supports side-by-side comparison for up to 4 models)."""
    if not results:
        return render_empty_decisions()

    model_cards = [render_model_decision_card(r, threshold_percent) for r in results]

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


def create_decisions_panel(
    available_models: Optional[List[str]] = None,
    default_models: Optional[List[str]] = None,
):
    if available_models is None:
        try:
            from src.ollama_client import get_cross_referenced_models
            available_models = get_cross_referenced_models()
        except Exception:
            available_models = get_available_models()

    if default_models is None:
        def_m = get_default_model()
        default_models = [def_m] if (def_m and def_m in available_models) else (available_models[:1] if available_models else [])

    count = len(default_models)
    btn_label = f"{count} model(s)" if count > 0 else "0 model"

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
                                # Real dropdown box for model selection
                                dmc.Popover(
                                    id="models-popover",
                                    position="bottom-start",
                                    shadow="md",
                                    radius="xs",
                                    withArrow=False,
                                    children=[
                                        dmc.PopoverTarget(
                                            dmc.Button(
                                                id="models-dropdown-btn",
                                                children=btn_label,
                                                size="xs",
                                                variant="default",
                                                rightSection=DashIconify(icon="tabler:chevron-down", width=12, color="#94a3b8"),
                                                style={
                                                    "backgroundColor": "#090a0f",
                                                    "border": "1px solid #1f2430",
                                                    "color": "#f1f5f9",
                                                    "fontFamily": "'JetBrains Mono', monospace",
                                                    "fontSize": "11px",
                                                    "fontWeight": 500,
                                                    "height": "26px",
                                                    "padding": "0 10px",
                                                },
                                            )
                                        ),
                                        dmc.PopoverDropdown(
                                            style={
                                                "backgroundColor": "#0e1015",
                                                "border": "1px solid #2a3142",
                                                "padding": "8px 12px",
                                                "minWidth": "160px",
                                            },
                                            children=[
                                                dmc.CheckboxGroup(
                                                    id="decisions-model-select",
                                                    value=default_models,
                                                    children=dmc.Stack(
                                                        id="decisions-model-checkboxes",
                                                        gap=6,
                                                        children=[
                                                            dmc.Checkbox(
                                                                label=m,
                                                                value=m,
                                                                size="xs",
                                                                color="blue",
                                                                styles={
                                                                    "input": {"cursor": "pointer", "backgroundColor": "#090a0f", "borderColor": "#2a3142"},
                                                                    "label": {
                                                                        "cursor": "pointer",
                                                                        "fontFamily": "'JetBrains Mono', monospace",
                                                                        "fontSize": "11px",
                                                                        "color": "#f1f5f9",
                                                                        "paddingLeft": "4px",
                                                                    },
                                                                },
                                                            )
                                                            for m in available_models
                                                        ],
                                                    ),
                                                )
                                            ]
                                        )
                                    ]
                                ),
                                # Run Button
                                dmc.Button(
                                    id="run-button",
                                    children=[
                                        html.Span(
                                            className="run-btn-idle",
                                            style={"display": "inline-flex", "alignItems": "center", "gap": "6px"},
                                            children=[
                                                DashIconify(icon="tabler:player-play-filled", width=12, color="#94a3b8"),
                                                html.Span("Run"),
                                            ]
                                        ),
                                        html.Span(
                                            className="run-btn-loading",
                                            style={"display": "none", "alignItems": "center", "gap": "6px"},
                                            children=[
                                                html.Span(className="animated-circle-spinner"),
                                                html.Span("Running"),
                                            ]
                                        ),
                                    ],
                                    variant="filled",
                                    size="xs",
                                    radius="xs",
                                    style={
                                        "fontWeight": 700,
                                        "fontSize": "11.5px",
                                        "height": "26px",
                                        "backgroundColor": "#19202c",
                                        "color": "#ffffff",
                                        "border": "1px solid #2a3142",
                                        "padding": "0 12px",
                                        "cursor": "pointer",
                                    },
                                ),
                            ], gap="xs"),
                            dmc.Group([
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
