import json
import os
from datetime import datetime

from orchestrator import call_model
from synthesizer import synthesize_responses


LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "council_runs.jsonl")


def ensure_log_directory():
    os.makedirs(LOG_DIR, exist_ok=True)


def write_audit_log(audit_record):
    ensure_log_directory()

    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(audit_record, ensure_ascii=False) + "\n")


def run_council_deliberation(prompt):
    execution_start = datetime.utcnow()

    execution_trace = [
        "User Prompt",
        "Governance Gate",
        "Council Orchestrator",
        "GPT Architect",
        "Claude Critique",
        "Gemini Expansion",
        "Challenge Pass",
        "Synthesis Engine",
        "D.A.D. Audit Layer"
    ]

    council_outputs = {}

    gpt_prompt = f"""
You are the Architect model in a controlled AI council.

Task:
Answer the user's prompt clearly, structurally, and directly.

Constraints:
- Do not mention being in a council.
- Do not speculate beyond the prompt.
- Do not create autonomous actions.
- Keep the answer useful and grounded.

User prompt:
{prompt}
"""

    gpt_response = call_model("GPT", gpt_prompt)
    council_outputs["GPT Architect"] = gpt_response

    claude_prompt = f"""
You are the Critique model in a controlled AI council.

Task:
Review the Architect's answer.

Evaluate:
- assumptions
- weak reasoning
- missing context
- unsupported claims
- places where the answer could be clearer

Constraints:
- Do not rewrite the full answer.
- Do not be hostile.
- Be precise and constructive.
- Keep the critique grounded in the user prompt.

User prompt:
{prompt}

Architect answer:
{gpt_response}
"""

    claude_response = call_model("Claude", claude_prompt)
    council_outputs["Claude Critique"] = claude_response

    gemini_prompt = f"""
You are the Expansion model in a controlled AI council.

Task:
Use the original prompt, the Architect answer, and the Critique to produce an improved response.

You should:
- preserve strong points
- correct weak points
- add missing context
- resolve obvious gaps
- produce a clearer, stronger answer

Constraints:
- Do not introduce unrelated concepts.
- Do not create autonomous actions.
- Do not claim certainty where uncertainty remains.

User prompt:
{prompt}

Architect answer:
{gpt_response}

Critique:
{claude_response}
"""

    gemini_response = call_model("Gemini", gemini_prompt)
    council_outputs["Gemini Expansion"] = gemini_response

    challenge_prompt = f"""
You are the Challenge Pass inside a controlled AI council.

Task:
Analyze the Architect answer, Critique, and Expansion.

Produce a concise challenge map with these sections:

1. Consensus:
What do the responses agree on?

2. Disagreements:
Where do the responses conflict, diverge, or emphasize different priorities?

3. Weak Assumptions:
What assumptions remain unsupported or under-examined?

4. Strongest Reasoning:
Which points appear most useful, grounded, or durable?

5. Synthesis Instructions:
What should the final synthesis preserve, correct, remove, or clarify?

Constraints:
- Do not answer the user directly.
- Do not introduce unrelated topics.
- Do not invent facts.
- Be concise and operational.
- Focus on improving final synthesis quality.

User prompt:
{prompt}

Architect answer:
{gpt_response}

Critique:
{claude_response}

Expansion:
{gemini_response}
"""

    challenge_response = call_model("Claude", challenge_prompt)
    council_outputs["Challenge Pass"] = challenge_response

    synthesis_inputs = {
        "GPT Architect": gpt_response,
        "Claude Critique": claude_response,
        "Gemini Expansion": gemini_response,
        "Challenge Pass": challenge_response
    }

    final_synthesis = synthesize_responses(synthesis_inputs)

    execution_end = datetime.utcnow()
    execution_time = round((execution_end - execution_start).total_seconds(), 2)

    audit_record = {
        "timestamp_utc": execution_start.isoformat(),
        "execution_mode": "Council Deliberation",
        "prompt": prompt,
        "execution_trace": execution_trace,
        "council_outputs": council_outputs,
        "final_synthesis": final_synthesis,
        "execution_time_seconds": execution_time
    }

    write_audit_log(audit_record)

    return {
        "prompt": prompt,
        "execution_trace": execution_trace,
        "council_outputs": council_outputs,
        "final_synthesis": final_synthesis,
        "execution_time_seconds": execution_time
    }