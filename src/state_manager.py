import json
from typing import Optional, Dict
from src.config import STATE_FILE

def save_state(issue_number: int, history: list, metadata: Optional[Dict]=None):
    state = {"issue_number": issue_number, "history": history, "metadata": metadata or {}}
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
