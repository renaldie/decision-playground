"""
Decision Playground Execution Logger.
Saves run evaluations and audits to ./logs/{date_time}.json with UTC+8 timestamps.
"""
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from src.config import get_log_folder, get_timezone_offset_hours


def get_utc8_now() -> datetime:
    """Returns the current datetime in UTC+8 (or configured offset)."""
    offset = get_timezone_offset_hours()
    tz = timezone(timedelta(hours=offset))
    return datetime.now(tz)


def log_run(mode: str, data: Dict[str, Any]) -> Optional[str]:
    """
    Saves an evaluation run event to ./logs/{date_time}.json with UTC+8 timestamp.
    Returns the file path of the saved log, or None if failed.
    """
    try:
        now = get_utc8_now()
        date_time_str = now.strftime("%Y%m%d_%H%M%S")
        log_dir_str = get_log_folder()
        log_dir = Path(__file__).parent.parent / log_dir_str if not Path(log_dir_str).is_absolute() else Path(log_dir_str)
        log_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{date_time_str}.json"
        log_path = log_dir / filename

        # Ensure unique filename if triggered multiple times in the same second
        counter = 1
        while log_path.exists():
            filename = f"{date_time_str}_{counter}.json"
            log_path = log_dir / filename
            counter += 1

        payload = {
            "timestamp": now.isoformat(),
            "timezone": f"UTC+{get_timezone_offset_hours()}",
            "mode": mode,
            **data,
        }

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        return str(log_path)
    except Exception as e:
        print(f"Warning: Failed to write run log ({e})")
        return None


def list_recent_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """Lists recent log files from the configured log directory."""
    try:
        log_dir_str = get_log_folder()
        log_dir = Path(__file__).parent.parent / log_dir_str if not Path(log_dir_str).is_absolute() else Path(log_dir_str)
        if not log_dir.exists():
            return []
        log_files = sorted(log_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
        return [{"filename": f.name, "path": str(f), "modified": os.path.getmtime(f)} for f in log_files[:limit]]
    except Exception as e:
        print(f"Warning: Failed to list recent logs ({e})")
        return []
