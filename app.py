"""
Decision Playground - Main Application
A model playground to inspect, evaluate, and benchmark Ollama decision models (tev1:0.8b, tev1:4b, etc.)
on industrial manufacturing process data.
"""
import datetime
import io
import base64
import json
import csv
import dash
from dash import html, dcc, Input, Output, State, ALL, ctx, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from src.types import DecisionQuestion, DatasetRecord, DecisionDataset, QuestionType, PassCondition
from src.presets import (
    PRESET_SNIPPETS,
    DEFAULT_MANUFACTURING_QUESTIONS,
    get_preset_by_id,
    get_template_dataset,
)
from src.evaluator import run_model_inference, get_model_color
from src.benchmark import run_batch_evaluation
from src.config import get_available_models, get_default_model, get_default_threshold, get_ollama_settings
from src.logger import log_run
from src.ollama_client import (
    get_installed_models,
    get_gpu_loaded_models,
    load_model_to_gpu,
    stop_model_on_gpu,
    is_ollama_online,
)
from components.header import create_header, render_model_toggle_pill
from components.panel_state import create_state_panel
from components.panel_questions import create_questions_panel, render_question_card
from components.panel_decisions import create_decisions_panel, render_decisions_content
from components.tab_inference import (
    create_inference,
    render_results_table_rows,
    get_dataset_results_headers,
)
from components.tab_batch import create_batch_tab, render_batch_results
from components.tab_logs import create_runs_tab
from components.add_question_modal import create_add_question_modal


# Query installed Ollama models
installed_models_data = get_installed_models()
installed_model_names = [m["name"] for m in installed_models_data] if installed_models_data else get_available_models()
gpu_models_map = get_gpu_loaded_models()

app = dash.Dash(
    __name__,
    title="Decision Playground",
    update_title=None,
    suppress_callback_exceptions=True,
)

initial_questions = [q.to_dict() for q in DEFAULT_MANUFACTURING_QUESTIONS]

app.layout = html.Div(
    id="app-root",
    children=[
        # Stores & Helpers
        dcc.Store(id="active-questions-store", data=initial_questions),
        dcc.Store(id="runs-history-store", data=[]),
        dcc.Store(id="latest-results-store", data=None),
        dcc.Store(id="installed-models-store", data=installed_model_names),
        dcc.Store(id="gpu-models-store", data=gpu_models_map),
        dcc.Store(id="inference-dataset-store", data=None),
        dcc.Store(id="inference-results-store", data=None),
        dcc.Store(id="inspect-panels-state", data={"state_collapsed": False, "questions_collapsed": False, "decisions_collapsed": False, "maximized": None}),
        dcc.Store(id="prev-model-values-store", data={"0": None, "1": None, "2": None, "3": None}),
        dcc.Clipboard(id="clipboard-helper"),

        # Periodic interval to check GPU status
        dcc.Interval(id="gpu-poll-interval", interval=10000, n_intervals=0),

        # Mantine UI Provider
        dmc.MantineProvider(
            forceColorScheme="dark",
            children=[
                # Top Header (Compact 2-Row 4-Model Dropdown Header)
                create_header(
                    gpu_models=gpu_models_map,
                    active_indices=[0],
                ),

                # Add Question Modal
                create_add_question_modal(),

                # Main Views Container
                html.Div(
                    id="views-wrapper",
                    children=[
                        # View 1: Compare Workbench (3 Columns)
                        html.Div(
                            id="inspect-view",
                            className="workbench-container",
                            style={"display": "flex"},
                            children=[
                                create_state_panel(),
                                create_questions_panel(DEFAULT_MANUFACTURING_QUESTIONS),
                                create_decisions_panel(),
                            ]
                        ),

                        # View 2: Dedicated Single Model Inference
                        html.Div(
                            id="inference-view",
                            style={"display": "none"},
                            children=[
                                html.Div(
                                    id="inference-content",
                                    children=create_inference(
                                        installed_models=[{"name": m} for m in installed_model_names],
                                        selected_model=get_default_model(),
                                        dataset_records=None,
                                        evaluation_results=None,
                                        questions=DEFAULT_MANUFACTURING_QUESTIONS,
                                    ),
                                )
                            ]
                        ),

                        # View 3: Batch Tab Container
                        html.Div(
                            id="batch-view",
                            style={"display": "none"},
                            children=[
                                html.Div(id="batch-view-content")
                            ]
                        ),

                        # View 4: Logs Tab Container
                        html.Div(
                            id="runs-view",
                            style={"display": "none"},
                            children=[
                                html.Div(id="runs-view-content")
                            ]
                        ),
                    ]
                ),
            ]
        ),
    ]
)


# -------------------------------------------------------------------------
# CALLBACKS
# -------------------------------------------------------------------------

# 1. Mode Switcher (Compare / Inference / Batch / Logs)
@app.callback(
    Output("inspect-view", "style"),
    Output("inference-view", "style"),
    Output("batch-view", "style"),
    Output("runs-view", "style"),
    Output("inference-content", "children"),
    Output("batch-view-content", "children"),
    Output("runs-view-content", "children"),
    Input("main-mode-selector", "value"),
    State("runs-history-store", "data"),
    State("installed-models-store", "data"),
    State("inference-dataset-store", "data"),
    State("inference-results-store", "data"),
    State("active-questions-store", "data"),
    State("inference-model-select", "value"),
)
def switch_view(
    mode,
    run_history,
    installed_models,
    dataset_records,
    single_results,
    active_questions_data,
    selected_inference_model,
):
    models = get_available_models()

    if mode == "inference":
        return (
            {"display": "none"},
            {"display": "block"},
            {"display": "none"},
            {"display": "none"},
            create_inference(
                installed_models=[{"name": model} for model in (installed_models or [])],
                selected_model=selected_inference_model,
                dataset_records=dataset_records,
                evaluation_results=single_results,
                questions=active_questions_data,
            ),
            no_update,
            no_update,
        )
    elif mode == "batch":
        return (
            {"display": "none"},
            {"display": "none"},
            {"display": "block"},
            {"display": "none"},
            no_update,
            create_batch_tab(get_default_threshold(), models[:2]),
            no_update,
        )
    elif mode == "logs":
        return (
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            {"display": "block"},
            no_update,
            no_update,
            create_runs_tab(run_history or []),
        )
    else:  # compare
        return (
            {"display": "flex"},
            {"display": "none"},
            {"display": "none"},
            {"display": "none"},
            no_update,
            no_update,
            no_update,
        )


# 2. Check GPU Status and Poll
@app.callback(
    Output("gpu-models-store", "data"),
    Input("gpu-poll-interval", "n_intervals"),
)
def poll_gpu_status(n):
    return get_gpu_loaded_models()


# 3. Model Preloading / Warm-up to GPU on Click
@app.callback(
    Output("gpu-models-store", "data", allow_duplicate=True),
    Input("gpu-load-btn-0", "n_clicks"),
    Input("gpu-load-btn-1", "n_clicks"),
    Input("gpu-load-btn-2", "n_clicks"),
    Input("gpu-load-btn-3", "n_clicks"),
    State("model-select-0", "value"),
    State("model-select-1", "value"),
    State("model-select-2", "value"),
    State("model-select-3", "value"),
    prevent_initial_call=True,
)
def handle_gpu_preload(btn0, btn1, btn2, btn3, m0, m1, m2, m3):
    triggered = ctx.triggered_id
    if not triggered:
        return no_update

    idx = 0
    for i in range(4):
        if str(i) in str(triggered):
            idx = i
            break

    slot_models = [m0, m1, m2, m3]
    if idx < len(slot_models) and slot_models[idx]:
        target_model = slot_models[idx]
        load_model_to_gpu(target_model)
        return get_gpu_loaded_models()
    return no_update


# 3a. Stop model when its slot is cleared (X clicked on Select)
@app.callback(
    Output("gpu-models-store", "data", allow_duplicate=True),
    Output("prev-model-values-store", "data"),
    Input("model-select-0", "value"),
    Input("model-select-1", "value"),
    Input("model-select-2", "value"),
    Input("model-select-3", "value"),
    State("prev-model-values-store", "data"),
    prevent_initial_call=True,
)
def handle_model_select_change(m0, m1, m2, m3, prev_data):
    prev = prev_data or {"0": None, "1": None, "2": None, "3": None}
    current = {"0": m0 or None, "1": m1 or None, "2": m2 or None, "3": m3 or None}
    stopped_any = False
    for idx, (cur_val, prev_val) in enumerate(zip([m0, m1, m2, m3], [prev.get("0"), prev.get("1"), prev.get("2"), prev.get("3")])):
        # Slot was cleared (X clicked): cur is None/empty, prev had a model
        if not cur_val and prev_val:
            stop_model_on_gpu(prev_val)
            stopped_any = True
    new_prev = {"0": m0 or None, "1": m1 or None, "2": m2 or None, "3": m3 or None}
    gpu_map = get_gpu_loaded_models() if stopped_any else no_update
    return gpu_map, new_prev


# 3b. Show loading animation on the badge while GPU preload is in progress
@app.callback(
    Output("gpu-load-btn-0", "children", allow_duplicate=True), Output("gpu-load-btn-0", "className", allow_duplicate=True),
    Output("gpu-load-btn-1", "children", allow_duplicate=True), Output("gpu-load-btn-1", "className", allow_duplicate=True),
    Output("gpu-load-btn-2", "children", allow_duplicate=True), Output("gpu-load-btn-2", "className", allow_duplicate=True),
    Output("gpu-load-btn-3", "children", allow_duplicate=True), Output("gpu-load-btn-3", "className", allow_duplicate=True),
    Input("gpu-load-btn-0", "n_clicks"),
    Input("gpu-load-btn-1", "n_clicks"),
    Input("gpu-load-btn-2", "n_clicks"),
    Input("gpu-load-btn-3", "n_clicks"),
    State("model-select-0", "value"),
    State("model-select-1", "value"),
    State("model-select-2", "value"),
    State("model-select-3", "value"),
    prevent_initial_call=True,
)
def show_loading_badge(btn0, btn1, btn2, btn3, m0, m1, m2, m3):
    """Immediately marks the clicked badge as 'Loading…' with shimmer animation before actual load completes."""
    triggered = ctx.triggered_id
    if not triggered:
        return (no_update,) * 8

    idx = 0
    for i in range(4):
        if str(i) in str(triggered):
            idx = i
            break

    slot_models = [m0, m1, m2, m3]
    target = slot_models[idx] if idx < len(slot_models) else None
    if not target:
        return (no_update,) * 8

    loading_children = [
        html.Span("◔", style={"marginRight": "2px", "color": "#f59e0b"}),
        html.Span("Loading…"),
    ]
    out = [no_update] * 8
    out[idx * 2] = loading_children
    out[idx * 2 + 1] = "gpu-badge-loading"
    return tuple(out)


# 4. Dynamic GPU Status Badges on Poll or Model Change
@app.callback(
    Output("gpu-load-btn-0", "children"), Output("gpu-load-btn-0", "className"), Output("gpu-load-btn-0", "title"),
    Output("gpu-load-btn-1", "children"), Output("gpu-load-btn-1", "className"), Output("gpu-load-btn-1", "title"),
    Output("gpu-load-btn-2", "children"), Output("gpu-load-btn-2", "className"), Output("gpu-load-btn-2", "title"),
    Output("gpu-load-btn-3", "children"), Output("gpu-load-btn-3", "className"), Output("gpu-load-btn-3", "title"),
    Input("gpu-models-store", "data"),
    Input("model-select-0", "value"),
    Input("model-select-1", "value"),
    Input("model-select-2", "value"),
    Input("model-select-3", "value"),
)
def update_gpu_badges(gpu_models, m0, m1, m2, m3):
    gpu_map = gpu_models or {}
    results = []
    for m in [m0, m1, m2, m3]:
        is_on = bool(m and (m in gpu_map or any(m in k for k in gpu_map.keys())))
        children = [
            html.Span("●" if is_on else "○", style={"marginRight": "2px", "color": "#22c55e" if is_on else "#64748b"}),
            html.Span("Ready" if is_on else "Load"),
        ]
        cls_name = "gpu-badge-ready" if is_on else "gpu-badge-cold"
        title = f"{m} is resident on GPU — Ready" if is_on else f"Click to load {m} into GPU VRAM"
        results.extend([children, cls_name, title])
    return tuple(results)


# 4b. Dynamic Dot Colors based on selected model
@app.callback(
    Output("model-dot-0", "style"),
    Output("model-dot-1", "style"),
    Output("model-dot-2", "style"),
    Output("model-dot-3", "style"),
    Input("model-select-0", "value"),
    Input("model-select-1", "value"),
    Input("model-select-2", "value"),
    Input("model-select-3", "value"),
)
def update_model_dot_colors(m0, m1, m2, m3):
    styles = []
    for idx, m in enumerate([m0, m1, m2, m3]):
        color = get_model_color(m or "", idx)
        styles.append({"backgroundColor": color, "boxShadow": f"0 0 6px {color}88"})
    return tuple(styles)


# 4c. Active Pill Highlighting
@app.callback(
    Output("model-slot-0", "className"),
    Output("model-slot-1", "className"),
    Output("model-slot-2", "className"),
    Output("model-slot-3", "className"),
    Input("model-toggle-0", "checked"),
    Input("model-toggle-1", "checked"),
    Input("model-toggle-2", "checked"),
    Input("model-toggle-3", "checked"),
)
def update_slot_classes(c0, c1, c2, c3):
    return tuple("model-slot-pill active" if c else "model-slot-pill" for c in [c0, c1, c2, c3])


# 4d. Model Indicators Summary (Supports 4 models)
@app.callback(
    Output("active-models-summary", "children"),
    Input("model-toggle-0", "checked"),
    Input("model-toggle-1", "checked"),
    Input("model-toggle-2", "checked"),
    Input("model-toggle-3", "checked"),
)
def update_active_models_header(m0_on, m1_on, m2_on, m3_on):
    active_count = sum(1 for c in [m0_on, m1_on, m2_on, m3_on] if c)
    if active_count == 0:
        return "0 Models Active"
    return f"{active_count} Model{'s' if active_count > 1 else ''} Active"


# 4f. Auto-toggle checkbox when model is selected from -Model- placeholder
@app.callback(
    Output("model-toggle-0", "checked"),
    Input("model-select-0", "value"),
    prevent_initial_call=True,
)
def auto_toggle_m0(val):
    return bool(val)


@app.callback(
    Output("model-toggle-1", "checked"),
    Input("model-select-1", "value"),
    prevent_initial_call=True,
)
def auto_toggle_m1(val):
    return bool(val)


@app.callback(
    Output("model-toggle-2", "checked"),
    Input("model-select-2", "value"),
    prevent_initial_call=True,
)
def auto_toggle_m2(val):
    return bool(val)


@app.callback(
    Output("model-toggle-3", "checked"),
    Input("model-select-3", "value"),
    prevent_initial_call=True,
)
def auto_toggle_m3(val):
    return bool(val)


# 4e. Manage Expandable/Collapsible Workbench Cards
@app.callback(
    Output("inspect-panels-state", "data"),
    Output("state-panel-wrapper", "style"),
    Output("state-panel-card", "style"),
    Output("state-panel-collapsed-strip", "style"),
    Output("questions-panel-wrapper", "style"),
    Output("questions-panel-card", "style"),
    Output("questions-panel-collapsed-strip", "style"),
    Output("decisions-panel-wrapper", "style"),
    Output("decisions-panel-card", "style"),
    Output("decisions-panel-card", "className"),
    Output("decisions-panel-collapsed-strip", "style"),
    Output("btn-maximize-state", "children"),
    Output("btn-maximize-questions", "children"),
    Output("btn-maximize-decisions", "children"),
    Input("btn-collapse-state", "n_clicks"),
    Input("btn-expand-state-strip", "n_clicks"),
    Input("btn-maximize-state", "n_clicks"),
    Input("btn-collapse-questions", "n_clicks"),
    Input("btn-expand-questions-strip", "n_clicks"),
    Input("btn-maximize-questions", "n_clicks"),
    Input("btn-collapse-decisions", "n_clicks"),
    Input("btn-expand-decisions-strip", "n_clicks"),
    Input("btn-maximize-decisions", "n_clicks"),
    State("inspect-panels-state", "data"),
    prevent_initial_call=True,
)
def manage_panel_layouts(
    c_state, e_state, m_state,
    c_q, e_q, m_q,
    c_decisions, e_decisions, m_decisions,
    current_state,
):
    state = dict(current_state or {"state_collapsed": False, "questions_collapsed": False, "decisions_collapsed": False, "maximized": None})
    triggered = ctx.triggered_id
    if not triggered:
        return (no_update,) * 14

    if triggered == "btn-collapse-state":
        state["state_collapsed"] = True
        state["maximized"] = None
    elif triggered == "btn-expand-state-strip":
        state["state_collapsed"] = False
        state["maximized"] = None
    elif triggered == "btn-maximize-state":
        if state.get("maximized") == "state":
            state = {"state_collapsed": False, "questions_collapsed": False, "decisions_collapsed": False, "maximized": None}
        else:
            state = {"state_collapsed": False, "questions_collapsed": True, "decisions_collapsed": True, "maximized": "state"}

    elif triggered == "btn-collapse-questions":
        state["questions_collapsed"] = True
        state["maximized"] = None
    elif triggered == "btn-expand-questions-strip":
        state["questions_collapsed"] = False
        state["maximized"] = None
    elif triggered == "btn-maximize-questions":
        if state.get("maximized") == "questions":
            state = {"state_collapsed": False, "questions_collapsed": False, "decisions_collapsed": False, "maximized": None}
        else:
            state = {"state_collapsed": True, "questions_collapsed": False, "decisions_collapsed": True, "maximized": "questions"}

    elif triggered == "btn-collapse-decisions":
        state["decisions_collapsed"] = True
        state["maximized"] = None
    elif triggered == "btn-expand-decisions-strip":
        state["decisions_collapsed"] = False
        state["maximized"] = None
    elif triggered == "btn-maximize-decisions":
        if state.get("maximized") == "decisions":
            state = {"state_collapsed": False, "questions_collapsed": False, "decisions_collapsed": False, "maximized": None}
        else:
            state = {"state_collapsed": True, "questions_collapsed": True, "decisions_collapsed": False, "maximized": "decisions"}

    # Compute styles based on state
    state_collapsed = state.get("state_collapsed", False)
    state_wrapper_style = {"flex": "0 0 38px", "minWidth": "38px", "width": "38px"} if state_collapsed else (
        {"flex": "1", "minWidth": "0", "width": "100%"} if state.get("maximized") == "state" else {"flex": "1.15", "minWidth": "300px"}
    )
    state_card_style = {"display": "none"} if state_collapsed else {"display": "flex", "height": "100%", "width": "100%"}
    state_ribbon_style = {"display": "flex"} if state_collapsed else {"display": "none"}

    q_collapsed = state.get("questions_collapsed", False)
    q_wrapper_style = {"flex": "0 0 38px", "minWidth": "38px", "width": "38px"} if q_collapsed else (
        {"flex": "1", "minWidth": "0", "width": "100%"} if state.get("maximized") == "questions" else {"flex": "1.25", "minWidth": "320px"}
    )
    q_card_style = {"display": "none"} if q_collapsed else {"display": "flex", "height": "100%", "width": "100%"}
    q_ribbon_style = {"display": "flex"} if q_collapsed else {"display": "none"}

    decisions_collapsed = state.get("decisions_collapsed", False)
    decisions_wrapper_style = {"flex": "0 0 38px", "minWidth": "38px", "width": "38px"} if decisions_collapsed else (
        {"flex": "1", "minWidth": "0", "width": "100%"} if state.get("maximized") == "decisions" else {"flex": "1.75", "minWidth": "380px"}
    )
    decisions_card_style = {"display": "none"} if decisions_collapsed else {"display": "flex", "height": "100%", "width": "100%"}
    decisions_card_class = "panel-card panel-card-maximized" if (state.get("maximized") == "decisions" or (state_collapsed and q_collapsed)) else "panel-card"
    decisions_ribbon_style = {"display": "flex"} if decisions_collapsed else {"display": "none"}

    icon_state = DashIconify(icon="tabler:arrows-minimize" if state.get("maximized") == "state" else "tabler:arrows-maximize", width=14, color="#94a3b8")
    icon_q = DashIconify(icon="tabler:arrows-minimize" if state.get("maximized") == "questions" else "tabler:arrows-maximize", width=14, color="#94a3b8")
    icon_decisions = DashIconify(icon="tabler:arrows-minimize" if state.get("maximized") == "decisions" else "tabler:arrows-maximize", width=14, color="#94a3b8")

    return (
        state,
        state_wrapper_style, state_card_style, state_ribbon_style,
        q_wrapper_style, q_card_style, q_ribbon_style,
        decisions_wrapper_style, decisions_card_style, decisions_card_class, decisions_ribbon_style,
        icon_state, icon_q, icon_decisions,
    )


# 6. Text Metrics (Characters & Token Estimation)
@app.callback(
    Output("input-token-count", "children"),
    Output("input-char-count", "children"),
    Input("document-text-input", "value"),
)
def update_text_metrics(text):
    if not text:
        return "~0 tokens", "0 chars"
    char_count = len(text)
    word_count = len(text.split())
    approx_tokens = int(word_count * 1.35)
    return f"~{approx_tokens} tokens", f"{char_count} chars"


# 7. Preset Snippet Selection
@app.callback(
    Output("document-text-input", "value"),
    Input("preset-document-select", "value"),
    prevent_initial_call=True,
)
def handle_preset_selection(preset_id):
    if not preset_id:
        return no_update
    doc = get_preset_by_id(preset_id)
    return doc.content


# 7e. Batch threshold label
@app.callback(
    Output("batch-threshold-label", "children"),
    Input("batch-threshold-slider", "value"),
)
def update_batch_threshold_label(val):
    return f"Threshold: ≥ {val}%"


# 7f. Run Benchmark on demand
@app.callback(
    Output("batch-results-area", "children"),
    Input("run-batch-btn", "n_clicks"),
    State("batch-model-a-select", "value"),
    State("batch-model-b-select", "value"),
    State("batch-threshold-slider", "value"),
    prevent_initial_call=True,
)
def run_batch_benchmark(n_clicks, model_a, model_b, threshold):
    if not n_clicks:
        return no_update
    from src.benchmark import run_batch_evaluation
    models = list({model_a, model_b}) if model_a and model_b else [model_a or model_b]
    # Ensure m1/m2 order is preserved
    models = [m for m in [model_a, model_b] if m]
    if not models:
        return no_update
    batch_data = run_batch_evaluation(float(threshold or 90), models)
    return render_batch_results(batch_data, float(threshold or 90), models)


# 9. Render Question Cards from Store
@app.callback(
    Output("questions-list-container", "children"),
    Input("active-questions-store", "data"),
)
def update_question_cards(questions_data):
    if not questions_data:
        return html.Div(
            dmc.Text("No decision gates configured. Click '+ Add Check' to add one.", size="xs", c="dimmed", ta="center", mt="xl")
        )
    return [render_question_card(DecisionQuestion.from_dict(d)) for d in questions_data]


# 10. Delete Question Card
@app.callback(
    Output("active-questions-store", "data", allow_duplicate=True),
    Input({"type": "q-delete-btn", "index": ALL}, "n_clicks"),
    State("active-questions-store", "data"),
    prevent_initial_call=True,
)
def delete_question(n_clicks_list, current_data):
    if not any(c for c in n_clicks_list if c):
        return no_update
    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return no_update
    q_id_to_delete = triggered.get("index")
    updated = [q for q in current_data if q.get("id") != q_id_to_delete]
    return updated


# 11. Add Question Modal Open / Close / Submit
@app.callback(
    Output("add-question-modal", "opened"),
    Output("active-questions-store", "data", allow_duplicate=True),
    Output("new-q-name", "value"),
    Output("new-q-prompt", "value"),
    Output("new-q-choices", "value"),
    Input("add-question-btn", "n_clicks"),
    Input("cancel-add-q-btn", "n_clicks"),
    Input("submit-add-q-btn", "n_clicks"),
    State("new-q-name", "value"),
    State("new-q-prompt", "value"),
    State("new-q-type", "value"),
    State("new-q-choices", "value"),
    State("new-q-required", "checked"),
    State("new-q-needs-record", "checked"),
    State("active-questions-store", "data"),
    prevent_initial_call=True,
)
def manage_add_question_modal(
    open_clicks,
    cancel_clicks,
    submit_clicks,
    q_name,
    q_prompt,
    q_type,
    q_choices_str,
    q_required,
    q_needs_record,
    current_data,
):
    button_id = ctx.triggered_id
    if button_id == "add-question-btn":
        return True, no_update, "", "", ""
    elif button_id == "cancel-add-q-btn":
        return False, no_update, "", "", ""
    elif button_id == "submit-add-q-btn":
        if not q_name or not q_prompt:
            return True, no_update, q_name, q_prompt, q_choices_str

        choices_list = [c.strip() for c in q_choices_str.split(",") if c.strip()] if q_choices_str else []
        criteria_val = None
        if q_type == "choice":
            criteria_val = {c: c for c in choices_list} if choices_list else {"none": "Within tolerance", "defect": "Defect detected"}
        elif q_type == "score":
            criteria_val = choices_list if len(choices_list) >= 2 else ["Low", "Medium", "High"]

        new_q = DecisionQuestion(
            id=f"custom_{datetime.datetime.now().strftime('%M%S')}",
            name=q_name.strip(),
            instructions=q_prompt.strip(),
            type=q_type,
            criteria=criteria_val,
            required=bool(q_required),
            pass_condition=True,
            pass_choice=choices_list[0] if (choices_list and q_type == "choice") else None,
        )
        updated = list(current_data) + [new_q.to_dict()]
        return False, updated, "", "", ""

    return no_update, no_update, no_update, no_update, no_update


# 12. Run Decision Evaluation Callback (Supports up to 4 side-by-side models)
@app.callback(
    Output("decisions-panel-content", "children"),
    Output("decisions-status-indicator", "children"),
    Output("runs-history-store", "data"),
    Output("latest-results-store", "data"),
    Input("run-button", "n_clicks"),
    State("document-text-input", "value"),
    State("active-questions-store", "data"),
    State("model-toggle-0", "checked"),
    State("model-toggle-1", "checked"),
    State("model-toggle-2", "checked"),
    State("model-toggle-3", "checked"),
    State("model-select-0", "value"),
    State("model-select-1", "value"),
    State("model-select-2", "value"),
    State("model-select-3", "value"),
    State("runs-history-store", "data"),
    State("preset-document-select", "value"),
    State("inspect-panels-state", "data"),
    prevent_initial_call=True,
)
def run_inspection(
    n_clicks,
    text,
    questions_data,
    m0_on,
    m1_on,
    m2_on,
    m3_on,
    m0_val,
    m1_val,
    m2_val,
    m3_val,
    history_data,
    preset_id,
    panels_state,
):
    if not n_clicks:
        return no_update, no_update, no_update, no_update

    threshold = get_default_threshold()
    active_pairs = []
    for idx, (is_on, m_val) in enumerate([
        (m0_on, m0_val),
        (m1_on, m1_val),
        (m2_on, m2_val),
        (m3_on, m3_val),
    ]):
        if is_on and m_val:
            active_pairs.append((idx, m_val))

    if not active_pairs:
        empty_warning = html.Div(
            dmc.Alert("Please select at least one active model in the header selectors.", color="red", title="No Model Active")
        )
        return empty_warning, "Error: No model active", no_update, no_update

    if not text or not text.strip():
        empty_warning = html.Div(
            dmc.Alert("Process log text is empty. Please select or paste a log to inspect.", color="yellow", title="Empty Text")
        )
        return empty_warning, "Warning: Empty input", no_update, no_update

    q_objs = [DecisionQuestion.from_dict(d) for d in questions_data]
    results = [run_model_inference(m_name, text, q_objs, float(threshold), model_index=slot_idx) for slot_idx, m_name in active_pairs]
    active_models = [m_name for _, m_name in active_pairs]

    # Ground truth mapping: loaded from selected preset
    ground_truth_map = None
    if preset_id:
        doc = get_preset_by_id(preset_id)
        if doc and doc.states:
            ground_truth_map = doc.states

    is_max = bool(panels_state and (panels_state.get("maximized") == "decisions" or (panels_state.get("state_collapsed") and panels_state.get("questions_collapsed"))))
    rendered_decisions = render_decisions_content(
        results,
        float(threshold),
        ground_truth_map=ground_truth_map,
        is_maximized=is_max,
    )

    # Append to run history
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    doc_title = get_preset_by_id(preset_id).title if preset_id else "Custom Process Log"
    all_passed = all(r.overall_passed for r in results)
    avg_latency = sum(r.latency_ms for r in results) / len(results)

    new_record = {
        "timestamp": now_str,
        "doc_title": doc_title,
        "models": active_models,
        "threshold": threshold,
        "overall_passed": all_passed,
        "avg_latency_ms": avg_latency,
    }
    updated_history = list(history_data or []) + [new_record]

    status_text = f"Audit complete at {now_str} ({avg_latency:.0f}ms avg)"
    results_serialized = [r.to_dict() for r in results]

    # Save run execution to ./logs/{date_time}.json in UTC+8
    log_run(
        mode="compare",
        data={
            "document_title": doc_title,
            "threshold": threshold,
            "active_models": active_models,
            "overall_passed": all_passed,
            "avg_latency_ms": avg_latency,
            "input_text": text,
            "questions": [q.to_dict() for q in q_objs],
            "results": results_serialized,
        },
    )

    return rendered_decisions, status_text, updated_history, results_serialized





# 14. Inference: Load Sample Set, Load Template, or Upload File
@app.callback(
    Output("inference-dataset-store", "data"),
    Output("inference-preview-table-container", "children"),
    Output("inference-badge-count", "children"),
    Output("inference-total-count", "children"),
    Output("active-questions-store", "data", allow_duplicate=True),
    Input("load-sample-dataset-btn", "n_clicks"),
    Input("load-template-dataset-btn", "n_clicks"),
    Input("upload-dataset-file", "contents"),
    State("upload-dataset-file", "filename"),
    prevent_initial_call=True,
)
def handle_dataset_source(sample_clicks, template_clicks, file_contents, filename):
    triggered = ctx.triggered_id
    records = []
    new_questions = no_update

    if triggered == "load-sample-dataset-btn":
        records = [
            {"id": f"REC_{i+1:03d}", "title": s.title, "category": s.category, "text": s.content, "states": {}}
            for i, s in enumerate(PRESET_SNIPPETS)
        ]
    elif triggered == "load-template-dataset-btn":
        template_ds = get_template_dataset()
        records = [r.to_dict() for r in template_ds.records]
        new_questions = [q.to_dict() for q in template_ds.questions]
    elif triggered == "upload-dataset-file" and file_contents:
        try:
            content_type, content_string = file_contents.split(",")
            decoded = base64.b64decode(content_string).decode("utf-8")
            if filename.endswith(".json"):
                data = json.loads(decoded)
                if isinstance(data, dict):
                    # Native DecisionDataset JSON format
                    if "questions" in data or "records" in data or "schema_version" in data:
                        parsed_ds = DecisionDataset.from_dict(data)
                        records = [r.to_dict() for r in parsed_ds.records]
                        if parsed_ds.questions:
                            new_questions = [q.to_dict() for q in parsed_ds.questions]
                    else:
                        for k, v in data.items():
                            records.append({
                                "id": str(k),
                                "title": str(k),
                                "category": "JSON",
                                "text": str(v),
                                "states": {},
                            })
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        if isinstance(item, dict):
                            records.append({
                                "id": str(item.get("id", f"UP_{i+1:03d}")),
                                "title": str(item.get("title", f"Uploaded Sample {i+1}")),
                                "category": str(item.get("category", "Uploaded")),
                                "text": str(item.get("text", item.get("content", str(item)))),
                                "states": dict(item.get("states", {})),
                            })
                        else:
                            records.append({
                                "id": f"UP_{i+1:03d}",
                                "title": f"Uploaded Sample {i+1}",
                                "category": "Uploaded",
                                "text": str(item),
                                "states": {},
                            })
            elif filename.endswith(".csv"):
                reader = csv.reader(io.StringIO(decoded))
                rows = list(reader)
                for i, r in enumerate(rows[1:]):
                    txt = " | ".join(r)
                    records.append({
                        "id": f"CSV_{i+1:03d}",
                        "title": r[0] if len(r) > 0 else f"Row {i+1}",
                        "category": "CSV Upload",
                        "text": txt,
                        "states": {},
                    })
            else:
                chunks = decoded.split("---")
                for i, ch in enumerate(chunks):
                    if ch.strip():
                        records.append({
                            "id": f"TXT_{i+1:03d}",
                            "title": f"Snippet #{i+1}",
                            "category": "Text Log",
                            "text": ch.strip(),
                            "states": {},
                        })
        except Exception:
            return no_update, no_update, no_update, no_update, no_update

    if not records:
        return no_update, no_update, no_update, no_update, no_update

    preview_table = dmc.Table(
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
    )
    return records, preview_table, f"{len(records)} Items Loaded", f"{len(records)} Process Logs", new_questions


# 15. Inference: Run Evaluation
@app.callback(
    Output("inference-results-store", "data"),
    Output("inference-dataset-store", "data", allow_duplicate=True),
    Output("inference-results-table-container", "children"),
    Output("inference-pass-rate-text", "children"),
    Output("inference-hold-count-text", "children"),
    Output("inference-speed-text", "children"),
    Output("export-native-json-btn", "disabled"),
    Output("export-decisions-csv-btn", "disabled"),
    Output("inference-eval-status-badge", "children"),
    Input("run-inference-btn", "n_clicks"),
    State("inference-model-select", "value"),
    State("inference-threshold-slider", "value"),
    State("inference-dataset-store", "data"),
    State("active-questions-store", "data"),
    prevent_initial_call=True,
)
def run_single_dataset_eval(
    n_clicks,
    selected_model,
    threshold,
    dataset_records,
    questions_data,
):
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    records = dataset_records or [
        {"id": f"REC_{i+1:03d}", "title": s.title, "category": s.category, "text": s.content, "states": {}}
        for i, s in enumerate(PRESET_SNIPPETS)
    ]
    model = selected_model or get_default_model()
    thresh = float(threshold or get_default_threshold())

    q_objs = [DecisionQuestion.from_dict(d) for d in questions_data] if questions_data else DEFAULT_MANUFACTURING_QUESTIONS

    results = []
    updated_records = []
    for rec in records:
        text = rec.get("text", "")
        res = run_model_inference(model, text, q_objs, thresh)
        eval_map = {e.question_name: e.to_dict() for e in res.evaluations}

        # Populate evaluated state into record
        rec_states = {
            "overall_passed": res.overall_passed,
            "latency_ms": res.latency_ms,
            "model": model,
        }
        for ev in res.evaluations:
            rec_states[ev.question_name] = {
                "passed": ev.passed,
                "p_true": ev.p_true,
                "confidence": ev.confidence,
                "selected_choice": ev.selected_choice,
                "evidence": ev.evidence,
                "rationale": ev.rationale,
            }

        updated_rec = dict(rec)
        updated_rec["states"] = rec_states
        updated_records.append(updated_rec)

        results.append({
            "record_id": rec.get("id"),
            "title": rec.get("title"),
            "overall_passed": res.overall_passed,
            "latency_ms": res.latency_ms,
            "eval_map": eval_map,
        })

    # Render results table using dynamic headers and rows
    table_headers = get_dataset_results_headers(q_objs)
    table_rows = render_results_table_rows(results, q_objs)
    table_comp = dmc.Table(
        striped=True,
        highlightOnHover=True,
        data={
            "head": table_headers,
            "body": table_rows,
        },
    )

    total_count = len(records)
    passed_count = sum(1 for r in results if r.get("overall_passed"))
    pass_rate = round((passed_count / total_count * 100), 1) if total_count else 0.0
    avg_latency = round(sum(r.get("latency_ms", 0) for r in results) / max(1, len(results)), 1)

    # Save run execution to ./logs/{date_time}.json in UTC+8
    log_run(
        mode="inference",
        data={
            "target_model": model,
            "threshold": thresh,
            "total_records": total_count,
            "passed_records": passed_count,
            "pass_rate_percent": pass_rate,
            "avg_latency_ms": avg_latency,
            "results": results,
        },
    )

    return (
        results,
        updated_records,
        table_comp,
        f"{pass_rate}%",
        f"{total_count - passed_count}",
        f"{avg_latency:.0f} ms / log",
        False,  # Enable Native JSON download
        False,  # Enable CSV download
        f"Status: {len(results)} Evaluated",
    )


# 16. Export Single Dataset Results to Native JSON (readable by types.py)
@app.callback(
    Output("download-native-json", "data"),
    Input("export-native-json-btn", "n_clicks"),
    State("inference-dataset-store", "data"),
    State("active-questions-store", "data"),
    prevent_initial_call=True,
)
def export_native_json(n_clicks, dataset_records, questions_data):
    if not n_clicks or not dataset_records:
        return no_update

    q_objs = [DecisionQuestion.from_dict(d) for d in questions_data] if questions_data else DEFAULT_MANUFACTURING_QUESTIONS
    rec_objs = [DatasetRecord.from_dict(r) for r in dataset_records]
    dataset = DecisionDataset(
        name="Process Decision Evaluation Results",
        schema_version="1.0",
        description="Dataset records with user-defined quality gates and evaluated states.",
        questions=q_objs,
        records=rec_objs,
    )
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return dict(
        content=dataset.to_json(indent=2),
        filename=f"process_decision_dataset_{timestamp}.json",
    )


# 17. Export Single Dataset Results to CSV (Original format + States)
@app.callback(
    Output("download-decisions-csv", "data"),
    Input("export-decisions-csv-btn", "n_clicks"),
    State("inference-dataset-store", "data"),
    State("active-questions-store", "data"),
    prevent_initial_call=True,
)
def export_results_to_csv(n_clicks, dataset_records, questions_data):
    if not n_clicks or not dataset_records:
        return no_update

    q_objs = [DecisionQuestion.from_dict(d) for d in questions_data] if questions_data else DEFAULT_MANUFACTURING_QUESTIONS
    rec_objs = [DatasetRecord.from_dict(r) for r in dataset_records]
    dataset = DecisionDataset(
        name="Process Decision Evaluation Results",
        questions=q_objs,
        records=rec_objs,
    )
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return dict(
        content=dataset.to_original_format_with_states_csv(),
        filename=f"process_decision_audit_{timestamp}.csv",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=False)
