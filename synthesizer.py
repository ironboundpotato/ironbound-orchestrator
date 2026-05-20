from orchestrator import call_model


def build_synthesis_prompt(responses):
    """
    Build the synthesis instruction prompt.
    """

    formatted_responses = ""

    for model_name, response in responses.items():
        formatted_responses += f"\n{model_name} RESPONSE:\n{response}\n"

    synthesis_prompt = f"""
You are a synthesis engine.

Compare the following AI model responses.

Your task:

1. Identify consensus points
2. Identify disagreements
3. Identify unique insights
4. Produce a final synthesized answer

Do not invent claims not present in the responses.

MODEL RESPONSES:
{formatted_responses}
"""

    return synthesis_prompt


def synthesize_responses(responses):
    """
    Use GPT as the synthesis model.
    """

    synthesis_prompt = build_synthesis_prompt(responses)

    synthesis_output = call_model(
        "GPT",
        synthesis_prompt
    )

    return synthesis_output