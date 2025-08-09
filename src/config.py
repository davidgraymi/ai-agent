import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "davidgraymi"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "openai" or "ollama"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3:8b")

STATE_FILE = ".agent_state.json"

DRY_RUN = bool(int(os.getenv("DRY_RUN", "1")))
