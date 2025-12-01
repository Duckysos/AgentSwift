from typing import Optional

try:
    from google import genai
except Exception:  # pragma: no cover - optional dependency for offline tests
    genai = None

from schemas import CandidateProfile
from tools.resume_parsing_util import parse_resume


class ResumeParserAgent:
    def __init__(self, model: str = "gemini-1.5-pro", llm_client=None, use_llm: bool = True):
        self.use_llm = use_llm
        self.llm = llm_client if llm_client is not None else None
        if self.llm is None and self.use_llm and genai is not None and hasattr(genai, "GenerativeModel"):
            self.llm = genai.GenerativeModel(model)

    def run(self, resume_path: str) -> CandidateProfile:
        parsed = parse_resume(resume_path)
        return parsed
