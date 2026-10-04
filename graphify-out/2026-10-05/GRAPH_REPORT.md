# Graph Report - decision-playground  (2026-10-04)

## Corpus Check
- 27 files · ~17,316 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .css 1, .lock 1)

## Summary
- 256 nodes · 558 edges · 16 communities (10 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b17eed20`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- get_available_models
- presets.py
- evaluator.py
- config.py
- panel_decisions.py
- app.py
- ollama_client.py
- dash
- 🌟 Key Features
- benchmark.py
- rules/graphify.md
- workflows/graphify.md
- copilot-instructions.md
- decision-playground
- run_button.js

## God Nodes (most connected - your core abstractions)
1. `DecisionQuestion` - 22 edges
2. `get_available_models()` - 16 edges
3. `get_default_threshold()` - 15 edges
4. `DecisionDataset` - 15 edges
5. `run_model_inference()` - 14 edges
6. `get_default_model()` - 13 edges
7. `DatasetRecord` - 12 edges
8. `create_inference()` - 11 edges
9. `load_config()` - 11 edges
10. `run_single_dataset_eval()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `manage_add_question_modal()` --uses--> `DecisionQuestion`  [INFERRED]
  app.py → src/types.py
- `export_native_json()` --uses--> `DecisionQuestion`  [INFERRED]
  app.py → src/types.py
- `export_results_to_csv()` --uses--> `DecisionQuestion`  [INFERRED]
  app.py → src/types.py
- `render_evaluation_bar()` --uses--> `QuestionEvaluation`  [INFERRED]
  components/panel_decisions.py → src/types.py
- `switch_view()` --calls--> `create_runs_tab()`  [INFERRED]
  app.py → components/tab_logs.py

## Import Cycles
- None detected.

## Communities (16 total, 6 thin omitted)

### Community 0 - "get_available_models"
Cohesion: 0.15
Nodes (8): switch_view(), create_batch_tab(), create_inference(), get_dataset_results_headers(), render_results_table_rows(), create_runs_tab(), get_available_models(), get_default_threshold()

### Community 1 - "presets.py"
Cohesion: 0.10
Nodes (10): export_native_json(), export_results_to_csv(), handle_dataset_source(), handle_template_selection(), get_all_records(), get_preset_by_id(), get_preset_options(), get_template_dataset() (+2 more)

### Community 2 - "evaluator.py"
Cohesion: 0.09
Nodes (14): run_inspection(), run_single_dataset_eval(), update_question_cards(), create_questions_panel(), render_question_card(), render_question_criteria_section(), evaluate_manufacturing_question(), extract_evidence() (+6 more)

### Community 3 - "config.py"
Cohesion: 0.11
Nodes (9): get_config(), get_dataset_paths(), get_log_folder(), get_ollama_settings(), get_timezone_offset_hours(), load_config(), get_utc8_now(), list_recent_logs() (+1 more)

### Community 4 - "panel_decisions.py"
Cohesion: 0.11
Nodes (11): create_decisions_panel(), get_score_gradient(), render_continuous_gradient_meter(), render_decisions_content(), render_empty_decisions(), render_evaluation_bar(), render_model_decision_card(), render_stepped_gradient_meter() (+3 more)

### Community 5 - "app.py"
Cohesion: 0.17
Nodes (16): delete_question(), handle_preset_selection(), handle_question_type_change(), manage_add_question_modal(), manage_panel_layouts(), open_edit_question_modal(), parse_choice_criteria(), parse_score_criteria() (+8 more)

### Community 6 - "ollama_client.py"
Cohesion: 0.10
Nodes (9): get_base_url(), get_gpu_loaded_models(), get_installed_models(), get_ollama_list_models(), is_ollama_online(), load_model_to_gpu(), run_ollama_batch_decision(), run_ollama_decision() (+1 more)

### Community 7 - "dash"
Cohesion: 0.12
Nodes (5): create_add_question_modal(), create_edit_question_modal(), create_header(), _build_grouped_options(), create_state_panel()

### Community 8 - "🌟 Key Features"
Cohesion: 0.22
Nodes (8): 1. Local Ollama Integration & GPU Status Indicators, 2. Manufacturing Process Data & Quality Gates, 3. Dedicated Section: Single Model Inference, 4. Interactive 3-Column Workbench (`Inspect` Mode), 5. Benchmark Sensitivity & Run Audit (`Batch` & `Runs` Modes), Decision Playground (Ollama Decision Model Playground), 🌟 Key Features, 🚀 Quickstart

### Community 9 - "benchmark.py"
Cohesion: 0.24
Nodes (3): create_sensitivity_figure(), run_batch_evaluation(), get_model_color()

## Knowledge Gaps
- **10 isolated node(s):** `decision-playground`, `graphify`, `Workflow: graphify`, `graphify`, `1. Local Ollama Integration & GPU Status Indicators` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 110 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DecisionQuestion` connect `evaluator.py` to `get_available_models`, `presets.py`, `app.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `DecisionDataset` connect `presets.py` to `evaluator.py`, `app.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `DatasetRecord` connect `presets.py` to `evaluator.py`, `app.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `DecisionQuestion` (e.g. with `export_native_json()` and `export_results_to_csv()`) actually correct?**
  _`DecisionQuestion` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `DecisionDataset` (e.g. with `export_native_json()` and `export_results_to_csv()`) actually correct?**
  _`DecisionDataset` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `decision-playground`, `graphify`, `Workflow: graphify` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `presets.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09523809523809523 - nodes in this community are weakly interconnected._