"""
Modal for editing existing decision questions on the fly (name, type, instructions, criteria).
Edits are stored in-memory without altering data/example.json.
"""
import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify


def create_edit_question_modal():
    return dmc.Modal(
        id="edit-question-modal",
        title=dmc.Group([
            DashIconify(icon="tabler:edit", width=18, color="#38bdf8"),
            dmc.Text("Edit Decision Check", fw=600, size="sm"),
        ], gap=8),
        opened=False,
        size="lg",
        children=[
            dcc.Store(id="editing-question-id-store", data=""),
            dmc.Stack([
                dmc.TextInput(
                    id="edit-q-name",
                    label="Identifier / Key Name",
                    placeholder="e.g. yield_target_met",
                    value="",
                    size="xs",
                    required=True,
                ),
                dmc.Select(
                    id="edit-q-type",
                    label="TypeSafe Primitive",
                    data=[
                        {"value": "noul", "label": "Noul (Binary Judgment / P(yes))"},
                        {"value": "choice", "label": "Choice (Categorical Labels)"},
                        {"value": "score", "label": "Score (Ordinal Rubric)"},
                    ],
                    value="noul",
                    size="xs",
                    allowDeselect=False,
                ),
                dmc.Textarea(
                    id="edit-q-instructions",
                    label="Decision Instructions / Prompt",
                    placeholder="e.g. Does the production lot yield strictly meet or exceed baseline target?",
                    value="",
                    size="xs",
                    minRows=3,
                    autosize=True,
                    required=True,
                ),
                # Criteria container for Noul
                html.Div(
                    id="edit-q-noul-container",
                    style={"display": "block"},
                    children=[
                        dmc.Text("Noul Criteria (Optional clarification of True / False)", size="xs", fw=500, c="#94a3b8", mb=4),
                        dmc.Textarea(
                            id="edit-q-noul-true",
                            label="True Condition (Nominal / Pass definition)",
                            placeholder="e.g. Yield meets or exceeds 98.5% with zero lot rejection.",
                            minRows=2,
                            autosize=True,
                            size="xs",
                            mb="xs",
                        ),
                        dmc.Textarea(
                            id="edit-q-noul-false",
                            label="False Condition (Failure / Non-conformance definition)",
                            placeholder="e.g. Yield fell below 98.5% or lot was placed on quality hold.",
                            minRows=2,
                            autosize=True,
                            size="xs",
                        ),
                    ],
                ),
                # Criteria container for Choice
                html.Div(
                    id="edit-q-choice-container",
                    style={"display": "none"},
                    children=[
                        dmc.Text("Choice Criteria (Options & Descriptions)", size="xs", fw=500, c="#94a3b8", mb=2),
                        dmc.Text("Enter one option per line in 'option_name: description' format:", size="xs", c="dimmed", mb=4, style={"fontSize": "11px"}),
                        dmc.Textarea(
                            id="edit-q-choice-text",
                            placeholder="solder_bridging: Solder bridging or short circuit defects\nrf_plasma_drift: RF plasma excursion or drift\nnone: Nominal execution within spec",
                            minRows=5,
                            autosize=True,
                            size="xs",
                        ),
                    ],
                ),
                # Criteria container for Score
                html.Div(
                    id="edit-q-score-container",
                    style={"display": "none"},
                    children=[
                        dmc.Text("Score Rubric (Ordered Levels from Lowest to Highest)", size="xs", fw=500, c="#94a3b8", mb=2),
                        dmc.Text("Enter one rubric level per line (Level 0, Level 1, Level 2...):", size="xs", c="dimmed", mb=4, style={"fontSize": "11px"}),
                        dmc.Textarea(
                            id="edit-q-score-text",
                            placeholder="Nominal run with continuous flow and zero downtime.\nMinor nuisance alert cleared rapidly with zero scrap.\nModerate excursion with line pause or partial hold.\nCritical equipment fault or severe thermal hazard.",
                            minRows=5,
                            autosize=True,
                            size="xs",
                        ),
                    ],
                ),
                dmc.Group(
                    justify="flex-end",
                    children=[
                        dmc.Button("Cancel", id="cancel-edit-q-btn", variant="subtle", color="gray", size="xs"),
                        dmc.Button("Save Changes", id="save-edit-q-btn", variant="filled", color="blue", size="xs"),
                    ],
                    mt="md",
                ),
            ], gap="sm"),
        ],
    )
