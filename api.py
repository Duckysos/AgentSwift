"""
Minimal FastAPI app for uploading resume/JD and returning tailored content.
Requires fastapi and uvicorn to be installed.
"""
from typing import Optional

try:
    from fastapi import FastAPI, UploadFile, Form
except Exception as exc:  # pragma: no cover - optional dependency
    raise ImportError("FastAPI not installed. Install with `pip install fastapi uvicorn`.") from exc

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from agents.orchestrator import SwiftOrchestratorAgent

app = FastAPI(title="Resume Tailor API")

if load_dotenv:
    load_dotenv()


@app.post("/tailor")
async def tailor_resume(
    resume_file: UploadFile,
    jd_file: UploadFile,
    offline: Optional[bool] = Form(False),
):
    resume_bytes = await resume_file.read()
    jd_bytes = await jd_file.read()
    resume_path = f"/tmp/{resume_file.filename}"
    jd_path = f"/tmp/{jd_file.filename}"
    with open(resume_path, "wb") as f:
        f.write(resume_bytes)
    with open(jd_path, "wb") as f:
        f.write(jd_bytes)

    with open(jd_path, "r", encoding="utf-8", errors="ignore") as fh:
        jd_text = fh.read()

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
    }
