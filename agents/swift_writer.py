try:
    from google import genai
except Exception:  # pragma: no cover - optional dependency for offline tests
    genai = None

from agents.llm_utils import LLMClientWrapper
from config import ModelConfig
from schemas import CandidateProfile, JobRequirements, StrategyPlan, DraftContent


class SwiftWriterAgent:
    def __init__(self, config: ModelConfig | None = None, llm_client=None, use_llm: bool = True):
        config = config or ModelConfig()
        self.use_llm = use_llm
        self.llm = None
        if llm_client is not None:
            self.llm = LLMClientWrapper(llm_client, max_retries=config.max_retries)
        elif self.use_llm and genai is not None and hasattr(genai, "GenerativeModel"):
            self.llm = LLMClientWrapper(genai.GenerativeModel(config.writer_model), max_retries=config.max_retries)

    def _fallback_generate(self, profile: CandidateProfile, jd: JobRequirements, strategy: StrategyPlan) -> DraftContent:
        resume_lines = [
            f"{profile.name}",
            f"Contact: {profile.contact}",
            "",
            "Skills: " + ", ".join(profile.skills or ["TBD"]),
            "Experience: " + ", ".join(profile.experience or ["TBD"]),
            "Education: " + ", ".join(profile.education or ["TBD"]),
            "",
            "Strategy focus: " + "; ".join(strategy.rewriting_focus or strategy.gaps),
        ]
        cover_lines = [
            "Dear Hiring Manager,",
            f"I am excited to apply for the {jd.title} role at {jd.company}.",
            "I bring strengths in " + ", ".join(profile.skills[:3] or ["relevant skills"]),
            "Sincerely,",
            profile.name,
        ]
        return DraftContent(
            tailored_resume="\n".join(resume_lines),
            tailored_cover="\n".join(cover_lines),
        )

    def run(self, profile: CandidateProfile, jd: JobRequirements, strategy: StrategyPlan) -> DraftContent:
        if self.llm is None or not self.use_llm:
            return self._fallback_generate(profile, jd, strategy)

        prompt = f"""You are a resume+cover specialist. Write concise, ATS-friendly output.
Instructions:
- Keep to bullet-friendly formatting (no tables), short sentences, quantified impact where possible.
- Include keywords from the job where relevant.
- Output exactly two sections with markers:
[RESUME]
<resume markdown>
[/RESUME]
[COVER]
<cover letter markdown>
[/COVER]

Context:
Candidate: {profile.model_dump_json()}
Job: {jd.model_dump_json()}
Strategy: {strategy.model_dump_json()}
"""
        try:
            text = self.llm.generate_text(prompt)
        except Exception:
            return self._fallback_generate(profile, jd, strategy)

        lower = text.lower()
        resume_start = lower.find("[resume]")
        resume_end = lower.find("[/resume]")
        cover_start = lower.find("[cover]")
        cover_end = lower.find("[/cover]")
        if resume_start == -1 or resume_end == -1 or cover_start == -1:
            return self._fallback_generate(profile, jd, strategy)
        resume_text = text[resume_start + len("[resume]") : resume_end].strip()
        cover_text = None
        if cover_end != -1:
            cover_text = text[cover_start + len("[cover]") : cover_end].strip()
        return DraftContent(tailored_resume=resume_text, tailored_cover=cover_text or None)
