"""
State panel component (Left Column).
"""
from collections import defaultdict
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify
from src.presets import PRESET_SNIPPETS


def _build_grouped_options():
    """Groups records by category for the dropdown."""
    groups = defaultdict(list)
    for rec in PRESET_SNIPPETS:
        groups[rec.category].append({"value": rec.id, "label": rec.title})
    return [{"group": cat, "items": items} for cat, items in groups.items()]


def create_state_panel():
    grouped_options = _build_grouped_options()
    initial_id = PRESET_SNIPPETS[0].id if PRESET_SNIPPETS else None
    initial_content = PRESET_SNIPPETS[0].content if PRESET_SNIPPETS else ""

    return html.Div(
        id="state-panel-wrapper",
        className="panel-wrapper",
        style={"flex": "1.15", "minWidth": "300px"},
        children=[
            html.Div(
                id="state-panel-card",
                className="panel-card",
                style={"display": "flex", "height": "100%", "width": "100%"},
                children=[
                    html.Div(
                        className="panel-header",
                        children=[
                            dmc.Group([
                                dmc.Badge("STATE", variant="light", color="gray", size="xs", radius="xs"),
                                dmc.Select(
                                    id="preset-document-select",
                                    placeholder="Select state...",
                                    data=grouped_options,
                                    value=initial_id,
                                    allowDeselect=False,
                                    size="xs",
                                    style={"width": "230px"},
                                    styles={
                                        "option": {
                                            "paddingLeft": "10px",
                                            "fontSize": "11.5px",
                                        },
                                    },
                                ),
                            ], gap="xs"),
                            dmc.Group([
                                dmc.Tooltip(
                                    label="Collapse to side",
                                    children=dmc.ActionIcon(
                                        id="btn-collapse-state",
                                        children=DashIconify(icon="tabler:layout-sidebar-left-collapse", width=14, color="#94a3b8"),
                                        variant="subtle", color="gray", size="xs",
                                    ),
                                ),
                                dmc.Tooltip(
                                    label="Maximize to full screen",
                                    children=dmc.ActionIcon(
                                        id="btn-maximize-state",
                                        children=DashIconify(icon="tabler:arrows-maximize", width=14, color="#94a3b8"),
                                        variant="subtle", color="gray", size="xs",
                                    ),
                                ),
                            ], gap=2),
                        ]
                    ),

                    html.Div(
                        className="panel-body",
                        style={"display": "flex", "flexDirection": "column", "gap": "8px"},
                        children=[
                            dmc.Textarea(
                                id="document-text-input",
                                value=initial_content,
                                className="document-textarea",
                                autosize=False,
                                style={"flex": 1, "height": "100%", "display": "flex", "flexDirection": "column"},
                                styles={
                                    "wrapper": {"height": "100%", "flex": 1, "display": "flex", "flexDirection": "column"},
                                    "input": {"height": "100%", "flex": 1, "minHeight": "480px"},
                                },
                                placeholder="Paste or drop manufacturing process log / run text here...",
                            ),
                            dmc.Group(
                                justify="space-between",
                                children=[
                                    dmc.Group([
                                        dmc.Text(id="input-token-count", size="xs", c="dimmed", children="~124 tokens"),
                                        dmc.Text("·", size="xs", c="dimmed"),
                                        dmc.Text(id="input-char-count", size="xs", c="dimmed", children="682 chars"),
                                    ], gap=6),
                                    dmc.Badge(id="input-format-badge", children="Process Text Mode", variant="outline", color="gray", size="xs"),
                                ]
                            ),
                        ]
                    ),
                ]
            ),

            html.Div(
                id="state-panel-collapsed-strip",
                className="collapsed-ribbon",
                style={"display": "none"},
                title="Click to restore State panel",
                children=[
                    dmc.ActionIcon(
                        id="btn-expand-state-strip",
                        children=DashIconify(icon="tabler:layout-sidebar-left-expand", width=16, color="#94a3b8"),
                        variant="subtle", color="gray", size="xs",
                    ),
                    html.Span("STATE", className="collapsed-ribbon-text"),
                ]
            ),
        ]
    )
