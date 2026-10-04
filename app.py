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
from typing import Dict, List, Optional, Any
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
    get_cross_referenced_models,
    is_ollama_online,
)
from components.header import create_header
from components.panel_state import create_state_panel
from components.panel_questions import create_questions_panel, render_question_card
from components.panel_decisions import create_decisions_panel, render_decisions_content
from components.tab_inference import (
    create_inference,
    render_results_table_rows,
    get_dataset_results_headers,
)
from components.tab_batch import create_batch_tab, render_batch_results
from components.add_question_modal import create_add_question_modal
from components.edit_question_modal import create_edit_question_modal


# Query cross-referenced Ollama models (config.yaml intersected with ollama list)
available_models = get_cross_referenced_models()

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
        dcc.Store(id="installed-models-store", data=available_models),
        dcc.Store(id="inference-dataset-store", data=None),
        dcc.Store(id="inference-results-store", data=None),
        dcc.Store(id="inspect-panels-state", data={"state_collapsed": False, "questions_collapsed": False, "decisions_collapsed": False, "maximized": None}),
        dcc.Clipboard(id="clipboard-helper"),

        # Mantine UI Provider
        dmc.MantineProvider(
            forceColorScheme="dark",
            children=[
                # Top Header
                create_header(),

                # Add Question Modal
                create_add_question_modal(),

                # Edit Question Modal
                create_edit_question_modal(),

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
                                create_decisions_panel(available_models=available_models),
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
                                        installed_models=[{"name": m} for m in available_models],
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


# 2. Dynamic checkboxes synced with cross-referenced models
@app.callback(
    Output("decisions-model-checkboxes", "children"),
    Input("installed-models-store", "data"),
)
def sync_decisions_models_options(installed_models):
    models = installed_models or get_cross_referenced_models()
    return [
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
        for m in models
    ]


# 3. Model Dropdown Label: updates dropdown box text ('1 model', '2 model', etc.) when selections change
@app.callback(
    Output("models-dropdown-btn", "children"),
    Input("decisions-model-select", "value"),
)
def update_models_dropdown_label(selected_models):
    count = len(selected_models) if selected_models else 0
    if count == 0:
        return "0 model"
    return f"{count} model(s)"


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
    updated = [q for q in current_data if q.get("id") != q_id_to_delete and q.get("name") != q_id_to_delete]
    return updated


# 10b. Update Question Primitive Type (Noul / Choice / Score)
@app.callback(
    Output("active-questions-store", "data", allow_duplicate=True),
    Input({"type": "q-type-select", "index": ALL}, "value"),
    State("active-questions-store", "data"),
    prevent_initial_call=True,
)
def handle_question_type_change(values, current_data):
    if not ctx.triggered_id or not isinstance(ctx.triggered_id, dict):
        return no_update
    if ctx.triggered_id.get("type") != "q-type-select":
        return no_update

    target_id = ctx.triggered_id.get("index")
    new_type = None
    for trig in ctx.triggered:
        prop_id = trig.get("prop_id", "")
        if "q-type-select" in prop_id:
            new_type = trig.get("value")
            break

    if not new_type or not target_id or not current_data:
        return no_update

    new_type = str(new_type).lower()
    updated = []
    changed = False

    for item in current_data:
        q_dict = dict(item)
        qid = q_dict.get("id") or q_dict.get("name")
        qname = q_dict.get("name")
        if qid == target_id or qname == target_id:
            if q_dict.get("type") != new_type:
                q_dict["type"] = new_type
                changed = True
                if new_type == "noul":
                    old_crit = q_dict.get("criteria")
                    if not (isinstance(old_crit, dict) and "true" in old_crit and "false" in old_crit):
                        q_dict["criteria"] = {
                            "true": "Target condition or spec is strictly met with zero defects.",
                            "false": "Target condition failed, spec missed, or non-conformance occurred."
                        }
                    q_dict["choices"] = []
                elif new_type == "choice":
                    old_crit = q_dict.get("criteria")
                    if not (isinstance(old_crit, dict) and "true" not in old_crit and len(old_crit) >= 2):
                        q_dict["criteria"] = {
                            "none": "Within nominal tolerance, no defect detected.",
                            "defect": "Defect or non-conformance detected.",
                            "quarantine": "Critical parameter excursion or stoppage."
                        }
                    q_dict["choices"] = list(q_dict["criteria"].keys())
                elif new_type == "score":
                    old_crit = q_dict.get("criteria")
                    if not (isinstance(old_crit, list) and len(old_crit) >= 2):
                        q_dict["criteria"] = [
                            "Level 0: Nominal continuous run within control envelope.",
                            "Level 1: Minor nuisance alert cleared rapidly with zero scrap.",
                            "Level 2: Moderate excursion with line pause or partial hold.",
                            "Level 3: Critical equipment breakdown or complete scrap event."
                        ]
                    q_dict["choices"] = []
        updated.append(q_dict)

    if not changed:
        return no_update

    return updated


# 10c. Handle Question Template Switcher
@app.callback(
    Output("active-questions-store", "data", allow_duplicate=True),
    Input("question-template-select", "value"),
    prevent_initial_call=True,
)
def handle_template_selection(template_val):
    if not template_val:
        return no_update
    if template_val == "manufacturing_gates":
        from src.presets import DATASET_JSON_PATH
        fresh_dataset = DecisionDataset.from_json(str(DATASET_JSON_PATH))
        return [q.to_dict() for q in fresh_dataset.questions]
    elif template_val == "custom":
        from src.presets import get_template_dataset
        tmpl = get_template_dataset()
        return [q.to_dict() for q in tmpl.questions]
    return no_update


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
            pass_condition=True,
            pass_choice=choices_list[0] if (choices_list and q_type == "choice") else None,
        )
        updated = list(current_data) + [new_q.to_dict()]
        return False, updated, "", "", ""

    return no_update, no_update, no_update, no_update, no_update


# Helper criteria parsers for on-the-fly question edits
def parse_choice_criteria(text: str) -> Dict[str, str]:
    result = {}
    lines = [l.strip() for l in (text or "").strip().splitlines() if l.strip()]
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            k = parts[0].strip()
            v = parts[1].strip()
            if k:
                result[k] = v or k
        elif "," in line:
            for item in line.split(","):
                item = item.strip()
                if item:
                    result[item] = item
        else:
            result[line] = line
    return result if result else {"none": "Within nominal tolerance", "defect": "Defect detected"}


def parse_score_criteria(text: str) -> List[str]:
    lines = [l.strip() for l in (text or "").strip().splitlines() if l.strip()]
    cleaned = []
    for l in lines:
        import re
        l_clean = re.sub(r"^(?:Level\s*\d+|L\d+|\d+)[:\s.-]+", "", l, flags=re.IGNORECASE).strip()
        cleaned.append(l_clean if l_clean else l)
    return cleaned if len(cleaned) >= 2 else ["Level 0: Nominal", "Level 1: Minor", "Level 2: Severe", "Level 3: Critical"]


# 11b. Edit Question Modal: Toggle Criteria Fields by Primitive Type
@app.callback(
    Output("edit-q-noul-container", "style"),
    Output("edit-q-choice-container", "style"),
    Output("edit-q-score-container", "style"),
    Input("edit-q-type", "value"),
)
def toggle_edit_criteria_fields(q_type):
    t = str(q_type or "noul").lower()
    if t == "choice":
        return {"display": "none"}, {"display": "block"}, {"display": "none"}
    elif t == "score":
        return {"display": "none"}, {"display": "none"}, {"display": "block"}
    return {"display": "block"}, {"display": "none"}, {"display": "none"}


# 11c. Edit Question Modal: Open & Populate Fields from Selected Question
@app.callback(
    Output("edit-question-modal", "opened"),
    Output("editing-question-id-store", "data"),
    Output("edit-q-name", "value"),
    Output("edit-q-type", "value"),
    Output("edit-q-instructions", "value"),
    Output("edit-q-noul-true", "value"),
    Output("edit-q-noul-false", "value"),
    Output("edit-q-choice-text", "value"),
    Output("edit-q-score-text", "value"),
    Input({"type": "q-edit-btn", "index": ALL}, "n_clicks"),
    Input("cancel-edit-q-btn", "n_clicks"),
    State("active-questions-store", "data"),
    prevent_initial_call=True,
)
def open_edit_question_modal(edit_clicks_list, cancel_clicks, current_data):
    button_id = ctx.triggered_id
    if button_id == "cancel-edit-q-btn":
        return False, "", "", "noul", "", "", "", "", ""

    if not any(c for c in edit_clicks_list if c):
        return no_update

    if not button_id or not isinstance(button_id, dict):
        return no_update

    target_key = button_id.get("index")
    if not target_key or not current_data:
        return no_update

    found = None
    for item in current_data:
        qid = item.get("id") or item.get("name")
        qname = item.get("name")
        if qid == target_key or qname == target_key:
            found = item
            break

    if not found:
        return no_update

    q_name = found.get("name", "")
    q_type = str(found.get("type", "noul")).lower()
    q_instructions = found.get("instructions") or found.get("prompt") or ""
    crit = found.get("criteria")

    noul_true = ""
    noul_false = ""
    choice_text = ""
    score_text = ""

    if q_type == "choice":
        if isinstance(crit, dict):
            choice_text = "\n".join(f"{k}: {v}" for k, v in crit.items())
        elif isinstance(crit, list):
            choice_text = "\n".join(str(c) for c in crit)
        elif found.get("choices"):
            choice_text = "\n".join(str(c) for c in found["choices"])
    elif q_type == "score":
        if isinstance(crit, list):
            score_text = "\n".join(str(l) for l in crit)
        elif isinstance(crit, dict):
            score_text = "\n".join(f"{k}: {v}" for k, v in crit.items())
    else:  # noul
        if isinstance(crit, dict):
            noul_true = crit.get("true", "")
            noul_false = crit.get("false", "")

    return True, target_key, q_name, q_type, q_instructions, noul_true, noul_false, choice_text, score_text


# 11d. Edit Question Modal: Save Changes to Store
@app.callback(
    Output("edit-question-modal", "opened", allow_duplicate=True),
    Output("active-questions-store", "data", allow_duplicate=True),
    Input("save-edit-q-btn", "n_clicks"),
    State("editing-question-id-store", "data"),
    State("edit-q-name", "value"),
    State("edit-q-type", "value"),
    State("edit-q-instructions", "value"),
    State("edit-q-noul-true", "value"),
    State("edit-q-noul-false", "value"),
    State("edit-q-choice-text", "value"),
    State("edit-q-score-text", "value"),
    State("active-questions-store", "data"),
    prevent_initial_call=True,
)
def save_question_edits(
    n_clicks,
    target_id,
    new_name,
    new_type,
    new_instructions,
    noul_true,
    noul_false,
    choice_text,
    score_text,
    current_data,
):
    if not n_clicks or not target_id or not current_data:
        return no_update

    clean_name = (new_name or "").strip()
    clean_instructions = (new_instructions or "").strip()
    clean_type = str(new_type or "noul").lower()

    if not clean_name or not clean_instructions:
        return no_update

    if clean_type == "choice":
        criteria = parse_choice_criteria(choice_text)
        choices = list(criteria.keys())
    elif clean_type == "score":
        criteria = parse_score_criteria(score_text)
        choices = []
    else:  # noul
        criteria = {
            "true": (noul_true or "").strip() or "Target condition or spec is strictly met with zero defects.",
            "false": (noul_false or "").strip() or "Target condition failed, spec missed, or non-conformance occurred.",
        }
        choices = []

    updated = []
    found_match = False

    for item in current_data:
        q_dict = dict(item)
        qid = q_dict.get("id") or q_dict.get("name")
        qname = q_dict.get("name")
        if qid == target_id or qname == target_id:
            q_dict["name"] = clean_name
            q_dict["id"] = clean_name
            q_dict["type"] = clean_type
            q_dict["instructions"] = clean_instructions
            q_dict["prompt"] = clean_instructions
            q_dict["criteria"] = criteria
            q_dict["choices"] = choices
            found_match = True
        updated.append(q_dict)

    if not found_match:
        return False, no_update

    return False, updated


# 12. Run Decision Evaluation Callback (Supports selected models from decisions panel)
@app.callback(
    Output("decisions-panel-content", "children"),
    Output("runs-history-store", "data"),
    Output("latest-results-store", "data"),
    Input("run-button", "n_clicks"),
    State("document-text-input", "value"),
    State("active-questions-store", "data"),
    State("decisions-model-select", "value"),
    State("runs-history-store", "data"),
    State("preset-document-select", "value"),
    State("inspect-panels-state", "data"),
    prevent_initial_call=True,
)
def run_inspection(
    n_clicks,
    text,
    questions_data,
    selected_models,
    history_data,
    preset_id,
    panels_state,
):
    if not n_clicks:
        return no_update, no_update, no_update

    threshold = get_default_threshold()
    models = selected_models or []
    if not models:
        empty_warning = html.Div(
            dmc.Alert("Please select at least one active model in the decisions model selector.", color="red", title="No Model Active")
        )
        return empty_warning, no_update, no_update

    if not text or not text.strip():
        empty_warning = html.Div(
            dmc.Alert("Process log text is empty. Please select or paste a log to inspect.", color="yellow", title="Empty Text")
        )
        return empty_warning, no_update, no_update

    try:
        q_objs = [DecisionQuestion.from_dict(d) for d in questions_data]
        results = [run_model_inference(m_name, text, q_objs, float(threshold), model_index=slot_idx) for slot_idx, m_name in enumerate(models)]
        active_models = list(models)

        is_max = bool(panels_state and (panels_state.get("maximized") == "decisions" or (panels_state.get("state_collapsed") and panels_state.get("questions_collapsed"))))
        rendered_decisions = render_decisions_content(
            results,
            float(threshold),
            is_maximized=is_max,
        )
    except Exception as exc:
        err_warning = html.Div(
            dmc.Alert(f"Inference execution failed: {exc}", color="red", title="Inference Error")
        )
        return err_warning, no_update, no_update

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

    return rendered_decisions, updated_history, results_serialized





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
