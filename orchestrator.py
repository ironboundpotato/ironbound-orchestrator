import requests

from config import (
    OPENROUTER_BASE_URL,
    HEADERS,
    MODELS
)


def call_model(model_name, prompt):
    """
    Send a prompt to a selected model through OpenRouter.
    """

    if model_name not in MODELS:
        raise ValueError(f"Unknown model: {model_name}")

    model_id = MODELS[model_name]

    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 300
    }

    response = requests.post(
        OPENROUTER_BASE_URL,
        headers=HEADERS,
        json=payload,
        timeout=60
    )

    if not response.ok:
        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        raise RuntimeError(
            f"OpenRouter Error ({response.status_code})\n"
            f"Model: {model_id}\n"
            f"Response: {error_data}"
        )

    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        raise RuntimeError(
            f"Unexpected OpenRouter response format:\n{data}"
        )