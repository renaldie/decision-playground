"""
Top Header Component.
Features application branding and mode selector tabs.
"""
from typing import List, Dict, Any, Optional
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify


def create_header(*args, **kwargs):
    """
    Renders top application header with logo/title and navigation mode tabs.
    """
    return html.Div(
        className="top-header",
        children=[
            # Left: Title and 4 Mode Tabs compacted into 2 rows, aligned to the left
            html.Div(
                style={"display": "flex", "flexDirection": "column", "gap": "4px", "alignItems": "flex-start"},
                children=[
                    # Row 1: Logo Icon + "Decision Playground"
                    dmc.Group([
                        dmc.ThemeIcon(
                            DashIconify(icon="tabler:cpu", width=16, color="#94a3b8"),
                            variant="subtle",
                            color="gray",
                            size="sm",
                        ),
                        dmc.Text(
                            "Decision Playground",
                            fw=700,
                            size="sm",
                            c="white",
                            style={"letterSpacing": "-0.01em", "lineHeight": "1.2"},
                        ),
                    ], gap="xs"),

                    # Row 2: 4 Mode Tabs
                    dmc.SegmentedControl(
                        id="main-mode-selector",
                        value="compare",
                        data=[
                            {"label": "Compare", "value": "compare"},
                            {"label": "Inference", "value": "inference"},
                            {"label": "Batch", "value": "batch"},
                            {"label": "Logs", "value": "logs"},
                        ],
                        size="xs",
                        radius="xs",
                        color="gray",
                        styles={
                            "root": {"backgroundColor": "#090a0f", "border": "1px solid #1f2430", "padding": "1px"},
                            "control": {"fontSize": "11px", "padding": "2px 8px"},
                        },
                    ),
                ]
            ),
        ]
    )


# Backward compatibility stubs
def render_model_selector_slot(*args, **kwargs):
    return html.Div(style={"display": "none"})


def render_model_toggle_pill(*args, **kwargs):
    return html.Div(style={"display": "none"})
