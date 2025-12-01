import os
import tempfile
import unittest

try:
    import PyPDF2  # noqa: F401
except Exception:
    PyPDF2 = None

try:
    from fpdf import FPDF  # noqa: F401
except Exception:
    FPDF = None

from agents.jd_analyzer import JDAnalyzerAgent
from agents.resume_jd_matcher import ResumeJDMatcherAgent
from agents.resume_parser import ResumeParserAgent
from agents.swift_editor import SwiftEditorAgent
from agents.swift_writer import SwiftWriterAgent
from agents.orchestrator import SwiftOrchestratorAgent
from schemas import DraftContent
from tools.file_export_tool import export_content, export_draft, render_markdown
from tools.resume_parsing_util import parse_resume


class _StubResponse:
    def __init__(self, text: str):
        self.text = text


class _StubLLM:
    def __init__(self, text: str):
        self._text = text

    def generate_content(self, prompt: str):
        return _StubResponse(self._text)


class PipelineTests(unittest.TestCase):
    def test_orchestrator_fallback_pipeline(self):
        fd, resume_path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            with open(resume_path, "w", encoding="utf-8") as handle:
                handle.write(
                    "Jane Doe\n"
                    "jane@example.com\n"
                    "Skills: Python, NLP\n"
                    "Experience: ML Engineer\n"
                    "Education: BS CS\n"
                )

            jd_text = "Job: ML Engineer\nMust have: Python; NLP"
            jd_llm = _StubLLM(
                '{"title":"ML Engineer","company":"Acme","must_haves":["Python","NLP"],"nice_to_haves":["Leadership"],"responsibilities":["Build models"]}'
            )
            matcher_llm = _StubLLM(
                '{"gaps":["Leadership"],"positioning":["Impact-driven"],"rewriting_focus":["Highlight NLP results"]}'
            )

            orchestrator = SwiftOrchestratorAgent(
                resume_parser=ResumeParserAgent(llm_client=_StubLLM(""), use_llm=False),
                jd_analyzer=JDAnalyzerAgent(llm_client=jd_llm, use_llm=True),
                matcher=ResumeJDMatcherAgent(llm_client=matcher_llm, use_llm=True),
                writer=SwiftWriterAgent(use_llm=False),
                editor=SwiftEditorAgent(use_llm=False),
            )

            draft = orchestrator.run(resume_path, jd_text)
            self.assertIn("Jane Doe", draft.tailored_resume)
            self.assertTrue(draft.tailored_cover)
        finally:
            os.remove(resume_path)

    def test_editor_validation_flags_missing_cover(self):
        editor = SwiftEditorAgent(use_llm=False)
        draft = DraftContent(tailored_resume="Test resume", tailored_cover="")
        _, validation = editor.run(draft)
        self.assertFalse(validation.passes)
        self.assertTrue(any("cover" in reason.lower() for reason in validation.reasons))

    def test_editor_llm_retry_wrapper_handles_exception(self):
        class FailingLLM:
            def __init__(self):
                self.calls = 0

            def generate_content(self, prompt: str):
                self.calls += 1
                raise RuntimeError("fail")

        editor = SwiftEditorAgent(llm_client=FailingLLM(), use_llm=True)
        draft = DraftContent(tailored_resume="Test resume", tailored_cover="Hi")
        _, validation = editor.run(draft, required_keywords=["Test"])
        # Should retry the LLM at least twice then fall back to deterministic validation (passes here)
        self.assertGreaterEqual(editor.llm.client.calls, 2)
        self.assertTrue(validation.passes)

    def test_editor_validation_missing_keywords(self):
        editor = SwiftEditorAgent(use_llm=False)
        draft = DraftContent(tailored_resume="Resume body without keywords", tailored_cover="Cover text")
        _, validation = editor.run(draft, required_keywords=["Python", "NLP"])
        self.assertFalse(validation.passes)
        self.assertTrue(any("missing required keywords" in r.lower() for r in validation.reasons))

    def test_export_markdown(self):
        out_path = export_content("hello", fmt="md")
        self.assertTrue(os.path.exists(out_path))
        os.remove(out_path)

    def test_render_markdown_template(self):
        draft = DraftContent(tailored_resume="Resume body", tailored_cover="Cover body")
        md = render_markdown(draft)
        self.assertIn("Tailored Resume", md)
        self.assertIn("Cover Letter", md)

    def test_render_markdown_normalizes_bullets(self):
        draft = DraftContent(tailored_resume="Line without bullet\n- Existing bullet", tailored_cover=None)
        md = render_markdown(draft)
        self.assertIn("- Line without bullet", md)
        self.assertIn("- Existing bullet", md)

    def test_export_draft_convenience(self):
        draft = DraftContent(tailored_resume="Body", tailored_cover=None)
        path = export_draft(draft, fmt="md", out_path="tmp_export.md")
        self.assertTrue(os.path.exists(path))
        os.remove(path)

    def test_export_pdf_dependency_guard(self):
        if FPDF is None:
            with self.assertRaises(ImportError):
                export_content("hello", fmt="pdf")
        else:
            out_path = export_content("hello", fmt="pdf")
            self.assertTrue(os.path.exists(out_path))
            os.remove(out_path)

    def test_parse_pdf_dependency_guard(self):
        if PyPDF2 is None:
            fd, tmp_pdf = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            try:
                with self.assertRaises(ImportError):
                    parse_resume(tmp_pdf)
            finally:
                os.remove(tmp_pdf)
        else:
            self.skipTest("PyPDF2 installed; integration PDF parse not exercised here.")

    def test_parse_multiline_sections(self):
        fd, tmp = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            with open(tmp, "w", encoding="utf-8") as handle:
                handle.write(
                    "Jane Doe\n"
                    "jane@example.com\n"
                    "Skills:\n"
                    "Python, NLP, SQL\n"
                    "Experience:\n"
                    "- ML Engineer\n"
                    "Education:\n"
                    "BS CS\n"
                )
            profile = parse_resume(tmp)
            self.assertIn("Python", profile.skills)
            self.assertIn("ML Engineer", profile.experience)
            self.assertIn("BS CS", profile.education)
        finally:
            os.remove(tmp)


if __name__ == "__main__":
    unittest.main()
