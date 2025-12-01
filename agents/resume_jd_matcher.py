try:
    from google import genai
except Exception:  # pragma: no cover - optional dependency for offline tests
    genai = None

from agents.common import extract_json_block
from agents.llm_utils import LLMClientWrapper
from config import ModelConfig
from schemas import CandidateProfile, JobRequirements, StrategyPlan


class ResumeJDMatcherAgent:
    def __init__(self, config: ModelConfig | None = None, llm_client=None, use_llm: bool = True):
        config = config or ModelConfig()
        self.use_llm = use_llm
        self.llm = None
        if llm_client is not None:
            self.llm = LLMClientWrapper(llm_client, max_retries=config.max_retries)
        elif self.use_llm and genai is not None and hasattr(genai, "GenerativeModel"):
            self.llm = LLMClientWrapper(genai.GenerativeModel(config.matcher_model), max_retries=config.max_retries)

    def run(self, profile: CandidateProfile, jd: JobRequirements) -> StrategyPlan:
        if self.llm is None or not self.use_llm:
            gaps = [req for req in jd.must_haves if req not in profile.skills]
            positioning = [f"Highlight {skill}" for skill in profile.skills[:3]]
            focus = gaps[:3] if gaps else jd.responsibilities[:3]
            return StrategyPlan(gaps=gaps, positioning=positioning, rewriting_focus=focus)

        prompt = (
            "Given candidate profile (JSON) and job requirements (JSON), identify gaps, "
            "craft positioning, and list rewriting focus points. Respond ONLY with JSON in a code fence. Schema:\n"
            "{\"gaps\": [str], \"positioning\": [str], \"rewriting_focus\": [str]}\n\n"
            f"Profile: {profile.model_dump_json()}\nJD: {jd.model_dump_json()}"
        )
        try:
            text = self.llm.generate_text(prompt)
        except Exception:
            text = ""

        payload = extract_json_block(text)

        def _list(key: str):
            value = payload.get(key, [])
            return value if isinstance(value, list) else [str(value)]

        if not payload:
            gaps = [req for req in jd.must_haves if req not in profile.skills]
            positioning = [f"Highlight {skill}" for skill in profile.skills[:3]]
            focus = gaps[:3] if gaps else jd.responsibilities[:3]
            return StrategyPlan(gaps=gaps, positioning=positioning, rewriting_focus=focus)

        return StrategyPlan(
            gaps=_list("gaps"),
            positioning=_list("positioning"),
            rewriting_focus=_list("rewriting_focus"),
        )
