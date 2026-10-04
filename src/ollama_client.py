"""
Ollama Client for Decision Playground.
Interacts with the local Ollama instance (http://127.0.0.1:11434).
Handles model discovery, GPU memory status check, model preloading/warming,
and structured decision evaluation.
"""
import urllib.request
import urllib.error
import json
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from src.config import get_ollama_settings, get_available_models


def get_base_url() -> str:
    """Retrieves base Ollama URL from config.yaml."""
    return get_ollama_settings().get("base_url", "http://127.0.0.1:11434")


OLLAMA_BASE_URL = get_base_url()


def is_ollama_online() -> bool:
    """Checks if local Ollama daemon is reachable."""
    try:
        base_url = get_base_url()
        req = urllib.request.Request(f"{base_url}/api/version", headers={"User-Agent": "DecisionPlayground"})
        with urllib.request.urlopen(req, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def get_installed_models() -> List[Dict[str, Any]]:
    """Returns list of all installed Ollama models, falling back to config.yaml models."""
    try:
        base_url = get_base_url()
        req = urllib.request.Request(f"{base_url}/api/tags", headers={"User-Agent": "DecisionPlayground"})
        with urllib.request.urlopen(req, timeout=2.0) as r:
            data = json.loads(r.read().decode("utf-8"))
            models = data.get("models", [])
            return [{"name": m["name"], "size": m.get("size", 0)} for m in models]
    except Exception:
        return [{"name": m, "size": 0} for m in get_available_models()]


def get_gpu_loaded_models() -> Dict[str, Dict[str, Any]]:
    """Returns mapping of models currently resident in GPU memory."""
    loaded = {}
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/ps", headers={"User-Agent": "DecisionPlayground"})
        with urllib.request.urlopen(req, timeout=2.0) as r:
            data = json.loads(r.read().decode("utf-8"))
            for m in data.get("models", []):
                name = m.get("name", "")
                processor = m.get("processor", "GPU")
                size_vram = m.get("size_vram", m.get("size", 0))
                loaded[name] = {
                    "processor": processor,
                    "size_vram": size_vram,
                    "expires_at": m.get("expires_at", ""),
                }
    except Exception:
        pass
    return loaded


def load_model_to_gpu(model_name: str) -> Tuple[bool, str]:
    """Sends warm-up request to load the model into GPU memory with 30m keep-alive."""
    try:
        payload = json.dumps({
            "model": model_name,
            "keep_alive": "30m",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=25.0) as r:
            _ = r.read(512)
            return True, f"Model {model_name} loaded onto GPU successfully."
    except Exception as e:
        return False, f"Failed to load {model_name}: {str(e)}"


def stop_model_on_gpu(model_name: str) -> Tuple[bool, str]:
    """Sends keep_alive=0 to evict the model from GPU VRAM (equivalent to ollama stop)."""
    try:
        payload = json.dumps({
            "model": model_name,
            "keep_alive": 0,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10.0) as r:
            _ = r.read(512)
            return True, f"Model {model_name} stopped and evicted from GPU."
    except Exception as e:
        return False, f"Failed to stop {model_name}: {str(e)}"



def run_ollama_batch_decision(
    model_name: str,
    text: str,
    questions: List[Dict[str, Any]],
    timeout_sec: float = 6.0,
) -> Dict[str, Any]:
    """Evaluates all questions in a single batched prompt for high-speed inference."""
    q_lines = []
    for q in questions:
        q_type = q.get("type", "bool")
        if q_type == "choice":
            choices_str = ", ".join(q.get("choices", []))
            q_lines.append(f"- {q['name']}: {q['prompt']} (Choices: [{choices_str}])")
        else:
            q_lines.append(f"- {q['name']}: {q['prompt']} (Type: boolean P(true))")
    q_text = "\n".join(q_lines)

    system_instruction = (
        "You are an industrial manufacturing process audit and decision model. "
        "Analyze the process log against each question and respond in JSON format with an object where keys are the question names, "
        "each containing {\"p_true\": float (0.0 to 1.0), \"evidence\": string, \"rationale\": string, \"selected_choice\": string if choice type}."
    )

    user_query = f"PROCESS LOG:\n\"\"\"\n{text[:2200]}\n\"\"\"\n\nCRITERIA TO EVALUATE:\n{q_text}\n\nJSON output:"

    payload = json.dumps({
        "model": model_name,
        "prompt": f"<system>\n{system_instruction}\n</system>\n\n<user>\n{user_query}\n</user>\n\n",
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.05,
            "num_predict": 300,
            "num_ctx": 4096,
        },
    }).encode("utf-8")

    start_time = time.time()
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as r:
            res_data = json.loads(r.read().decode("utf-8"))
            elapsed_ms = (time.time() - start_time) * 1000

            raw_response = res_data.get("response", "").strip()
            cleaned = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL).strip()
            parsed = {}
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))

            return {
                "success": True,
                "data": parsed,
                "latency_ms": elapsed_ms,
                "tokens": res_data.get("eval_count", 0),
            }
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "success": False,
            "error": str(e),
            "latency_ms": elapsed_ms,
        }


def run_ollama_decision(
    model_name: str,
    text: str,
    question_name: str,
    prompt: str,
    question_type: str,
    choices: Optional[List[str]] = None,
    timeout_sec: float = 8.0,
) -> Dict[str, Any]:
    """Runs a targeted decision inference query through Ollama for a single question."""
    system_instruction = (
        "You are an industrial manufacturing process audit and decision model. "
        "Analyze the provided process text snippet carefully against the decision hypothesis. "
        "Respond in strict JSON with keys: "
        "{\"p_true\": float (0.00 to 1.00), \"passed\": bool, \"evidence\": string (quote from text), \"rationale\": string (brief 1-sentence engineering reason)}"
    )

    if question_type == "choice" and choices:
        system_instruction += (
            f" For choice question, select best matching choice among {choices} "
            f"and include \"selected_choice\": string in JSON."
        )

    user_query = f"PROCESS LOG:\n\"\"\"\n{text[:2000]}\n\"\"\"\n\nDECISION HYPOTHESIS ({question_name}):\n{prompt}\n\nStrict JSON response:"

    payload = json.dumps({
        "model": model_name,
        "prompt": f"<system>\n{system_instruction}\n</system>\n\n<user>\n{user_query}\n</user>\n\n",
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.05,
            "num_predict": 150,
            "num_ctx": 4096,
        },
    }).encode("utf-8")

    start_time = time.time()
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as r:
            res_data = json.loads(r.read().decode("utf-8"))
            elapsed_ms = (time.time() - start_time) * 1000

            raw_response = res_data.get("response", "").strip()
            cleaned = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL).strip()
            parsed = {}
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
            else:
                parsed = json.loads(cleaned)

            p_true = float(parsed.get("p_true", 0.5))
            p_true = max(0.01, min(0.99, p_true))

            return {
                "success": True,
                "p_true": p_true,
                "passed": bool(parsed.get("passed", p_true >= 0.8)),
                "evidence": str(parsed.get("evidence", "")),
                "rationale": str(parsed.get("rationale", "")),
                "selected_choice": parsed.get("selected_choice"),
                "latency_ms": elapsed_ms,
                "tokens": res_data.get("eval_count", 0),
            }
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "success": False,
            "error": str(e),
            "latency_ms": elapsed_ms,
        }
