# Graph Report - decision-playground  (2026-10-05)

## Corpus Check
- 27 files · ~17,607 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .css 1, .lock 1)

## Summary
- 260 nodes · 562 edges · 14 communities (8 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `30deeae3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- config.py
- presets.py
- logger.py
- panel_decisions.py
- app.py
- evaluator.py
- panel_questions.py
- 🌟 Core Features & Architecture
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
- `handle_template_selection()` --uses--> `DecisionDataset`  [INFERRED]
  app.py → src/types.py
- `handle_dataset_source()` --uses--> `DecisionDataset`  [INFERRED]
  app.py → src/types.py
- `export_native_json()` --uses--> `DatasetRecord`  [INFERRED]
  app.py → src/types.py
- `export_native_json()` --uses--> `DecisionDataset`  [INFERRED]
  app.py → src/types.py
- `export_results_to_csv()` --uses--> `DatasetRecord`  [INFERRED]
  app.py → src/types.py

## Import Cycles
- None detected.

## Communities (14 total, 6 thin omitted)

### Community 0 - "config.py"
Cohesion: 0.09
Nodes (15): switch_view(), create_decisions_panel(), create_batch_tab(), create_inference(), get_dataset_results_headers(), render_results_table_rows(), create_runs_tab(), create_sensitivity_figure() (+7 more)

### Community 1 - "presets.py"
Cohesion: 0.07
Nodes (5): get_all_records(), get_preset_options(), get_template_dataset(), DatasetRecord, DecisionDataset

### Community 3 - "logger.py"
Cohesion: 0.18
Nodes (4): get_log_folder(), get_timezone_offset_hours(), get_utc8_now(), list_recent_logs()

### Community 4 - "panel_decisions.py"
Cohesion: 0.16
Nodes (7): get_score_gradient(), render_continuous_gradient_meter(), render_decisions_content(), render_empty_decisions(), render_evaluation_bar(), render_model_decision_card(), render_stepped_gradient_meter()

### Community 5 - "app.py"
Cohesion: 0.11
Nodes (26): delete_question(), export_native_json(), export_results_to_csv(), handle_dataset_source(), handle_preset_selection(), handle_question_type_change(), handle_template_selection(), manage_add_question_modal() (+18 more)

### Community 6 - "evaluator.py"
Cohesion: 0.06
Nodes (20): get_ollama_settings(), evaluate_manufacturing_question(), extract_evidence(), generate_engineering_dispatch(), get_model_color(), run_model_inference(), get_base_url(), get_cross_referenced_models() (+12 more)

### Community 7 - "panel_questions.py"
Cohesion: 0.10
Nodes (8): create_add_question_modal(), create_edit_question_modal(), create_header(), create_questions_panel(), render_question_card(), render_question_criteria_section(), _build_grouped_options(), create_state_panel()

### Community 8 - "🌟 Core Features & Architecture"
Cohesion: 0.15
Nodes (12): 1. Native TypeSafe Decision Primitives, 1. Verify Local Ollama, 2. Interactive Questions Panel (`panel_questions.py`), 2. Launch the Playground, 3. Decisions & Evaluation Panel (`panel_decisions.py`), 3. Open in Browser, 4. Local Ollama Integration & GPU Status, 5. Multi-View Workspace (+4 more)

## Knowledge Gaps
- **13 isolated node(s):** `decision-playground`, `graphify`, `Workflow: graphify`, `graphify`, `1. Native TypeSafe Decision Primitives` (+8 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 113 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DecisionQuestion` connect `app.py` to `presets.py`, `evaluator.py`, `panel_questions.py`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `DecisionDataset` connect `presets.py` to `app.py`, `evaluator.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `DatasetRecord` connect `presets.py` to `app.py`, `evaluator.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `DecisionQuestion` (e.g. with `export_native_json()` and `export_results_to_csv()`) actually correct?**
  _`DecisionQuestion` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `DecisionDataset` (e.g. with `export_native_json()` and `export_results_to_csv()`) actually correct?**
  _`DecisionDataset` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `decision-playground`, `graphify`, `Workflow: graphify` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `config.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08985200845665962 - nodes in this community are weakly interconnected._