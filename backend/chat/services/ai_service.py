import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
AI_PATH = os.path.join(BASE_DIR, "AI")
sys.path.append(AI_PATH)

from llm import get_ai_response


def ask_ai(question: str, chat_history: list = None):
    try:
        return get_ai_response(question, chat_history or [])
    except Exception as e:
        print(f"ask_ai: {e}")
        return {
            "response": f"AI Error: {str(e)}",
            "handoff_required": False,
            "handoff_reason": None,
            "monitoring": {"path": "service_error", "hint": "error", "detail": str(e)},
        }
