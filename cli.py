import argparse
import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from agents.orchestrator import SwiftOrchestratorAgent
from config import ExportConfig
from tools.file_export_tool import export_draft


def main():
    parser = argparse.ArgumentParser(description="Tailor resume to a job description.")
    parser.add_argument("--resume", required=True, help="Path to resume (txt/md/pdf).")
    parser.add_argument("--jd", required=True, help="Path to job posting text.")
    parser.add_argument("--out", default=None, help="Output file path.")
    parser.add_argument("--format", default=ExportConfig().default_format, choices=["md", "txt", "pdf", "docx"], help="Export format.")
    parser.add_argument("--offline", action="store_true", help="Disable LLM calls; use heuristic fallbacks.")
    args = parser.parse_args()

    # Load .env if available
    if load_dotenv:
        load_dotenv()

    if not os.path.exists(args.resume):
        sys.exit(f"Resume not found: {args.resume}")
    if not os.path.exists(args.jd):
        sys.exit(f"Job posting not found: {args.jd}")

    with open(args.jd, "r", encoding="utf-8") as fh:
        jd_text = fh.read()

    orchestrator = SwiftOrchestratorAgent()
    # Toggle LLMs off if requested
    if args.offline:
        orchestrator.jd_analyzer.use_llm = False
        orchestrator.matcher.use_llm = False
        orchestrator.writer.use_llm = False
        orchestrator.editor.use_llm = False

    draft = orchestrator.run(args.resume, jd_text)
    out_path = export_draft(
        draft,
        profile=None,  # Could pass parsed profile if desired
        jd=None,
        fmt=args.format,
        out_path=args.out,
    )
    print(f"Exported to {out_path}")


if __name__ == "__main__":
    main()
