import json

try:
    from google import genai
except Exception:  # pragma: no cover - optional dependency for offline tests
    genai = None

from agents.llm_utils import LLMClientWrapper
from config import ModelConfig, ValidationConfig
from schemas import DraftContent, ValidationResult


class SwiftEditorAgent:
    def __init__(self, config: ModelConfig | None = None, llm_client=None, use_llm: bool = True):
        config = config or ModelConfig()
        self.use_llm = use_llm
        self.llm = None
        if llm_client is not None:
            self.llm = LLMClientWrapper(llm_client, max_retries=config.max_retries)
        elif self.use_llm and genai is not None and hasattr(genai, "GenerativeModel"):
            self.llm = LLMClientWrapper(genai.GenerativeModel(config.editor_model), max_retries=config.max_retries)
        self.validation_config = ValidationConfig()

    def _validate(self, draft: DraftContent, required_keywords: list[str] | None = None, max_words: int | None = None) -> ValidationResult:
        max_words = max_words or self.validation_config.max_words
        reasons = []
        suggestions = []
        text = f"{draft.tailored_resume}\n{draft.tailored_cover or ''}".lower()
        total_words = len(text.split())

        if not draft.tailored_resume.strip():
            reasons.append("Resume content is empty")
            suggestions.append("Add resume content")
        if not draft.tailored_cover:
            reasons.append("Cover letter missing")
            suggestions.append("Include a tailored cover letter")

        if required_keywords:
            missing = [kw for kw in required_keywords if kw and kw.lower() not in text]
            if missing:
                reasons.append(f"Missing required keywords: {', '.join(missing)}")
                suggestions.append(f"Incorporate keywords: {', '.join(missing)}")

        if total_words > max_words:
            reasons.append(f"Content too long ({total_words} words > {max_words})")
            suggestions.append("Trim content to fit length guidance")

        passes = not reasons
        return ValidationResult(passes=passes, reasons=reasons, suggestions=suggestions or None)

    def run(
        self,
        draft: DraftContent,
        required_keywords: list[str] | None = None,
        max_words: int | None = None,
    ) -> tuple[DraftContent, ValidationResult]:
        if self.llm is None or not self.use_llm:
            return draft, self._validate(draft, required_keywords, max_words)

        max_words = max_words or self.validation_config.max_words
        prompt = f"""Review and improve the draft for ATS-friendliness, clarity, and alignment.
Draft JSON: {draft.model_dump_json()}
Required keywords: {required_keywords or []}
Constraints:
- Keep bullets concise; avoid tables.
- Ensure required keywords appear naturally.
- Keep total content under {max_words} words.
Respond with two fenced blocks:
```resume
<revised resume+cover markdown>
```
```validation
{{"passes": bool, "reasons": [str], "suggestions": [str]}}
```
"""
        try:
            text = self.llm.generate_text(prompt)
        except Exception:
            return draft, self._validate(draft, required_keywords, max_words)

        resume_block_start = text.lower().find("```resume")
        if resume_block_start != -1:
            after = text[resume_block_start:]
            end = after.find("```", len("```resume"))
            if end != -1:
                resume_text = after[len("```resume") : end].strip()
                draft = DraftContent(tailored_resume=resume_text, tailored_cover=draft.tailored_cover)

        validation_start = text.lower().find("```validation")
        validation = None
        if validation_start != -1:
            after = text[validation_start:]
            end = after.find("```", len("```validation"))
            if end != -1:
                try:
                    payload = json.loads(after[len("```validation") : end].strip())
                    validation = ValidationResult(**payload)
                except Exception:
                    validation = None

        validation = validation or self._validate(draft, required_keywords, max_words)
        return draft, validation
