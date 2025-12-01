try:
    from google import genai
except Exception:  # pragma: no cover - optional dependency for offline tests
    genai = None

from agents.common import extract_json_block
from agents.llm_utils import LLMClientWrapper
from config import ModelConfig
from schemas import JobRequirements


class JDAnalyzerAgent:
    def __init__(self, config: ModelConfig | None = None, llm_client=None, use_llm: bool = True):
        config = config or ModelConfig()
        self.use_llm = use_llm
        self.llm = None
        if llm_client is not None:
            self.llm = LLMClientWrapper(llm_client, max_retries=config.max_retries)
        elif self.use_llm and genai is not None and hasattr(genai, "GenerativeModel"):
            self.llm = LLMClientWrapper(genai.GenerativeModel(config.jd_model), max_retries=config.max_retries)

    def run(self, jd_text: str) -> JobRequirements:
        if not jd_text:
            return JobRequirements(
                title="TBD",
                company="TBD",
                must_haves=[],
                nice_to_haves=[],
                responsibilities=[],
                location=None,
            )

        if self.llm is None or not self.use_llm:
            lines = [ln.strip() for ln in jd_text.splitlines() if ln.strip()]
            title = lines[0] if lines else "TBD"
            company = "TBD"
            must_haves = []
            for line in lines:
                lower = line.lower()
                if lower.startswith("company"):
                    company = line.split(":", 1)[-1].strip() or company
                if "must have" in lower or "must-have" in lower:
                    tokens = line.split(":", 1)[-1].replace(";", ",").split(",")
                    must_haves.extend([t.strip() for t in tokens if t.strip()])
            return JobRequirements(
                title=title,
                company=company,
                must_haves=must_haves,
                nice_to_haves=[],
                responsibilities=[],
                location=None,
            )

        prompt = (
            "Extract structured requirements from this job posting. "
            "Respond ONLY with JSON inside a code fence. Schema:\n"
            "{\"title\": str, \"company\": str, \"must_haves\": [str], \"nice_to_haves\": [str], \"responsibilities\": [str], \"location\": str|null}\n\n"
            f"Job posting:\n{jd_text}\n"
        )
        try:
            result = self.llm.generate_text(prompt)
        except Exception:
            result = ""

        payload = extract_json_block(result)

        def _list(key: str):
            value = payload.get(key, [])
            return value if isinstance(value, list) else [str(value)]

        return JobRequirements(
            title=str(payload.get("title", "TBD")),
            company=str(payload.get("company", "TBD")),
            must_haves=_list("must_haves"),
            nice_to_haves=_list("nice_to_haves"),
            responsibilities=_list("responsibilities"),
            location=payload.get("location"),
        )
