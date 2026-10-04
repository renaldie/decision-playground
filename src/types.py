"""
TypeSafe Decision Dataset and Schema Definitions.
Integrates with langchain_typesafe (Noul, Choice, Score, TypeSafeClassifier).
Questions, criteria, and pass conditions are dynamic and completely user-defined via JSON.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
import json
import uuid
import csv
import io

try:
    from langchain_typesafe import (
        Noul,
        Choice,
        Score,
        NoulCriteria,
        TypeSafeClassifier,
        ClassifierResponse,
        NoulAnswer,
        ChoiceAnswer,
        ScoreAnswer,
    )
except ImportError:
    Noul = None
    Choice = None
    Score = None
    TypeSafeClassifier = None


@dataclass
class DecisionQuestion:
    """
    A TypeSafe decision gate primitive.
    Supports binary judgments (Noul), discrete categoricals (Choice), and ordinal rubrics (Score).
    """
    name: str
    instructions: str
    type: str = "noul"  # "noul", "choice", "score"
    criteria: Any = None  # Dict[str, str] for Choice, List[str] for Score, Dict for Noul
    pass_condition: Any = True
    pass_choice: Optional[str] = None
    required: bool = True
    needs_record: bool = False
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def prompt(self) -> str:
        """Alias for instructions."""
        return self.instructions

    @prompt.setter
    def prompt(self, val: str):
        self.instructions = val

    @property
    def choices(self) -> List[str]:
        """Backward-compatible choices list."""
        if isinstance(self.criteria, dict):
            return list(self.criteria.keys())
        elif isinstance(self.criteria, list):
            return [str(c) for c in self.criteria]
        return []

    @choices.setter
    def choices(self, val: List[str]):
        if isinstance(val, list):
            self.criteria = {c: c for c in val}

    def to_typesafe(self) -> Any:
        """Converts to native langchain_typesafe Question primitive (Noul, Choice, or Score)."""
        t = self.type.lower()
        if t in ("noul", "bool", "boolean"):
            crit = None
            if isinstance(self.criteria, dict) and "true" in self.criteria and "false" in self.criteria:
                crit = NoulCriteria(true=self.criteria["true"], false=self.criteria["false"])
            return Noul(instructions=self.instructions, criteria=crit)
        elif t in ("choice", "categorical"):
            crit = self.criteria
            if isinstance(crit, list):
                crit = {str(c): str(c) for c in crit}
            elif not crit or not isinstance(crit, dict):
                crit = {"pass": "Pass condition met", "fail": "Fail condition met"}
            return Choice(instructions=self.instructions, criteria=crit)
        elif t in ("score", "ordinal"):
            crit = self.criteria if isinstance(self.criteria, list) else ["Level 0", "Level 1", "Level 2"]
            return Score(instructions=self.instructions, criteria=crit)
        return Noul(instructions=self.instructions)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes to TypeSafe JSON format."""
        return {
            "id": self.id or self.name,
            "name": self.name,
            "type": self.type,
            "instructions": self.instructions,
            "prompt": self.instructions,
            "criteria": self.criteria,
            "choices": self.choices,
            "pass_condition": self.pass_condition,
            "pass_choice": self.pass_choice,
            "required": self.required,
            "needs_record": self.needs_record,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionQuestion":
        """Instantiates from either native TypeSafe schema or legacy dictionary."""
        name = str(data.get("name") or data.get("id") or "gate")
        instructions = str(data.get("instructions") or data.get("prompt") or "")
        q_type = str(data.get("type", "noul")).lower()
        if q_type == "bool":
            q_type = "noul"

        criteria = data.get("criteria")
        if criteria is None and "choices" in data:
            choices_list = data.get("choices") or []
            if choices_list:
                criteria = {str(c): str(c) for c in choices_list}

        pass_cond = data.get("pass_condition", True)
        pass_choice = data.get("pass_choice")
        if not pass_choice and isinstance(criteria, dict):
            for k in criteria:
                if any(kw in k.lower() for kw in ("none", "pass", "tolerance")):
                    pass_choice = k
                    break

        return cls(
            name=name,
            instructions=instructions,
            type=q_type,
            criteria=criteria,
            pass_condition=pass_cond,
            pass_choice=pass_choice,
            required=bool(data.get("required", True)),
            needs_record=bool(data.get("needs_record", False)),
            id=str(data.get("id", name)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class QuestionEvaluation:
    """The result of evaluating a single TypeSafe question on a text state."""
    question_name: str
    question_type: str
    instructions: str = ""
    required: bool = True
    p_true: float = 0.0
    passed: bool = False
    confidence: float = 0.0
    choice_probs: Optional[Dict[str, float]] = None
    selected_choice: Optional[str] = None
    score: Optional[float] = None
    evidence: str = ""
    rationale: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    question_id: Optional[str] = None
    question_prompt: Optional[str] = None

    def __post_init__(self):
        if self.question_id is None:
            self.question_id = self.question_name
        if not self.instructions and self.question_prompt:
            self.instructions = self.question_prompt
        elif not self.question_prompt and self.instructions:
            self.question_prompt = self.instructions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id or self.question_name,
            "question_name": self.question_name,
            "question_prompt": self.instructions,
            "instructions": self.instructions,
            "question_type": self.question_type,
            "required": self.required,
            "p_true": round(self.p_true, 4),
            "passed": self.passed,
            "confidence": round(self.confidence, 4),
            "choice_probs": self.choice_probs,
            "selected_choice": self.selected_choice,
            "score": self.score,
            "evidence": self.evidence,
            "rationale": self.rationale,
            "metadata": self.metadata,
        }


@dataclass
class ModelResult:
    """Aggregated decision outcome from an evaluated TypeSafe decision model."""
    model_name: str
    model_color: str
    latency_ms: float
    evaluations: List[QuestionEvaluation]
    overall_passed: bool
    overall_confidence: float
    follow_up_email: str
    tokens_evaluated: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_color": self.model_color,
            "latency_ms": round(self.latency_ms, 1),
            "evaluations": [e.to_dict() for e in self.evaluations],
            "overall_passed": self.overall_passed,
            "overall_confidence": round(self.overall_confidence, 4),
            "follow_up_email": self.follow_up_email,
            "tokens_evaluated": self.tokens_evaluated,
            "metadata": self.metadata,
        }


@dataclass
class DatasetRecord:
    """A single text state sample in a TypeSafe dataset."""
    id: str
    title: str
    text: str
    category: str = "General"
    metadata: Dict[str, Any] = field(default_factory=dict)
    states: Dict[str, Any] = field(default_factory=dict)

    @property
    def content(self) -> str:
        return self.text

    @content.setter
    def content(self, value: str):
        self.text = value

    @property
    def questions(self) -> List[Any]:
        return getattr(self, "_questions", [])

    @questions.setter
    def questions(self, value: List[Any]):
        self._questions = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "state": self.text,   # canonical key per TypeSafe schema
            "text": self.text,    # backward-compat alias
            "metadata": dict(self.metadata),
            "truth": dict(self.states),   # canonical key per TypeSafe schema
            "states": dict(self.states),  # backward-compat alias
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetRecord":
        # Accept both 'state' (new canonical) and 'text'/'content' (legacy)
        text_val = str(data.get("state", data.get("text", data.get("content", ""))))
        # Accept both 'truth' (new canonical) and 'states' (legacy)
        truth_val = dict(data.get("truth", data.get("states", {})))
        return cls(
            id=str(data.get("id", str(uuid.uuid4())[:8])),
            title=str(data.get("title", "Untitled Record")),
            text=text_val,
            category=str(data.get("category", "General")),
            metadata=dict(data.get("metadata", {})),
            states=truth_val,
        )


@dataclass
class DecisionDataset:
    """
    TypeSafe Decision Dataset container.
    Stores complete schemas, typed questions, states, and records.
    Exports to native JSON format directly readable by langchain_typesafe workflows.
    """
    name: str = "TypeSafe Decision Dataset"
    schema_version: str = "1.0"
    description: str = ""
    questions: List[DecisionQuestion] = field(default_factory=list)
    records: List[DatasetRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "description": self.description,
            "questions": [q.to_dict() for q in self.questions],
            "states": [r.to_dict() for r in self.records],   # canonical key
            "records": [r.to_dict() for r in self.records],  # backward-compat alias
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Exports native JSON structure that can be read back in by types.py."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionDataset":
        questions = [DecisionQuestion.from_dict(q) for q in data.get("questions", [])]
        # Accept both 'states' (new canonical) and 'records' (legacy) for the record list
        raw_records = data.get("states", data.get("records", []))
        records = [DatasetRecord.from_dict(r) for r in raw_records]
        return cls(
            name=str(data.get("name", "TypeSafe Decision Dataset")),
            schema_version=str(data.get("schema_version", "1.0")),
            description=str(data.get("description", "")),
            questions=questions,
            records=records,
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def from_json(cls, json_source: Union[str, Dict[str, Any]]) -> "DecisionDataset":
        """Loads dataset and questions schema from JSON string or file path."""
        if isinstance(json_source, dict):
            return cls.from_dict(json_source)
        try:
            with open(json_source, "r", encoding="utf-8") as f:
                data = json.load(f)
                return cls.from_dict(data)
        except (OSError, FileNotFoundError):
            data = json.loads(json_source)
            return cls.from_dict(data)

    def to_typesafe_request(self, state_text: str) -> Dict[str, Any]:
        """Builds a ClassifierRequest dict suitable for TypeSafeClassifier.invoke()."""
        return {
            "state": state_text,
            "questions": {q.name: q.to_typesafe() for q in self.questions},
        }

    def to_original_format_with_states_csv(self) -> str:
        """Exports the dataset as CSV containing record fields and all evaluated state columns."""
        output = io.StringIO()
        writer = csv.writer(output)

        headers = ["Record ID", "Title", "Category", "Snippet Text"]
        for q in self.questions:
            t = getattr(q, "type", "noul").lower()
            if t in ("choice", "categorical"):
                headers.extend([f"Gate: {q.name} (Choice)", f"Gate: {q.name} (Confidence)", f"Gate: {q.name} (Passed)"])
            elif t in ("score", "ordinal"):
                headers.extend([f"Gate: {q.name} (Score)", f"Gate: {q.name} (Confidence)", f"Gate: {q.name} (Passed)"])
            else:
                headers.extend([f"Gate: {q.name} (Passed)", f"Gate: {q.name} (P_true)", f"Gate: {q.name} (Confidence)"])
        headers.append("Overall Passed")
        writer.writerow(headers)

        for r in self.records:
            row = [r.id, r.title, r.category, r.text.replace("\n", " ")[:150]]
            for q in self.questions:
                state = r.states.get(q.name, {})
                t = getattr(q, "type", "noul").lower()
                if t in ("choice", "categorical"):
                    row.extend([
                        state.get("selected_choice", state.get("choice", "-")),
                        f"{state.get('confidence', 0):.2f}" if isinstance(state.get("confidence"), (int, float)) else "-",
                        state.get("passed", "-"),
                    ])
                elif t in ("score", "ordinal"):
                    row.extend([
                        str(state.get("score", "-")),
                        f"{state.get('confidence', 0):.2f}" if isinstance(state.get("confidence"), (int, float)) else "-",
                        state.get("passed", "-"),
                    ])
                else:
                    p_val = state.get("p_true", state.get("noul"))
                    p_str = f"{p_val:.2f}" if isinstance(p_val, (int, float)) else str(p_val or "-")
                    row.extend([
                        state.get("passed", "-"),
                        p_str,
                        f"{state.get('confidence', 0):.2f}" if isinstance(state.get("confidence"), (int, float)) else "-",
                    ])
            row.append(r.states.get("overall_passed", "-"))
            writer.writerow(row)

        return output.getvalue()


# Compatibility classes
class QuestionType:
    BOOL = "noul"
    NOUL = "noul"
    CHOICE = "choice"
    SCORE = "score"


class PassCondition:
    TRUE = True
    FALSE = False


PresetDocument = DatasetRecord
