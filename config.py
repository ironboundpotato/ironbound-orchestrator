import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")

# Basic validation
if not OPENROUTER_API_KEY:
    raise ValueError("Missing OPENROUTER_API_KEY in .env")

if not OPENROUTER_BASE_URL:
    raise ValueError("Missing OPENROUTER_BASE_URL in .env")

# Stable verified models
MODELS = {
    "GPT": "openai/gpt-4o-mini",
    "Claude": "anthropic/claude-haiku-4.5",
    "Gemini": "google/gemini-2.0-flash-001"
}

# Shared request headers
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}