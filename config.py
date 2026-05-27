import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")

if not OPENROUTER_API_KEY:
    raise ValueError("Missing OPENROUTER_API_KEY in .env")

if not OPENROUTER_BASE_URL:
    raise ValueError("Missing OPENROUTER_BASE_URL in .env")

MODELS = {
    "GPT": "openai/gpt-4.1-mini",
    "Claude": "anthropic/claude-sonnet-4.5",
    "Gemini": "google/gemini-2.5-flash",
    "Grok": "x-ai/grok-3-mini-beta"
}

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}