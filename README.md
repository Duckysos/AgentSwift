# AgentSwift
An agentic AI system that autonomously analyses job descriptions and rewrites CVs to maximise role fit. Built for Google and Kaggle's Intensive Agentic AI course.


# Project Overview – Agent Swift

Agent Swift is a multi agent system designed to tailor resumes and cover letters for specific job postings. Built using Google’s Agent Development Kit (ADK), it follows a modular workflow where specialized agents collaborate to analyse job descriptions, extract relevant information from user documents, and generate polished application materials. The system helps job seekers submit targeted and high quality applications with far less manual effort.

## Problem Statement

Personalizing resumes and cover letters for each job is time consuming. Applicants must repeatedly examine job descriptions, pick out key requirements, and rewrite sections of their documents to align with employer expectations. This repetition can slow down job searching, introduce inconsistencies, and lead to generic submissions that fail to highlight relevant skills. The challenge becomes even greater when applying to many roles at once. Automation can reduce this workload by handling requirement extraction, rewriting, formatting, and the generation of tailored drafts, allowing applicants to focus on strategy instead of rewriting the same content repeatedly.

## Solution Statement

Agentic systems can evaluate job descriptions, extract essential qualifications, and match them with a candidate’s experience. They can rewrite bullet points to reflect required competencies, craft targeted cover letters, and reorganize content to fit each role. They can also highlight missing skills, recommend improvements, and produce multiple versions of documents for different job types. With automation handling these labour intensive tasks, applicants can submit more consistent and competitive applications across a wider range of opportunities.

## Architecture

The system revolves around the `swift_orchestrator_agent`, which coordinates all sub agents. It uses the ADK’s Agent class to define instructions, reasoning parameters, and the tools it can call. The orchestrator controls a series of specialized agents, each performing a specific stage of the tailoring workflow.

##Resume Parser Agent

The `resume_parser_agent` processes the applicant’s resume and extracts structured information such as work experience, skills, education, and key achievements. It normalizes formatting differences and produces a consistent representation of the user’s background for downstream agents.

## Job Description Analyzer Agent

The `jd_analyzer_agent` analyses job postings to extract required skills, responsibilities, seniority expectations, and relevant themes. It transforms noisy or unstructured job descriptions into a clear set of requirements that guide the tailoring process.

## Matcher Agent

The `resume_jd_matcher_agent` compares insights from the resume parser to the job description analysis. It identifies gaps, selects relevant accomplishments, and recommends which experiences should be emphasised or reframed. This ensures the rewritten content stays grounded in the user’s actual expertise.

## Tailored Writer Agent

The `swift_writer_agent` generates updated resume sections and a job specific cover letter. It uses the matcher output to guide writing decisions and applies professional tone and structure. Quality checks ensure that the generated material is clear and aligns with the job posting.

##Editor Agent

The `swift_editor_agent` refines the tailored content based on user feedback. It adjusts tone, improves clarity, corrects formatting inconsistencies, and ensures the final output is ready for export.

## Essential Tools and Utilities
### Resume Parsing Utility

A file parsing tool formats the user’s uploaded resume into clean, structured text. It handles common formatting quirks and ensures extracted sections are usable by the parser agent.

### Validation Checkers

Custom validation agents ensure that each generated section meets quality criteria. When a draft fails validation, the system uses the LoopAgent pattern to regenerate the content until the final output meets expected standards.

### File Export Tool

A file saving tool allows Agent Swift to export finished resumes and cover letters as Markdown or PDF files, making the output ready for application submission.

## Conclusion

Agent Swift demonstrates how modular agentic systems can streamline the job application process. By distributing tasks among dedicated agents that handle parsing, analysis, matching, writing, and editing, it creates a structured and repeatable workflow. The orchestrator ensures that each step progresses only when validation checks pass, making the process reliable and scalable. The final result is a set of application materials that are polished, targeted, and aligned with the expectations of each employer.

## Value Statement

Agent Swift cuts the time needed to tailor resumes and cover letters from hours to minutes. It enables applicants to maintain a consistently high standard across all applications and helps them apply to more roles without sacrificing quality. With further development, an additional agent could scan job boards, identify suitable roles, and automatically prepare tailored drafts for review. Integrating this functionality would involve connecting external data sources through MCP servers or custom ingestion tools.

# Resume Tailor (Google ADK + Gemini)

## Prerequisites
- Python 3.10+
- A Google API key in `.env` (for LLM mode):
  ```
  GOOGLE_API_KEY=your_key_here
  ```
- If you want offline-only use, you can skip the API key.

## Install
```
pip install -r requirements.txt
```

## Running (FastAPI)
Start the API (loads `.env` if `python-dotenv` is installed):
```
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```
Open http://localhost:8000/docs and call `/tailor`:
- `resume_file`: upload pdf/txt/md
- `jd_file`: upload the JD text
- `offline`: optional `true` to skip LLM calls

Curl example (PowerShell):
```
curl -X POST "http://localhost:8000/tailor" ^
  -F "resume_file=@sample_resume.txt" ^
  -F "jd_file=@job_posting.txt" ^
  -F "offline=true"
```

## Running (CLI)
```
python cli.py --resume sample_resume.txt --jd job_posting.txt --format md
```
Options:
- `--format`: md|txt|pdf|docx (pdf/docx need fpdf/python-docx installed)
- `--offline`: force heuristic (no LLM)

## Offline vs LLM
- LLM mode (default): ensure `GOOGLE_API_KEY` is loaded; agents call Gemini.
- Offline: add `offline=true` (API) or `--offline` (CLI) to use heuristic fallbacks.

## Outputs
- API/Web return JSON with `tailored_resume`, `tailored_cover`, and `markdown`.
- CLI writes the chosen format to disk; Markdown includes normalized bullets/headings.

