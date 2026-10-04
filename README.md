# Decision Playground (TypeSafe Decision Model Playground)

An industrial-grade model playground built with **Plotly Dash** and **Dash Mantine Components (DMC)** to inspect, evaluate, and benchmark local Ollama decision models (such as `tev1:0.8b`, `tev1:4b`, `lfm2.5:8b-a1b-q4_K_M`) on **manufacturing process data** using native **TypeSafe Primitives** (**Noul**, **Choice**, and **Score**).

Designed with a high-density, dark industrial aesthetic, rich telemetry meters, and reactive in-memory state management.

---

## 🌟 Core Features & Architecture

### 1. Native TypeSafe Decision Primitives
Fully aligned with the [TypeSafe Primitives Specification](https://docs.typesafe.ai/primitives.md):

* **Noul (`noul`)**:
  * **Function**: Binary judgment / statement evaluation.
  * **Output**: Calibrated probability $P(\text{yes}) \in [0.0, 1.0]$.
  * **Criteria**: Clear definitions for `True` (nominal / conforming) and `False` (failure / non-conformance).
* **Choice (`choice`)**:
  * **Function**: Categorical classification over discrete mutually-exclusive options.
  * **Output**: Selected `choice`, complete probability distribution across all options, and confidence metric.
  * **Criteria**: Dictionary mapping discrete option keys to detailed physical defect/process descriptions.
* **Score (`score`)**:
  * **Function**: Continuous position evaluation along an ordered rubric spectrum.
  * **Output**: Continuous `score` position (e.g. $0.0$ to $N.0$), distribution over levels, and confidence.
  * **Criteria**: Ordered list of rubric levels (Level 0 through Level $N$) specifying process disturbance severity.

---

### 2. Interactive Questions Panel (`panel_questions.py`)

* **Interactive Primitive Switcher**:
  * Change question primitives (`noul`, `choice`, `score`) dynamically on each card via the type dropdown.
  * Card elements, metric targets, and criteria immediately adapt with dedicated color accents (Blue for Noul, Cyan for Choice, Violet for Score).
* **Option & Level Pills with Hover Tooltips**:
  * Hovering over any option pill (Choice), rubric level pill (Score), or True/False pill (Noul) reveals an instant tooltip popover containing the full criteria definition.
* **Expandable Criteria Inspector Accordion**:
  * Each question card features a compact `Criteria Definitions (N)` accordion. Clicking it expands an inline breakdown displaying every option or rubric level alongside its full text specification.
* **On-the-Fly Question Editing Modal**:
  * Click the **`Edit`** button on any card to open the question editor.
  * Modify **Identifier / Name**, **Primitive Type**, **Instructions / Prompt**, and **Criteria** on the fly.
  * Changes update the active in-memory reactive store immediately without altering `data/example.json`.
* **Unified Question Actions**:
  * Single-click **`Edit`** and **`Remove`** buttons cleanly manage question sets.
  * Add custom decision checks via **`+ Add Check`** modal.
* **Question Template Switcher**:
  * Switch between preset suites: **Process Quality Gates** (`data/example.json`) and **Custom Criteria** (`data/template.json`).

---

### 3. Decisions & Evaluation Panel (`panel_decisions.py`)

* **Prediction vs. Truth Inspection**:
  * Direct comparison between model inference outputs and ground-truth process labels.
* **Stepped Gradient Capsule Meters**:
  * **Noul**: 10-step blue gradient capsule meter reflecting $P(\text{yes})$.
  * **Choice**: 10-step cyan gradient capsule meter reflecting classification confidence.
  * **Score**: Multi-capsule violet spectrum meter calibrated to the exact number of rubric levels (e.g., 4 levels = 4 distinct segments).
* **Multi-Model Side-by-Side Inference**:
  * Compare up to 4 models concurrently with latency tracking (ms), evaluated tokens, and exact log excerpts.

---

### 4. Local Ollama Integration & GPU Status

* **Automatic Model Discovery**: Queries local Ollama instance (`http://127.0.0.1:11434`) and cross-references installed models.
* **GPU VRAM Status Indicators**:
  * `🟢 GPU`: Model is actively resident in GPU VRAM (verified via `ollama ps`).
  * `⚪ Load`: Model is cold or offloaded. Clicking preloads the model into GPU memory with a 30-minute keep-alive.
* **Distinct Color Badges**:
  * 🔵 **Cyan Blue** (`#38bdf8`)
  * 🟠 **Amber Orange** (`#f97316`)
  * 🟣 **Purple** (`#a855f7`)
  * 🟢 **Emerald Green** (`#10b981`)

---

### 5. Multi-View Workspace

* **Workbench View (`Inspect`)**:
  * **Left Column (STATE)**: Industrial production log viewer, character and token estimation, and preset run selectors.
  * **Center Column (QUESTIONS)**: Interactive TypeSafe question cards, primitive switchers, option pills, and criteria inspectors.
  * **Right Column (DECISIONS)**: Side-by-side inference outputs, stepped gradient meters, and prediction metrics.
* **Dedicated Single-Model Inference View (`Inference`)**:
  * Run individual models across entire datasets with row-by-row decision audits, pass rates, and CSV matrix export.
* **Batch Sensitivity Benchmark View (`Batch`)**:
  * Threshold sensitivity curves and aggregate multi-run evaluation.
* **Audit History View (`Logs`)**:
  * Timestamped session execution audit logs.

---

## 📁 Dataset & File Structure

```text
decision-playground/
├── app.py                         # Dash main application, callbacks, and layout
├── main.py                        # Entry point runner (port 8050)
├── assets/
│   ├── style.css                  # Industrial dark theme styles
│   └── run_button.js              # Run button interaction script
├── components/
│   ├── header.py                  # App header, model selectors, view tabs
│   ├── panel_state.py             # Input state / text log viewer panel
│   ├── panel_questions.py         # Questions panel, card rendering, criteria inspector
│   ├── panel_decisions.py         # Decisions panel, stepped gradient meters
│   ├── add_question_modal.py      # Modal to add new decision checks
│   ├── edit_question_modal.py     # Modal to edit question name, type, prompt, criteria
│   ├── tab_inference.py           # Dedicated single model dataset inference
│   ├── tab_batch.py               # Batch evaluation & sensitivity curve
│   └── tab_logs.py                # Session execution history logs
├── data/
│   ├── example.json               # Baseline manufacturing dataset (pristine reference)
│   └── template.json              # Clean criteria template dataset
└── src/
    ├── types.py                   # TypeSafe schemas (DecisionQuestion, DatasetRecord, etc.)
    ├── presets.py                 # Preset loaders & dataset utilities
    ├── evaluator.py               # Inference execution & evaluation logic
    ├── benchmark.py               # Batch benchmark computations
    ├── config.py                  # Model configuration & settings
    └── ollama_client.py           # Local Ollama API client & VRAM manager
```

---

## 🚀 Quickstart

### 1. Verify Local Ollama
```bash
ollama list
ollama ps
```

### 2. Launch the Playground
```bash
# Using uv (recommended)
uv run python main.py

# Or using python directly
python main.py
```

### 3. Open in Browser
Navigate to **`http://127.0.0.1:8050`** in your browser.
