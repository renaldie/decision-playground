"""
Top Header Component.
Features compact comparison selectors for up to 4 models with predefined dropdowns,
distinct identity colors, clickable GPU VRAM residency indicators, a threshold slider, and Run action.
"""
from typing import List, Dict, Any
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify
from src.evaluator import get_model_color
from src.config import get_available_models, get_default_model


def render_model_selector_slot(
    index: int,
    default_model: str = None,
    checked: bool = False,
    is_on_gpu: bool = False,
    available_models: List[str] = None,
):
    """Renders a single compact model selector slot with checkbox, dot, dropdown, and GPU badge."""
    models_list = available_models if available_models is not None else get_available_models()
    color = get_model_color(default_model, index)
    check_id = f"model-toggle-{index}"
    select_id = f"model-select-{index}"
    dot_id = f"model-dot-{index}"
    gpu_btn_id = f"gpu-load-btn-{index}"
    slot_id = f"model-slot-{index}"

    # Prepend -Model- placeholder option so it is visible in the dropdown list and as placeholder
    dropdown_data = [{"value": "", "label": "-Model-"}] + [{"value": m, "label": m} for m in models_list]

    return html.Div(
        id=slot_id,
        className=f"model-slot-pill {'active' if checked else ''}",
        children=[
            # Color dot indicator
            html.Span(
                id=dot_id,
                className="dot-indicator",
                style={"backgroundColor": color, "boxShadow": f"0 0 6px {color}88"}
            ),
            # Checkbox to toggle model for comparison run
            dmc.Checkbox(
                id=check_id,
                checked=checked,
                size="xs",
                color="gray",
                styles={"input": {"cursor": "pointer"}},
            ),
            # Dropdown selector for the model name with placeholder
            dmc.Select(
                id=select_id,
                data=dropdown_data,
                value=default_model or "",
                placeholder="-Model-",
                size="xs",
                allowDeselect=True,
                clearable=True,
                style={"width": "115px"},
                styles={
                    # Make the -Model- placeholder value look white (not dimmed)
                    "input": {"color": "#ffffff" if not default_model else None},
                },
            ),
            # GPU Residency Indicator (Clickable to trigger preloading into VRAM)
            html.Div(
                id=gpu_btn_id,
                title="Ready — model is resident on GPU" if is_on_gpu else ("Click to load model into GPU memory" if default_model else "Select a model first"),
                children=[
                    html.Span("●" if is_on_gpu else "○", style={"marginRight": "2px", "color": "#22c55e" if is_on_gpu else "#64748b"}),
                    html.Span("Ready" if is_on_gpu else "Load"),
                ],
                className="gpu-badge-ready" if is_on_gpu else "gpu-badge-cold",
            ),
        ]
    )


# Backward compatibility alias
def render_model_toggle_pill(model_name: str, index: int, checked: bool, is_on_gpu: bool):
    return render_model_selector_slot(index, model_name, checked, is_on_gpu)


def create_header(
    models: List[str] = None,
    gpu_models: Dict[str, Dict[str, Any]] = None,
    active_indices: List[int] = None,
):
    if gpu_models is None:
        gpu_models = {}

    available_models = get_available_models()
    def_model = get_default_model()

    # Slot 0 defaults to the single chosen model (tev1:0.8b); remaining slots default to -Model-
    primary_model = def_model if def_model in available_models else (available_models[0] if available_models else None)
    slot_models = [primary_model, None, None, None]
    if models and len(models) >= 1:
        for idx, m in enumerate(models[:4]):
            if m in available_models:
                slot_models[idx] = m

    if active_indices is None:
        active_indices = [0] if slot_models[0] is not None else []

    slots = [
        render_model_selector_slot(
            index=i,
            default_model=slot_models[i],
            checked=(i in active_indices and slot_models[i] is not None),
            is_on_gpu=(bool(slot_models[i]) and slot_models[i] in gpu_models),
            available_models=available_models,
        )
        for i in range(4)
    ]
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

            # Right: 4-Model Comparison Grid and Run control
            dmc.Group([
                # 4-Model Comparison Grid in 2 compact rows
                html.Div(
                    id="header-models-grid",
                    className="models-grid-2x2",
                    children=slots,
                ),

                # Run button.
                html.Div(
                    style={"display": "flex", "alignItems": "stretch", "minWidth": "140px", "height": "64px"},
                    children=[
                        dmc.Button(
                            id="run-button",
                            children="Run",
                            leftSection=DashIconify(icon="tabler:player-play-filled", width=14, color="#94a3b8"),
                            variant="filled",
                            size="xs",
                            radius="xs",
                            style={
                                "fontWeight": 700,
                                "fontSize": "14px",
                                "height": "100%",
                                "minHeight": "100%",
                                "width": "100%",
                                "backgroundColor": "#19202c",
                                "color": "#ffffff",
                                "border": "1px solid #2a3142",
                                "padding": "0 12px",
                            },
                        ),
                    ]
                ),
            ], gap="md"),
        ]
    )
