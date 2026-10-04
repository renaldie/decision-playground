"""
Modal for adding custom decision questions.
"""
import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify


def create_add_question_modal():
    return dmc.Modal(
        id="add-question-modal",
        title=dmc.Group([
            DashIconify(icon="tabler:plus", width=18, color="#38bdf8"),
            dmc.Text("Add Decision Check", fw=600, size="sm"),
        ], gap=8),
        opened=False,
        children=[
            dmc.Stack([
                dmc.TextInput(
                    id="new-q-name",
                    label="Identifier / Key Name",
                    placeholder="e.g. license_verified, jurisdiction, signature",
                    value="",
                    size="xs",
                    required=True,
                ),
                dmc.Textarea(
                    id="new-q-prompt",
                    label="Decision Instructions",
                    placeholder="e.g. Does the production lot yield strictly meet or exceed baseline target?",
                    value="",
                    size="xs",
                    minRows=3,
                    required=True,
                ),
                dmc.Select(
                    id="new-q-type",
                    label="TypeSafe Primitive",
                    data=[
                        {"value": "noul", "label": "Noul (Binary Judgment / P(yes))"},
                        {"value": "choice", "label": "Choice (Categorical Labels)"},
                        {"value": "score", "label": "Score (Ordinal Rubric)"},
                    ],
                    value="noul",
                    size="xs",
                ),
                dmc.TextInput(
                    id="new-q-choices",
                    label="Criteria / Options (comma-separated for Choice or Score)",
                    placeholder="e.g. solder_bridging, rf_plasma_drift, none",
                    value="",
                    size="xs",
                ),
                dmc.Group([
                    dmc.Checkbox(
                        id="new-q-required",
                        label="Required Check (Failure blocks auto-approval)",
                        checked=True,
                        size="xs",
                    ),
                    dmc.Checkbox(
                        id="new-q-needs-record",
                        label="Needs Audit Record",
                        checked=False,
                        size="xs",
                    ),
                ], gap="md"),
                dmc.Group(
                    justify="flex-end",
                    children=[
                        dmc.Button("Cancel", id="cancel-add-q-btn", variant="subtle", color="gray", size="xs"),
                        dmc.Button("Add to Questions", id="submit-add-q-btn", variant="filled", color="blue", size="xs"),
                    ],
                    mt="md",
                ),
            ], gap="sm"),
        ],
    )
