"""
Questions panel component (Center Column).
Renders decision criteria questions matching TypeSafe primitives:
- Noul: Binary boolean judgment with True/False criteria
- Choice: Categorical judgment over discrete options
- Score: Continuous spectrum along ordered rubric criteria
Provides interactive primitive switcher, option badges with tooltips,
expandable criteria inspector, and question deletion.
"""
from typing import List, Dict, Any
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify
from src.types import DecisionQuestion, QuestionType


def render_question_criteria_section(q: DecisionQuestion, q_type: str):
    """Builds interactive option badges with tooltips and expandable criteria inspector."""
    badge_elements = []
    detail_rows = []
    count = 0

    if q_type == "choice":
        crit_dict = q.criteria if isinstance(q.criteria, dict) else {}
        options = list(crit_dict.keys()) if crit_dict else (q.choices or [])
        count = len(options)
        for opt in options:
            desc = crit_dict.get(opt, opt) if crit_dict else opt
            badge_elements.append(
                dmc.Tooltip(
                    label=f"{opt}: {desc}",
                    multiline=True,
                    w=280,
                    withArrow=True,
                    position="top",
                    children=dmc.Badge(
                        opt,
                        variant="light",
                        color="cyan",
                        size="xs",
                        radius="xs",
                        style={
                            "marginRight": "4px",
                            "marginBottom": "4px",
                            "textTransform": "none",
                            "fontFamily": "'JetBrains Mono', monospace",
                            "cursor": "pointer",
                        },
                    ),
                )
            )
            detail_rows.append(
                dmc.Group([
                    dmc.Badge(opt, color="cyan", variant="light", size="xs", style={"fontFamily": "'JetBrains Mono', monospace", "minWidth": "65px", "textTransform": "none"}),
                    dmc.Text(desc, size="xs", c="#94a3b8", style={"flex": "1", "fontSize": "11px", "lineHeight": 1.4}),
                ], align="flex-start", gap=8)
            )

    elif q_type == "score":
        levels = q.criteria if isinstance(q.criteria, list) else []
        count = len(levels)
        for idx, lvl_text in enumerate(levels):
            badge_elements.append(
                dmc.Tooltip(
                    label=f"Level {idx}: {lvl_text}",
                    multiline=True,
                    w=300,
                    withArrow=True,
                    position="top",
                    children=dmc.Badge(
                        f"L{idx}",
                        variant="light",
                        color="violet",
                        size="xs",
                        radius="xs",
                        style={
                            "marginRight": "4px",
                            "marginBottom": "4px",
                            "fontFamily": "'JetBrains Mono', monospace",
                            "cursor": "pointer",
                        },
                    ),
                )
            )
            detail_rows.append(
                dmc.Group([
                    dmc.Badge(f"Level {idx}", color="violet", variant="light", size="xs", style={"fontFamily": "'JetBrains Mono', monospace", "minWidth": "65px"}),
                    dmc.Text(str(lvl_text), size="xs", c="#94a3b8", style={"flex": "1", "fontSize": "11px", "lineHeight": 1.4}),
                ], align="flex-start", gap=8)
            )

    else:  # noul / boolean
        crit_dict = q.criteria if isinstance(q.criteria, dict) else {}
        true_desc = crit_dict.get("true", "Target condition or spec is strictly met.")
        false_desc = crit_dict.get("false", "Target condition failed, spec missed, or non-conformance detected.")
        count = 2

        badge_elements.append(
            dmc.Tooltip(
                label=f"True: {true_desc}",
                multiline=True,
                w=280,
                withArrow=True,
                position="top",
                children=dmc.Badge(
                    "True",
                    variant="light",
                    color="blue",
                    size="xs",
                    radius="xs",
                    style={
                        "marginRight": "4px",
                        "marginBottom": "4px",
                        "fontFamily": "'JetBrains Mono', monospace",
                        "cursor": "pointer",
                    },
                ),
            )
        )
        badge_elements.append(
            dmc.Tooltip(
                label=f"False: {false_desc}",
                multiline=True,
                w=280,
                withArrow=True,
                position="top",
                children=dmc.Badge(
                    "False",
                    variant="outline",
                    color="gray",
                    size="xs",
                    radius="xs",
                    style={
                        "marginRight": "4px",
                        "marginBottom": "4px",
                        "fontFamily": "'JetBrains Mono', monospace",
                        "cursor": "pointer",
                    },
                ),
            )
        )
        detail_rows.append(
            dmc.Group([
                dmc.Badge("True", color="blue", variant="light", size="xs", style={"fontFamily": "'JetBrains Mono', monospace", "minWidth": "65px"}),
                dmc.Text(true_desc, size="xs", c="#94a3b8", style={"flex": "1", "fontSize": "11px", "lineHeight": 1.4}),
            ], align="flex-start", gap=8)
        )
        detail_rows.append(
            dmc.Group([
                dmc.Badge("False", color="gray", variant="outline", size="xs", style={"fontFamily": "'JetBrains Mono', monospace", "minWidth": "65px"}),
                dmc.Text(false_desc, size="xs", c="#94a3b8", style={"flex": "1", "fontSize": "11px", "lineHeight": 1.4}),
            ], align="flex-start", gap=8)
        )

    # Accordion inspector for full definitions
    accordion_item = dmc.Accordion(
        variant="subtle",
        chevronPosition="right",
        children=[
            dmc.AccordionItem(
                value="criteria-details",
                children=[
                    dmc.AccordionControl(
                        dmc.Group([
                            DashIconify(icon="tabler:file-text", width=12, color="#94a3b8"),
                            dmc.Text(
                                f"Criteria Definitions ({count})",
                                size="xs",
                                c="dimmed",
                                style={"fontFamily": "'JetBrains Mono', monospace", "fontSize": "10.5px"},
                            ),
                        ], gap=5),
                        style={"padding": "2px 0", "minHeight": "20px"},
                    ),
                    dmc.AccordionPanel(
                        dmc.Stack(detail_rows, gap=4),
                        style={"padding": "4px 6px", "backgroundColor": "rgba(0, 0, 0, 0.25)", "borderRadius": "4px"},
                    ),
                ],
            ),
        ],
        styles={
            "item": {"border": "none"},
            "control": {"padding": "2px 0", "&:hover": {"backgroundColor": "transparent"}},
            "content": {"padding": "2px 0 0 0"},
        },
    )

    return html.Div(
        children=[
            html.Div(badge_elements, style={"display": "flex", "flexWrap": "wrap", "marginBottom": "4px"}) if badge_elements else html.Div(),
            accordion_item,
        ]
    )


def render_question_card(q: DecisionQuestion, status_class: str = "") -> html.Div:
    """Renders a single question card formatted for TypeSafe primitives."""
    q_type = getattr(q, "type", "noul").lower()
    is_choice = (q_type == "choice")
    is_score = (q_type == "score")
    type_val = "choice" if is_choice else ("score" if is_score else "noul")

    if type_val == "choice":
        metric_label = "Choice: P(distribution) across options"
        type_badge = dmc.Badge(
            "CHOICE",
            size="xs",
            variant="outline",
            color="cyan",
            style={"fontSize": "9px", "height": "18px", "padding": "0 5px", "fontFamily": "'JetBrains Mono', monospace"},
        )
    elif type_val == "score":
        metric_label = "Score: Spectrum along rubric levels"
        type_badge = dmc.Badge(
            "SCORE",
            size="xs",
            variant="outline",
            color="violet",
            style={"fontSize": "9px", "height": "18px", "padding": "0 5px", "fontFamily": "'JetBrains Mono', monospace"},
        )
    else:
        metric_label = "Noul: P(yes) ∈ [0.0, 1.0]"
        type_badge = dmc.Badge(
            "NOUL",
            size="xs",
            variant="outline",
            color="blue",
            style={"fontSize": "9px", "height": "18px", "padding": "0 5px", "fontFamily": "'JetBrains Mono', monospace"},
        )

    card_key = q.id or q.name

    return html.Div(
        className=f"question-card {status_class}",
        id={"type": "question-card-container", "index": card_key},
        children=[
            # Top row: Name, Type select, primitive badge, delete button
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Group([
                        dmc.Text(q.name, className="question-title"),
                        dmc.Select(
                            id={"type": "q-type-select", "index": card_key},
                            data=[
                                {"value": "noul", "label": "noul"},
                                {"value": "choice", "label": "choice"},
                                {"value": "score", "label": "score"},
                            ],
                            value=type_val,
                            size="xs",
                            style={"width": "85px"},
                        ),
                        type_badge,
                    ], gap=8),
                    dmc.Group([
                        dmc.Button(
                            id={"type": "q-edit-btn", "index": card_key},
                            children="Edit",
                            leftSection=DashIconify(icon="tabler:edit", width=12, color="#94a3b8"),
                            variant="subtle",
                            color="gray",
                            size="xs",
                            style={
                                "height": "20px",
                                "padding": "0 6px",
                                "fontSize": "10px",
                                "fontFamily": "'JetBrains Mono', monospace",
                                "color": "#94a3b8",
                            },
                        ),
                        dmc.Button(
                            id={"type": "q-delete-btn", "index": card_key},
                            children="Remove",
                            rightSection=DashIconify(icon="tabler:x", width=12, color="#94a3b8"),
                            variant="subtle",
                            color="gray",
                            size="xs",
                            style={
                                "height": "20px",
                                "padding": "0 6px",
                                "fontSize": "10px",
                                "fontFamily": "'JetBrains Mono', monospace",
                                "color": "#94a3b8",
                            },
                        ),
                    ], gap=4),
                ]
            ),

            # Instructions text
            dmc.Text(q.instructions, className="question-prompt"),

            # Metric target
            dmc.Text(
                metric_label,
                size="xs",
                c="#64748b",
                fw=500,
                style={"marginBottom": "6px", "fontFamily": "'JetBrains Mono', monospace"},
            ),

            # Interactive Criteria & Options Section
            render_question_criteria_section(q, type_val),
        ]
    )


def create_questions_panel(initial_questions: List[DecisionQuestion]):
    cards = [render_question_card(q) for q in initial_questions]

    return html.Div(
        id="questions-panel-wrapper",
        className="panel-wrapper",
        style={"flex": "1.25", "minWidth": "320px"},
        children=[
            # Normal Expanded Card
            html.Div(
                id="questions-panel-card",
                className="panel-card",
                style={"display": "flex", "height": "100%", "width": "100%"},
                children=[
                    # Header
                    html.Div(
                        className="panel-header",
                        children=[
                            dmc.Group([
                                dmc.Badge("QUESTIONS", variant="light", color="gray", size="xs", radius="xs"),
                                dmc.Select(
                                    id="question-template-select",
                                    data=[
                                        {"value": "manufacturing_gates", "label": "Process Quality Gates"},
                                        {"value": "custom", "label": "Custom Criteria"},
                                    ],
                                    value="manufacturing_gates",
                                    allowDeselect=False,
                                    size="xs",
                                    style={"width": "170px"},
                                ),
                            ], gap="xs"),
                            dmc.Group([
                                dmc.Button(
                                    id="add-question-btn",
                                    children="Add Check",
                                    leftSection=DashIconify(icon="tabler:plus", width=13, color="#94a3b8"),
                                    variant="subtle",
                                    size="xs",
                                    color="gray",
                                    style={"padding": "0 6px"},
                                ),
                                dmc.Tooltip(
                                    label="Collapse to side",
                                    children=dmc.ActionIcon(
                                        id="btn-collapse-questions",
                                        children=DashIconify(icon="tabler:layout-sidebar-left-collapse", width=14, color="#94a3b8"),
                                        variant="subtle",
                                        color="gray",
                                        size="xs",
                                    ),
                                ),
                                dmc.Tooltip(
                                    label="Maximize to full screen",
                                    children=dmc.ActionIcon(
                                        id="btn-maximize-questions",
                                        children=DashIconify(icon="tabler:arrows-maximize", width=14, color="#94a3b8"),
                                        variant="subtle",
                                        color="gray",
                                        size="xs",
                                    ),
                                ),
                            ], gap=2),
                        ]
                    ),

                    # Body / Questions list
                    html.Div(
                        className="panel-body",
                        id="questions-list-container",
                        children=cards,
                    ),
                ]
            ),

            # Collapsed Ribbon (shown when questions panel is hidden to the left side)
            html.Div(
                id="questions-panel-collapsed-strip",
                className="collapsed-ribbon",
                style={"display": "none"},
                title="Click to restore Questions panel",
                children=[
                    dmc.ActionIcon(
                        id="btn-expand-questions-strip",
                        children=DashIconify(icon="tabler:layout-sidebar-left-expand", width=16, color="#94a3b8"),
                        variant="subtle",
                        color="gray",
                        size="xs",
                    ),
                    html.Span("QUESTIONS", className="collapsed-ribbon-text"),
                ]
            ),
        ]
    )
