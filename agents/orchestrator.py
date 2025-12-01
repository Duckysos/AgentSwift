from agents.resume_parser import ResumeParserAgent
from agents.jd_analyzer import JDAnalyzerAgent
from agents.resume_jd_matcher import ResumeJDMatcherAgent
from agents.swift_writer import SwiftWriterAgent
from agents.swift_editor import SwiftEditorAgent
from config import ModelConfig
from logger import get_logger, redact
from schemas import DraftContent


class SwiftOrchestratorAgent:
    """Coordinates resume tailoring flow across specialized agents."""

    def __init__(
        self,
        resume_parser: ResumeParserAgent | None = None,
        jd_analyzer: JDAnalyzerAgent | None = None,
        matcher: ResumeJDMatcherAgent | None = None,
        writer: SwiftWriterAgent | None = None,
        editor: SwiftEditorAgent | None = None,
        max_editor_loops: int = 2,
        config: ModelConfig | None = None,
        pii_redact: bool = True,
    ):
        config = config or ModelConfig()
        self.resume_parser = resume_parser or ResumeParserAgent()
        self.jd_analyzer = jd_analyzer or JDAnalyzerAgent(config=config)
        self.matcher = matcher or ResumeJDMatcherAgent(config=config)
        self.writer = writer or SwiftWriterAgent(config=config)
        self.editor = editor or SwiftEditorAgent(config=config)
        self.max_editor_loops = max_editor_loops
        self.logger = get_logger()
        self.pii_redact = pii_redact

    def run(self, resume_path: str, jd_text: str) -> DraftContent:
        self.logger.info("Start orchestration")
        profile = self.resume_parser.run(resume_path)
        self.logger.info("Parsed resume for %s", redact(profile.name, self.pii_redact))

        jd = self.jd_analyzer.run(jd_text)
        self.logger.info("Analyzed JD: %s @ %s", jd.title, jd.company)

        strategy = self.matcher.run(profile, jd)
        self.logger.info("Strategy gaps: %s", ", ".join(strategy.gaps) if strategy.gaps else "none")

        draft = self.writer.run(profile, jd, strategy)
        self.logger.info("Writer produced draft")

        required_keywords = jd.must_haves
        last_validation = None
        for attempt in range(max(1, self.max_editor_loops)):
            draft, validation = self.editor.run(draft, required_keywords=required_keywords)
            last_validation = validation
            if validation.passes:
                self.logger.info("Validation passed on attempt %s", attempt + 1)
                return draft
            self.logger.warning("Validation failed (attempt %s): %s", attempt + 1, "; ".join(validation.reasons))
        if last_validation and last_validation.reasons:
            note = "\n\nValidation notes: " + "; ".join(last_validation.reasons)
            draft = DraftContent(tailored_resume=draft.tailored_resume + note, tailored_cover=draft.tailored_cover)
        return draft
