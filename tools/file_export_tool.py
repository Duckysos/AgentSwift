from pathlib import Path
from typing import Optional

try:  # Optional PDF export dependency
    from fpdf import FPDF
except Exception:  # pragma: no cover - optional import
    FPDF = None

try:  # Optional DOCX export dependency
    from docx import Document
except Exception:  # pragma: no cover - optional import
    Document = None

from schemas import CandidateProfile, DraftContent, JobRequirements


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return True
    if stripped.endswith(":"):
        return True
    if len(stripped.split()) == 1 and stripped.isupper():
        return True
    return False


def _normalize_bullets(text: str) -> str:
    """
    Ensure bullet-friendly formatting: prefix non-heading, non-empty lines with "- ".
    Leaves existing bullets intact.
    """
    normalized = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            normalized.append("")
            continue
        if _looks_like_heading(stripped):
            normalized.append(stripped)
            continue
        if stripped[0] in {"-", "*", "•"}:
            normalized.append(f"- {stripped.lstrip('-*•').strip()}")
            continue
        normalized.append(f"- {stripped}")
    return "\n".join(normalized)


def render_markdown(
    draft: DraftContent,
    profile: Optional[CandidateProfile] = None,
    jd: Optional[JobRequirements] = None,
) -> str:
    """
    Render a simple, consistent Markdown template for resume + cover letter.
    Keeps formatting ATS-friendly (plain headings/bullets).
    """
    lines: list[str] = []
    if profile:
        lines.extend(
            [
                f"# {profile.name or 'Candidate'}",
                profile.contact if profile.contact else "",
                "",
            ]
        )
    lines.append("## Tailored Resume")
    lines.append("")
    lines.append(_normalize_bullets(draft.tailored_resume.strip()))
    lines.append("")
    if draft.tailored_cover:
        lines.append("## Cover Letter")
        lines.append("")
        lines.append(_normalize_bullets(draft.tailored_cover.strip()))
        lines.append("")
    if jd:
        lines.append("## Target Role")
        lines.append("")
        lines.append(f"- **Title:** {jd.title or 'TBD'}")
        lines.append(f"- **Company:** {jd.company or 'TBD'}")
        if jd.must_haves:
            lines.append(f"- **Must-haves:** {', '.join(jd.must_haves)}")
        if jd.nice_to_haves:
            lines.append(f"- **Nice-to-haves:** {', '.join(jd.nice_to_haves)}")
        lines.append("")
    return "\n".join(lines)


def _ensure_out_path(out_path: str | None, suffix: str) -> Path:
    if out_path:
        return Path(out_path)
    return Path(f"out.{suffix}")


def export_draft(
    draft: DraftContent,
    profile: Optional[CandidateProfile] = None,
    jd: Optional[JobRequirements] = None,
    fmt: str = "md",
    out_path: str | None = None,
) -> str:
    """
    Convenience helper: render markdown template then export in chosen format.
    """
    md = render_markdown(draft, profile=profile, jd=jd)
    return export_content(md, fmt=fmt, out_path=out_path)


def export_content(draft_text: str, fmt: str = "md", out_path: str | None = None) -> str:
    """
    Export draft text to md/txt (always) or pdf/docx (if dependencies installed).
    """
    fmt = fmt.lower()
    if fmt in {"md", "markdown"}:
        path = _ensure_out_path(out_path, "md")
        path.write_text(draft_text, encoding="utf-8")
        return str(path)
    if fmt in {"txt", "text"}:
        path = _ensure_out_path(out_path, "txt")
        path.write_text(draft_text, encoding="utf-8")
        return str(path)
    if fmt == "pdf":
        if FPDF is None:
            raise ImportError("fpdf not installed; install with `pip install fpdf` to export PDF.")
        path = _ensure_out_path(out_path, "pdf")
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for line in draft_text.splitlines():
            pdf.multi_cell(0, 8, line)
        pdf.output(str(path))
        return str(path)
    if fmt in {"docx", "doc"}:
        if Document is None:
            raise ImportError("python-docx not installed; install with `pip install python-docx` to export DOCX.")
        path = _ensure_out_path(out_path, "docx")
        doc = Document()
        for line in draft_text.splitlines():
            doc.add_paragraph(line)
        doc.save(str(path))
        return str(path)
    raise ValueError("Unsupported export format. Use md, txt, pdf, or docx.")
