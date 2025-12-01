import json
import re
from typing import Any, Dict


def extract_json_block(text: str) -> Dict[str, Any]:
    """
    Extract the first JSON object from an LLM response. Handles code fences and mixed prose.
    Returns an empty dict on failure to keep callers resilient.
    """
    if not text:
        return {}
    # Prefer fenced JSON blocks
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    # Fallback: first curly-brace block
    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        candidate = brace_match.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return {}
    return {}
