from pathlib import Path
from typing import List

try:  # Optional dependency for PDF parsing
    import PyPDF2
except Exception:  # pragma: no cover - optional import
    PyPDF2 = None

from schemas import CandidateProfile


def _read_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {file_path}")
    for encoding in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def _read_pdf_text(file_path: str) -> str:
    if PyPDF2 is None:
        raise ImportError("PyPDF2 not installed; install it or provide text/markdown resumes.")
    text_chunks: List[str] = []
    with open(file_path, "rb") as fh:
        reader = PyPDF2.PdfReader(fh)
        for page in reader.pages:
            text = page.extract_text() or ""
            text_chunks.append(text)
    return "\n".join(text_chunks)


def _extract_section(lines: List[str], label: str) -> List[str]:
    """
    Grab items following a 'Label:' line.
    Supports inline values and multi-line blocks until a blank or new heading.
    """
    items: List[str] = []
    for idx, line in enumerate(lines):
        lowered = line.lower()
        if lowered.startswith(f"{label.lower()}:"):
            content = line.split(":", 1)[1].strip()
            if content:
                parts = [p.strip() for p in content.replace(";", ",").split(",") if p.strip()]
                items.extend(parts)
            # Collect subsequent lines until blank or another heading-like line
            for next_line in lines[idx + 1 :]:
                stripped = next_line.strip()
                if not stripped:
                    break
                if ":" in stripped and stripped.split(":", 1)[0].strip().isalpha():
                    # Likely a new section
                    break
                if stripped.startswith("-"):
                    stripped = stripped.lstrip("-").strip()
                parts = [p.strip() for p in stripped.replace(";", ",").split(",") if p.strip()]
                items.extend(parts)
            break
    return items


def parse_resume(file_path: str) -> CandidateProfile:
    """
    Resume parser with PDF/Text/Markdown support.
    - PDF uses PyPDF2 if available.
    - Text/Markdown uses labeled-section heuristics.
    """
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        text = _read_pdf_text(file_path)
    else:
        text = _read_text(file_path)

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    name = lines[0] if lines else "TBD"
    contact = lines[1] if len(lines) > 1 else "email@example.com"
    summary = ""

    skills = _extract_section(lines, "skills")
    experience = _extract_section(lines, "experience")
    education = _extract_section(lines, "education")

    return CandidateProfile(
        name=name,
        contact=contact,
        summary=summary,
        skills=skills,
        experience=experience,
        education=education,
    )
