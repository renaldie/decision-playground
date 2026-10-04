"""
Questions panel component (Center Column).
Renders decision criteria questions matching the screenshot layout,
including bool/choice types, pass conditions, required toggles, and choice pills.
Uses dark monochrome icons.
"""
from typing import List
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify
from src.types import DecisionQuestion, QuestionType, PassCondition


def render_question_card(q: DecisionQuestion, status_class: str = "") -> html.Div:
    """Renders a single question card formatted like the screenshot."""
    q_type = getattr(q, "type", "noul").lower()
    is_choice = (q_type == "choice")
    is_score = (q_type == "score")
    type_val = "choice" if is_choice else ("score" if is_score else "noul")
    pass_cond_val = q.pass_condition.value if isinstance(q.pass_condition, PassCondition) else str(q.pass_condition)

    # Choice chips if choice type
    choice_pills = []
    if is_choice and q.choices:
        for c in q.choices:
            is_target = (c == q.pass_choice)
            choice_pills.append(
                dmc.Badge(
                    c,
                    variant="filled" if is_target else "outline",
                    color="dark" if not is_target else "teal",
                    size="xs",
                    radius="xs",
                    style={"cursor": "pointer", "marginRight": "4px", "textTransform": "none", "fontFamily": "'JetBrains Mono', monospace"},
                )
            )

    return html.Div(
        className=f"question-card {status_class}",
        id={"type": "question-card-container", "index": q.id or q.name},
        children=[
            # Top row: Name, Type select, quick actions, delete button
            dmc.Group(
                justify="space-between",
                children=[
                    dmc.Group([
                        dmc.Text(q.name, className="question-title"),
                        dmc.Select(
                            id={"type": "q-type-select", "index": q.id or q.name},
                            data=[
                                {"value": "noul", "label": "noul"},
                                {"value": "choice", "label": "choice"},
                                {"value": "score", "label": "score"},
                            ],
                            value=type_val,
                            size="xs",
                            style={"width": "85px"},
                        ),
                    ], gap=8),
                    dmc.Group([
                        dmc.Text("TypeSafe", size="xs", c="dimmed", style={"fontFamily": "'JetBrains Mono', monospace", "fontSize": "10px"}),
                        dmc.ActionIcon(
                            id={"type": "q-delete-btn", "index": q.id or q.name},
                            children=DashIconify(icon="tabler:x", width=13, color="#94a3b8"),
                            variant="subtle",
                            color="gray",
                            size="xs",
                        ),
                    ], gap=8),
                ]
            ),

            # Instructions text
            dmc.Text(q.instructions, className="question-prompt"),

            # Metric target
            dmc.Text(
                "Noul: P(yes)" if type_val == "noul" else ("Score: Rubric" if is_score else "Choice: P(distribution)"),
                size="xs",
                c="#64748b",
                fw=500,
                style={"marginBottom": "6px", "fontFamily": "'JetBrains Mono', monospace"},
            ),

            # If choice question, render discrete options
            html.Div(choice_pills, style={"marginBottom": "8px"}) if choice_pills else html.Div(),

            # Bottom controls row
            html.Div(
                className="card-footer-controls",
                children=[
                    dmc.Checkbox(
                        id={"type": "q-required-check", "index": q.id},
                        label="required check",
                        checked=q.required,
                        size="xs",
                        color="gray",
                    ),
                    dmc.Group([
                        dmc.Text("pass if", size="xs", c="dimmed"),
                        dmc.Select(
                            id={"type": "q-pass-cond", "index": q.id},
                            data=[
                                {"value": "true", "label": "true"},
                                {"value": "false", "label": "false"},
                            ] if not is_choice else [
                                {"value": c, "label": c} for c in (q.choices or [])
                            ],
                            value=pass_cond_val if not is_choice else (q.pass_choice or "none / within_tolerance"),
                            size="xs",
                            style={"width": "140px"},
                        ),
                    ], gap=6),
                    dmc.Checkbox(
                        id={"type": "q-needs-record", "index": q.id},
                        label="needs record",
                        checked=q.needs_record,
                        size="xs",
                        color="gray",
                    ),
                ]
            ),
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

