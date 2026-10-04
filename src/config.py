"""
Configuration loader for Decision Playground.
Reads all application settings dynamically from config.yaml.
"""
from pathlib import Path
from typing import Dict, Any, List
import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

_CONFIG_CACHE: Dict[str, Any] = None


def load_config(force_reload: bool = False) -> Dict[str, Any]:
    """Loads and caches configuration directly from config.yaml."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None and not force_reload:
        return _CONFIG_CACHE

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        _CONFIG_CACHE = yaml.safe_load(f) or {}
    return _CONFIG_CACHE


def get_config() -> Dict[str, Any]:
    """Returns the full parsed configuration dictionary."""
    return load_config()


def get_available_models() -> List[str]:
    """Returns the list of maintained models defined in config.yaml."""
    cfg = load_config()
    return list(cfg.get("ollama", {}).get("models", []))


def get_default_model() -> str:
    """Returns the designated default model from config.yaml."""
    cfg = load_config()
    return cfg.get("ollama", {}).get("default_model", "")


def get_default_threshold() -> float:
    """Returns the default decision threshold percentage from config.yaml."""
    cfg = load_config()
    return float(cfg.get("ollama", {}).get("threshold", 90.0))


def get_ollama_settings() -> Dict[str, Any]:
    """Returns Ollama base_url, api_key, threshold, and model settings from config.yaml."""
    cfg = load_config()
    return cfg.get("ollama", {})


def get_dataset_paths() -> Dict[str, str]:
    """Returns dataset file paths from config.yaml."""
    cfg = load_config()
    return cfg.get("datasets", {})


def get_log_folder() -> str:
    """Returns the destination logging folder path from config.yaml."""
    cfg = load_config()
    return cfg.get("logging", {}).get("log_folder", "./logs")


def get_timezone_offset_hours() -> int:
    """Returns timezone offset in hours from config.yaml."""
    cfg = load_config()
    return int(cfg.get("logging", {}).get("timezone_offset_hours", 8))
