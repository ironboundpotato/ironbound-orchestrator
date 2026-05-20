import streamlit as st

from orchestrator import call_model
from synthesizer import synthesize_responses
from config import MODELS


st.set_page_config(
    page_title="Ironbound Orchestrator",
    page_icon="⚙️",
    layout="wide"
)

st.title("IRONBOUND ORCHESTRATOR")
st.caption("One prompt. Multiple models. One synthesized answer.")

prompt = st.text_area(
    "Enter prompt",
    height=160,
    placeholder="Explain whether AI governance matters."
)

selected_models = st.multiselect(
    "Select models",
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
        responses = {}

        st.subheader("Model Outputs")

        for model_name in selected_models:
            with st.spinner(f"Calling {model_name}..."):
                try:
                    output = call_model(model_name, prompt)
                    responses[model_name] = output

                    with st.expander(f"{model_name} Output", expanded=True):
                        st.write(output)

                except Exception as error:
                    responses[model_name] = f"ERROR: {error}"

                    with st.expander(f"{model_name} Error", expanded=True):
                        st.error(str(error))

        successful_responses = {
            name: text
            for name, text in responses.items()
            if not text.startswith("ERROR:")
        }

        if len(successful_responses) >= 2:
            st.subheader("Synthesis")

            with st.spinner("Synthesizing responses..."):
                try:
                    synthesis = synthesize_responses(successful_responses)
                    st.write(synthesis)
                except Exception as error:
                    st.error(f"Synthesis failed: {error}")

        elif len(successful_responses) == 1:
            st.warning("Only one model succeeded. Need at least two successful outputs for synthesis.")
        else:
            st.error("No models succeeded.")