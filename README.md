# Decision Playground (Ollama Decision Model Playground)

An industrial-grade model playground built with **Plotly Dash** and **Dash Mantine Components (DMC)** to inspect, evaluate, and benchmark local Ollama decision models (such as `tev1:0.8b` vs `tev1:4b` vs `lfm2.5:8b-a1b-q4_K_M`) on **manufacturing process data** (lines, yields, stoppages, parameter drifts, and defect modes).

Designed with a high-density, dark industrial aesthetic (no AI-slop, neutral dark monochrome icons, and distinct vivid color badges reserved strictly for model identification).

---

## 🌟 Key Features

### 1. Local Ollama Integration & GPU Status Indicators
- **Auto-Discovery**: Queries local Ollama instance (`http://127.0.0.1:11434`) for installed models (`tev1:0.8b`, `tev1:4b`, etc.).
- **GPU VRAM Status Indicators**:
  - `🟢 GPU`: Model is resident in GPU VRAM (verified via `ollama ps`).
  - `⚪ Load`: Model is cold or offloaded. **Clicking the indicator directly warms up and preloads the model into GPU memory** with a 30-minute keep-alive.
- **Side-by-Side Comparison for up to 3 Models**:
  - 🔵 **Model 1 (`tev1:0.8b`)**: Cyan Blue identity dot (`#38bdf8`).
  - 🟠 **Model 2 (`tev1:4b`)**: Amber Orange identity dot (`#f97316`).
  - 🟣 **Model 3 (`lfm2.5:8b-a1b-q4_K_M`)**: Purple identity dot (`#a855f7`).

### 2. Manufacturing Process Data & Quality Gates
- All data and presets focus strictly on industrial process engineering:
  - **SMT Line 4 - PCBA Surface Mount Reflow Run** (Yield 99.42% - Nominal)
  - **Bay 3 Etch Chamber B - Plasma Drift & Pressure Spike** (Yield 91.20% - Excursion)
  - **Die Cast Cell 2 - Cold Shut & Ladle Misfeed** (Yield 95.79% - Sub-optimal)
  - **Formation Rack 04 - Thermal Runaway Risk & DC-IR Spikes** (Yield 97.83%)
  - **CNC Line 6 - 5-Axis Aerospace Impeller Milling** (Yield 99.09% - Precision)
- **Manufacturing Decision Gates**:
  1. `yield_target_met` ($P(\text{true})$): Lot yield $\ge$ 98.50% nominal target.
  2. `line_stoppage_flag` ($P(\text{false})$): Zero unscheduled downtime $> 10$ minutes.
  3. `parameter_drift` ($P(\text{false})$): Pressures, temperatures, and tolerances remain within 3-sigma control limits.
  4. `root_cause_documented` ($P(\text{true})$): Formal engineering failure mechanism verified in the log.
  5. `primary_defect_type` (Categorical Choice): Classifies defect mode (`solder_bridging`, `rf_plasma_drift`, `porosity / cold_shut`, `thermal_gradient`, `none`).

### 3. Dedicated Section: Single Model Inference
- Dedicated workspace tab to evaluate a single model across an entire dataset:
  - **Target Model Selector** with live GPU VRAM badge and load trigger.
  - **Dataset Upload & Ingestion**: Upload custom `.csv`, `.json`, or `.txt` process logs, or click "Load Sample Set" (5 industrial production runs).
  - **Gate Checklist Configurator**: Select and customize which quality gates to evaluate across every row.
  - **Execution & Decision Trace Table**: Row-by-row decision audit, pass rate %, excursion count, and average inference latency.
  - **CSV Export**: Download full decision evaluation matrices directly to CSV.

### 4. Interactive 3-Column Workbench (`Inspect` Mode)
- **Column 1: INPUT**:
  - Process snippet selector, monospaced text viewer, character and token estimation (~1.35x words).
- **Column 2: QUESTIONS (Process Gates)**:
  - Card list matching industrial audit criteria: gate name, type (`bool` / `choice`), prompt text, metric indicator ($P(\text{true})$), requirement flag, and pass condition.
- **Column 3: RESULTS**:
  - Lot clearance banner (`ALL MODELS CLEARED LOT` vs `PROCESS EXCURSION / QUALITY HOLD REQUIRED`).
  - **Engineering Action Dispatch / Hold Ticket**: Automatically generates a formal shift quarantine ticket detailing flagged gates when an excursion occurs.
  - Multi-model probability bars with an overlaid vertical line at the gate threshold $\tau$ (e.g. `Auto at ≥ 90%`).
  - Extracted log citations and latency tracking.

### 5. Benchmark Sensitivity & Run Audit (`Batch` & `Runs` Modes)
- **Plotly Sensitivity Curve**: Interactive curve showing how tuning the threshold $\tau$ (70% - 95%) trades off auto-clearance vs human engineering escalation.
- **Session Audit History**: Log of all executed decision runs with timestamps, active models, and gate outcomes.

---

## 🚀 Quickstart

1. **Verify Ollama is Running**:
   ```bash
   ollama list
   ollama ps
   ```

2. **Launch the Playground**:
   ```bash
   uv run python main.py
   ```

3. **Open in Browser**:
   Navigate to [http://127.0.0.1:8050](http://127.0.0.1:8050)
