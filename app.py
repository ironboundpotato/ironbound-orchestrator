import json
import os
import html
import streamlit as st
import time

from orchestrator import call_model
from synthesizer import synthesize_responses
from config import MODELS
from council import run_council_deliberation
from governance import evaluate_prompt


LOG_FILE = "logs/council_runs.jsonl"


st.set_page_config(
    page_title="Ironbound Orchestrator",
    page_icon="⚙️",
    layout="wide"
)


st.markdown(
    """
    <style>
    .council-box {
        border: 1px solid #d0d0d0;
        border-radius: 12px;
        padding: 18px;
        background-color: #fafafa;
        height: 520px;
        overflow-y: auto;
        margin-bottom: 18px;
        line-height: 1.55;
        white-space: pre-wrap;
    }

    .standard-box {
        border: 1px solid #d0d0d0;
        border-radius: 12px;
        padding: 18px;
        background-color: #fafafa;
        height: 480px;
        overflow-y: auto;
        margin-bottom: 18px;
        line-height: 1.55;
        white-space: pre-wrap;
    }

    .synthesis-box {
        border: 1px solid #b8c7dc;
        border-radius: 12px;
        padding: 22px;
        background-color: #f6f9ff;
        max-height: 620px;
        overflow-y: auto;
        margin-top: 12px;
        margin-bottom: 18px;
        line-height: 1.6;
        white-space: pre-wrap;
    }

    .audit-box {
        border: 1px solid #d6d6d6;
        border-radius: 12px;
        padding: 16px;
        background-color: #fbfbfb;
        margin-bottom: 16px;
        line-height: 1.55;
        white-space: pre-wrap;
    }

    .governance-card {
        border: 1px solid #d8dee9;
        border-radius: 14px;
        padding: 18px;
        background-color: #fbfcff;
        margin-bottom: 16px;
        line-height: 1.5;
    }

    .rule-card {
        border: 1px solid #d6d6d6;
        border-radius: 12px;
        padding: 14px;
        background-color: #ffffff;
        margin-bottom: 12px;
    }

    .chip {
        display: inline-block;
        padding: 4px 10px;
        margin: 4px 4px 4px 0;
        border-radius: 999px;
        background-color: #eef2f7;
        border: 1px solid #ccd4df;
        font-size: 0.82rem;
    }

    .role-caption {
        font-size: 0.85rem;
        color: #666666;
        margin-bottom: 10px;
    }

    .status-complete {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background-color: #e8f5e9;
        border: 1px solid #b7dfbd;
        color: #1b5e20;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 12px;
    }

    .status-failed {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background-color: #ffebee;
        border: 1px solid #efb4b4;
        color: #b71c1c;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 12px;
    }

    .status-governed {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background-color: #eef4ff;
        border: 1px solid #b8c7dc;
        color: #173b6c;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def boxed_text(text, css_class):
    safe_text = html.escape(str(text))
    st.markdown(
        f'<div class="{css_class}">{safe_text}</div>',
        unsafe_allow_html=True
    )


def status_pill(label, status_type="complete"):
    css_class = "status-complete"

    if status_type == "failed":
        css_class = "status-failed"

    if status_type == "governed":
        css_class = "status-governed"

    st.markdown(
        f'<div class="{css_class}">{label}</div>',
        unsafe_allow_html=True
    )


def chip_list(items):
    if not items:
        st.caption("No trigger patterns matched.")
        return

    chip_html = ""

    for item in items:
        chip_html += f'<span class="chip">{html.escape(str(item))}</span>'

    st.markdown(chip_html, unsafe_allow_html=True)


def render_governance_decision(decision):
    st.subheader("Governance Gate")

    decision_value = decision.get("decision", "UNKNOWN")
    severity = decision.get("severity", "UNKNOWN")
    gate = decision.get("execution_gate", "UNKNOWN")
    confidence = decision.get("confidence", 0)
    risk_category = decision.get("risk_category", "Unknown")
    reason = decision.get("reason", "No reason provided.")

    if decision_value == "APPROVED":
        status_pill("APPROVED — EXECUTION GATE OPEN", "complete")
        st.success(reason)

    elif decision_value == "CLARIFICATION_REQUIRED":
        status_pill("CLARIFICATION REQUIRED — EXECUTION GATE CLOSED", "governed")
        st.warning(reason)

    elif decision_value == "REFUSED":
        status_pill("REFUSED — EXECUTION GATE CLOSED", "failed")
        st.error(reason)

    else:
        status_pill("UNKNOWN GOVERNANCE STATE", "failed")
        st.error("Unknown governance state.")

    st.markdown("### Governance Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Decision", decision_value)

    with col2:
        st.metric("Severity", severity)

    with col3:
        st.metric("Confidence", f"{round(confidence * 100)}%")

    with col4:
        st.metric("Execution Gate", gate)

    st.progress(float(confidence))

    st.markdown(
        f"""
        <div class="governance-card">
            <strong>Risk Category:</strong> {html.escape(str(risk_category))}<br><br>
            <strong>Governance Rationale:</strong><br>
            {html.escape(str(decision.get("governance_rationale", "No rationale generated.")))}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Trigger Patterns")
    chip_list(decision.get("matched_patterns", []))

    st.markdown("### Matched Rules")

    matched_rules = decision.get("matched_rules", [])

    if not matched_rules:
        st.info("No blocking or classification rules matched.")
    else:
        for rule in matched_rules:
            st.markdown(
                f"""
                <div class="rule-card">
                    <strong>Rule ID:</strong> {html.escape(str(rule.get("rule_id", "Unknown")))}<br>
                    <strong>Category:</strong> {html.escape(str(rule.get("category", "Unknown")))}<br>
                    <strong>Severity:</strong> {html.escape(str(rule.get("severity", "Unknown")))}<br>
                    <strong>Decision:</strong> {html.escape(str(rule.get("decision", "Unknown")))}<br>
                </div>
                """,
                unsafe_allow_html=True
            )

            chip_list(rule.get("matched_patterns", []))

    with st.expander("Raw Governance Record", expanded=False):
        st.json(decision)


def role_panel(title, caption, output):
    st.markdown(f"### {title}")
    st.markdown(
        f'<div class="role-caption">{caption}</div>',
        unsafe_allow_html=True
    )

    if output and not str(output).startswith("ERROR:"):
        status_pill("COMPLETE", "complete")
        boxed_text(output, "council-box")
    else:
        status_pill("FAILED", "failed")
        boxed_text(output or "No output.", "council-box")


st.title("IRONBOUND ORCHESTRATOR")
st.caption("Governed multi-model deliberation under deterministic orchestration.")


view_mode = st.radio(
    "Operator View",
    options=[
        "Run Orchestration",
        "D.A.D. Audit Viewer"
    ],
    horizontal=True
)


if view_mode == "Run Orchestration":

    mode = st.radio(
        "Execution Mode",
        options=[
            "Standard Orchestration",
            "Council Deliberation"
        ],
        horizontal=True
    )

    prompt = st.text_area(
        "Enter Prompt",
        height=180,
        placeholder="Explain why governed multi-model orchestration matters."
    )

    selected_models = st.multiselect(
        "Select Models",
        options=list(MODELS.keys()),
        default=list(MODELS.keys())
    )

    run_button = st.button("Run Orchestration")

    if run_button:

        if not prompt.strip():
            st.error("Enter a prompt before running orchestration.")

        elif not selected_models:
            st.error("Select at least one model.")

        else:

            start_time = time.time()

            governance_decision = evaluate_prompt(prompt)

            st.divider()
            render_governance_decision(governance_decision)

            if governance_decision["execution_gate"] == "CLOSED":

                st.stop()

            st.divider()
            st.subheader("Execution Trace")
            status_pill("GOVERNANCE PASSED", "complete")

            st.code(
                """
User Prompt
↓
Governance Gate
↓
APPROVED
↓
Council Orchestrator
↓
GPT Architect
↓
Claude Critique
↓
Gemini Expansion
↓
Synthesis Engine
↓
D.A.D. Audit Layer
                """,
                language="text"
            )

            if mode == "Standard Orchestration":

                responses = {}

                st.subheader("Model Outputs")

                columns = st.columns(len(selected_models))

                for index, model_name in enumerate(selected_models):

                    with columns[index]:

                        st.markdown(f"### {model_name}")

                        with st.spinner(f"Calling {model_name}..."):

                            try:
                                output = call_model(model_name, prompt)
                                responses[model_name] = output
                                status_pill("COMPLETE", "complete")
                                boxed_text(output, "standard-box")

                            except Exception as error:
                                responses[model_name] = f"ERROR: {error}"
                                status_pill("FAILED", "failed")
                                boxed_text(str(error), "standard-box")

                successful_responses = {
                    name: text
                    for name, text in responses.items()
                    if not text.startswith("ERROR:")
                }

                st.divider()

                if len(successful_responses) >= 2:

                    st.subheader("Synthesis Engine")

                    with st.spinner("Generating synthesis..."):

                        try:
                            synthesis = synthesize_responses(successful_responses)
                            status_pill("RECONCILED", "complete")
                            st.markdown("### Final Synthesized Output")
                            boxed_text(synthesis, "synthesis-box")

                        except Exception as error:
                            status_pill("FAILED", "failed")
                            st.error(f"Synthesis failed: {error}")

                elif len(successful_responses) == 1:

                    st.warning(
                        "Only one model succeeded. Need at least two successful outputs for synthesis."
                    )

                else:

                    st.error("No successful model outputs.")

            elif mode == "Council Deliberation":

                st.subheader("Council Deliberation")

                with st.spinner("Running governed council deliberation..."):

                    try:
                        result = run_council_deliberation(prompt)

                        st.success("Council deliberation completed successfully.")

                        st.divider()
                        st.markdown("## Council Deliberation View")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            role_panel(
                                "GPT Architect",
                                "Builds the initial structured reasoning foundation.",
                                result["council_outputs"].get("GPT Architect", "No output.")
                            )

                        with col2:
                            role_panel(
                                "Claude Critique",
                                "Challenges assumptions, coherence, and weak reasoning.",
                                result["council_outputs"].get("Claude Critique", "No output.")
                            )

                        with col3:
                            role_panel(
                                "Gemini Expansion",
                                "Expands context, implications, and synthesis quality.",
                                result["council_outputs"].get("Gemini Expansion", "No output.")
                            )

                        st.divider()
                        st.markdown("## Final Council Synthesis")
                        status_pill("RECONCILED", "complete")

                        st.info(
                            "The synthesis engine reconciles consensus points, "
                            "disagreements, and unique insights into one governed final answer."
                        )

                        boxed_text(result["final_synthesis"], "synthesis-box")

                    except Exception as error:
                        status_pill("FAILED", "failed")
                        st.error(f"Council deliberation failed: {error}")

            end_time = time.time()
            execution_time = round(end_time - start_time, 2)

            st.divider()
            st.subheader("Run Metrics")
            st.metric(label="Execution Time (seconds)", value=execution_time)
            st.caption("IRONBOUND ORCHESTRATOR v0.5.0")


if view_mode == "D.A.D. Audit Viewer":

    st.subheader("D.A.D. Audit Viewer")
    st.caption("Deterministic Audit Daemon — council deliberation history")

    if not os.path.exists(LOG_FILE):

        st.warning("No audit log found yet. Run Council Deliberation first.")

    else:

        with open(LOG_FILE, "r", encoding="utf-8") as log_file:
            lines = [
                line.strip()
                for line in log_file.readlines()
                if line.strip()
            ]

        if not lines:

            st.warning("Audit log exists but contains no records.")

        else:

            records = []

            for line in lines:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

            st.metric("Total Logged Council Runs", len(records))

            records = list(reversed(records))

            for index, record in enumerate(records, start=1):

                timestamp = record.get("timestamp_utc", "Unknown timestamp")
                prompt = record.get("prompt", "No prompt captured")

                with st.expander(
                    f"Run {index} — {timestamp}",
                    expanded=False
                ):

                    st.markdown("### Prompt")
                    boxed_text(prompt, "audit-box")

                    st.markdown("### Execution Trace")

                    trace = record.get("execution_trace", [])

                    st.code(
                        "\n↓\n".join(trace),
                        language="text"
                    )

                    st.markdown("### Council Outputs")

                    council_outputs = record.get("council_outputs", {})

                    output_columns = st.columns(3)

                    role_order = [
                        "GPT Architect",
                        "Claude Critique",
                        "Gemini Expansion"
                    ]

                    role_captions = {
                        "GPT Architect": "Initial structured reasoning.",
                        "Claude Critique": "Assumption and coherence pressure test.",
                        "Gemini Expansion": "Context and implication expansion."
                    }

                    for idx, role in enumerate(role_order):

                        with output_columns[idx]:

                            role_panel(
                                role,
                                role_captions.get(role, ""),
                                council_outputs.get(role, "No output.")
                            )

                    st.markdown("### Final Synthesis")
                    status_pill("RECONCILED", "complete")

                    boxed_text(
                        record.get("final_synthesis", "No synthesis captured."),
                        "synthesis-box"
                    )

                    st.markdown("### Run Metrics")

                    st.write(
                        f"Execution time: "
                        f"{record.get('execution_time_seconds', 'Unknown')} seconds"
                    )