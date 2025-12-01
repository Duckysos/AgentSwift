"""
ADK Web app entrypoint.
Run with: adk web --app adk_app:web_app --host 0.0.0.0 --port 8000
"""
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from google import adk
except Exception as exc:  # pragma: no cover - ADK not installed in some envs
    raise ImportError("google-adk is required. Install with `pip install google-adk[web]`." ) from exc

from agents.orchestrator import SwiftOrchestratorAgent
from tools.file_export_tool import render_markdown

if load_dotenv:
    load_dotenv()


def tailor_resume(resume_path: str, jd_text: str, offline: bool = False):
    """Tailor a resume to a job description.

    Args:
        resume_path: path to the resume file (saved to temp by ADK File input).
        jd_text: raw job posting text.
        offline: if True, disables LLM calls and uses heuristic fallbacks.
    """
    orchestrator = SwiftOrchestratorAgent()
    if offline:
        orchestrator.jd_analyzer.use_llm = False
        orchestrator.matcher.use_llm = False
        orchestrator.writer.use_llm = False
        orchestrator.editor.use_llm = False
    draft = orchestrator.run(resume_path, jd_text)
    return {
        "tailored_resume": draft.tailored_resume,
        "tailored_cover": draft.tailored_cover,
        "markdown": render_markdown(draft),
    }


@adk.tool()
def tailor_resume_tool(resume_file: adk.File, jd_text: str, offline: bool = False):
    """ADK tool wrapper for tailoring resumes.

    Upload resume (pdf/txt/md), provide JD text, and optionally force offline mode.
    """
    resume_path = resume_file.save_to_temp()
    return tailor_resume(resume_path, jd_text, offline=offline)


@adk.tool()
def tailor_resume_text_tool(resume_text: str, jd_text: str, offline: bool = False):
    """Tailor using pasted resume and JD text (chat-friendly)."""
    # Save the resume text to a temp file for reuse by the parser
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
        tmp.write(resume_text)
        resume_path = tmp.name
    return tailor_resume(resume_path, jd_text, offline=offline)


# Chat-style agent that can call either tool
chat_agent = adk.Agent(
    tools=[tailor_resume_tool, tailor_resume_text_tool],
    instructions="You help tailor resumes to job descriptions. If the user uploads a file, use tailor_resume_tool. If they paste resume text, use tailor_resume_text_tool with their pasted resume and JD.",
)

web_app = adk.web.App(
    tools=[tailor_resume_tool, tailor_resume_text_tool],
    agent=chat_agent,
    title="Resume Tailor",
    description="Tailors a resume and cover letter to a job posting using Gemini when available.",
)
