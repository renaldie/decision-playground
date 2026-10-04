"""
Benchmark and batch testing src.
Evaluates manufacturing process snippets across selected Ollama models
and generates metrics for threshold sensitivity, model calibration, and consensus.
"""
from typing import List, Dict, Any, Optional
from src.presets import PRESET_SNIPPETS, DEFAULT_MANUFACTURING_QUESTIONS
from src.evaluator import run_model_inference, get_model_color
from src.config import get_available_models, get_default_model, get_default_threshold
import plotly.graph_objects as go


def run_batch_evaluation(
    threshold_percent: Optional[float] = None,
    models: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Runs all preset snippets through the selected models and computes metrics."""
    if threshold_percent is None:
        threshold_percent = get_default_threshold()

    if not models:
        avail = get_available_models()
        models = avail[:2] if len(avail) >= 2 else (avail if avail else [get_default_model()])

    results_by_model: Dict[str, List[Dict[str, Any]]] = {m: [] for m in models}

    for doc in PRESET_SNIPPETS:
        questions = doc.questions if doc.questions else DEFAULT_MANUFACTURING_QUESTIONS
        for idx, m in enumerate(models):
            res = run_model_inference(m, doc.content, questions, threshold_percent, model_index=idx)
            results_by_model[m].append({
                "doc_id": doc.id,
                "doc_title": doc.title,
                "category": doc.category,
                "passed": res.overall_passed,
                "confidence": res.overall_confidence,
                "latency_ms": res.latency_ms,
            })

    # Sensitivity sweep across thresholds (70% to 95%)
    thresholds = [70, 75, 80, 85, 90, 95]
    sweep_data = {m: {"thresholds": thresholds, "auto_rates": []} for m in models}

    for t in thresholds:
        for idx, m in enumerate(models):
            passed_count = 0
            for doc in PRESET_SNIPPETS:
                q = doc.questions if doc.questions else DEFAULT_MANUFACTURING_QUESTIONS
                res = run_model_inference(m, doc.content, q, float(t), model_index=idx)
                if res.overall_passed:
                    passed_count += 1
            auto_rate = round((passed_count / len(PRESET_SNIPPETS)) * 100, 1)
            sweep_data[m]["auto_rates"].append(auto_rate)

    return {
        "results_by_model": results_by_model,
        "sweep_data": sweep_data,
        "total_documents": len(PRESET_SNIPPETS),
        "models": models,
    }


def create_sensitivity_figure(sweep_data: Dict[str, Any], current_threshold: float) -> go.Figure:
    """Creates a sleek, dark-themed Plotly figure for threshold vs auto-approval rate."""
    fig = go.Figure()

    dash_styles = ["solid", "dot", "dash", "longdash"]

    for idx, (m_name, m_data) in enumerate(sweep_data.items()):
        color = get_model_color(m_name, idx)
        fig.add_trace(go.Scatter(
            x=m_data["thresholds"],
            y=m_data["auto_rates"],
            mode="lines+markers",
            name=m_name,
            line=dict(color=color, width=2.5, dash=dash_styles[idx % len(dash_styles)]),
            marker=dict(size=7),
        ))

    # Add vertical line for current threshold
    fig.add_vline(
        x=current_threshold,
        line_width=1.5,
        line_dash="dash",
        line_color="#64748b",
        annotation_text=f"Threshold: {current_threshold:.0f}%",
        annotation_position="top right",
        annotation_font_color="#94a3b8",
        annotation_font_size=11,
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.4)",
        font=dict(family="'Inter', -apple-system, sans-serif", color="#94a3b8", size=11),
        margin=dict(l=40, r=40, t=30, b=40),
        xaxis=dict(
            title="Decision Threshold (Auto at ≥ %)",
            gridcolor="#1e293b",
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(
            title="Auto-Approval Rate (%)",
            gridcolor="#1e293b",
            showgrid=True,
            range=[0, 105],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)"
        ),
        hovermode="x unified",
    )
    return fig
