"""
Preset loader for manufacturing process text snippets and decision criteria suites.
All snippets, questions, and choices are loaded dynamically from data/example.json.
No hardcoded question options or enums in python code.
"""
from pathlib import Path
from typing import List
from src.types import DecisionQuestion, DatasetRecord, DecisionDataset
from src.config import get_dataset_paths

# Resolve dataset JSON path from config.yaml
paths = get_dataset_paths()
DATASET_JSON_PATH = Path(__file__).parent.parent / paths.get("example_path", "data/example.json")
TEMPLATE_JSON_PATH = Path(__file__).parent.parent / paths.get("template_path", "data/template.json")

# Load the demo dataset from JSON
DEMO_DATASET: DecisionDataset = DecisionDataset.from_json(str(DATASET_JSON_PATH))

# Dynamically populate questions and snippets from JSON
DEFAULT_MANUFACTURING_QUESTIONS: List[DecisionQuestion] = DEMO_DATASET.questions
PRESET_SNIPPETS: List[DatasetRecord] = DEMO_DATASET.records


def get_template_dataset() -> DecisionDataset:
    """Loads the reference template dataset specified in config.yaml."""
    return DecisionDataset.from_json(str(TEMPLATE_JSON_PATH))


def get_all_records() -> List[DatasetRecord]:
    """Returns combined list of demo records and template records."""
    records = list(PRESET_SNIPPETS)
    try:
        tmpl = get_template_dataset()
        for r in tmpl.records:
            if not any(existing.id == r.id for existing in records):
                records.append(r)
    except Exception:
        pass
    return records


def get_preset_by_id(preset_id: str) -> DatasetRecord:
    for doc in get_all_records():
        if doc.id == preset_id:
            return doc
    return PRESET_SNIPPETS[0]


def get_preset_options():
    options = [{"value": doc.id, "label": doc.title} for doc in PRESET_SNIPPETS]
    try:
        tmpl = get_template_dataset()
        for doc in tmpl.records:
            options.append({"value": doc.id, "label": f"[Template] {doc.title}"})
    except Exception:
        pass
    return options
