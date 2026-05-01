import json
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

api_key = os.getenv("METIS_API_KEY")
if not api_key:
    raise ValueError("METIS_API_KEY is missing")

_metis_rest = os.getenv("METIS_REST_API_ENDPOINT")
if not _metis_rest:
    raise RuntimeError("METIS_REST_API_ENDPOINT is not set")

genai.configure(
    api_key=api_key,
    transport="rest",
    client_options={"api_endpoint": _metis_rest.rstrip("/")},
)


def should_handoff_to_human(user_message: str) -> tuple[bool, str]:
    system_instruction = (
        "ناظر پشتیبانی. JSON بده: {\"handoff\": bool, \"reason\": str}.\n"
        "handoff true اگر کاربر خیلی عصبی است، "
        "مستقیم انسان می‌خواهد، یا مسئله حقوقی/مالی جدی مطرح است؛ "
        "وگرنه false."
    )

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-lite",
            system_instruction=system_instruction,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        response = model.generate_content(
            user_message, request_options={"timeout": 60}
        )
        result_dict = json.loads(response.text)
        return (
            bool(result_dict.get("handoff", False)),
            result_dict.get("reason", ""),
        )
    except Exception as e:
        print(f"handoff error: {e}")
        return True, type(e).__name__
