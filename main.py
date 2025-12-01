import os

from agents.orchestrator import SwiftOrchestratorAgent

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def main():
    # Load environment variables from .env if python-dotenv is available.
    if load_dotenv:
        load_dotenv()
    elif os.environ.get("GOOGLE_API_KEY") is None:
        # Minimal hint if credentials are missing and python-dotenv is not installed.
        print("Warning: GOOGLE_API_KEY not set and python-dotenv missing; LLM calls will be skipped.")

    orchestrator = SwiftOrchestratorAgent()
    # Prefer PDF if present; otherwise fall back to the sample text resume.
    resume_path = "sample_resume.pdf" if os.path.exists("sample_resume.pdf") else "sample_resume.txt"
    draft = orchestrator.run(resume_path, open("job_posting.txt", "r", encoding="utf-8").read())
    print("Tailored resume:\n", draft.tailored_resume)
    if draft.tailored_cover:
        print("\nCover letter:\n", draft.tailored_cover)


if __name__ == "__main__":
    main()
