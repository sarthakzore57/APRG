import logging
import re
from sqlalchemy.orm import Session

from app.models.entities import FileKind, JobStatus, ReportJob, StoredFile
from app.services.ai_provider import get_ai_provider
from app.services.diagram import DiagramRenderer, ExhibitGenerator, GeneratedExhibit
from app.services.docx_writer import DocxReportWriter
from app.services.project_analyzer import analyze_project
from app.services.prompting import DEFAULT_CHAPTERS, diagram_prompt, project_context, report_prompt, validation_prompt
from app.services.rag import RagService

logger = logging.getLogger(__name__)

IGNORE_PATTERNS = [
    r"page\s*no",
    r"certificate",
    r"acknowledg",
    r"abstract",
    r"table\s*of\s*content",
    r"index",
    r"list\s*of\s*figure",
    r"list\s*of\s*table",
    r"list\s*of\s*abbreviation",
    r"sr\.?\s*no",
    r"serial\s*no",
    r"title\s*of\s*chapter",
    r"declaration",
    r"^references?$",
    r"^bibliography$",
    r"^appendix",
]


def sanitize_and_structure_chapters(raw_chapters: list[str] | None) -> tuple[list[str], str]:
    """Sanitizes user outlines by stripping out front-matter pages (Certificate, Abstract, etc.)
    and grouping nested sub-topics into formal parent chapters."""
    if not raw_chapters:
        return (DEFAULT_CHAPTERS, "")

    filtered: list[str] = []
    for line in raw_chapters:
        t = line.strip().lower()
        if not t or any(re.search(pat, t) for pat in IGNORE_PATTERNS):
            continue
        filtered.append(line.strip())

    if not filtered:
        return (DEFAULT_CHAPTERS, "")

    # Check if this is already a concise list of chapters (<= 8 items with no sub-numberings)
    has_subnumbering = any(re.search(r"\d+\.\d+", l) for l in filtered)
    if not has_subnumbering and len(filtered) <= 8:
        clean_names = [re.sub(r"^(?:chapter\s+\d+[:\s-]*|\d+[\.\)]\s*)", "", l, flags=re.I).strip() for l in filtered]
        return ([c for c in clean_names if c], "")

    # Parse multi-tier syllabus lists
    major_chapters: list[dict] = []
    current_chapter: dict | None = None

    for line in filtered:
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
        m_major = re.match(r"^(?:0([1-9])|chapter\s+(\d+))[:\s-]*(.*)$", cleaned, re.I)
        if m_major:
            c_num = m_major.group(1) or m_major.group(2)
            c_name = m_major.group(3).strip()
            c_name = re.sub(r"^chapter\s+\d+[:\s-]*", "", c_name, flags=re.I).strip()
            title = c_name or f"Chapter {c_num}"
            current_chapter = {"title": title, "subsections": []}
            major_chapters.append(current_chapter)
        elif current_chapter:
            sub = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            if sub:
                current_chapter["subsections"].append(sub)
        else:
            if not re.search(r"^\d+\.\d+", cleaned):
                current_chapter = {"title": cleaned, "subsections": []}
                major_chapters.append(current_chapter)

    if not major_chapters:
        return (filtered[:7], "")

    names = [c["title"] for c in major_chapters]
    guidance = ["Curriculum Chapter Structure & Required Subsections:"]
    for idx, c in enumerate(major_chapters, start=1):
        ctitle = c["title"]
        guidance.append(f"Chapter {idx}: {ctitle}")
        for sub in c["subsections"]:
            guidance.append(f"  - {sub}")

    return (names, "\n".join(guidance))


def run_report_job(db: Session, job_id: int) -> None:
    job = db.get(ReportJob, job_id)
    if not job:
        return
    job.status = JobStatus.running
    job.message = "Analyzing uploads"
    db.commit()
    try:
        project = job.project
        is_img = lambda f: f.kind == FileKind.screenshot or any(
            f.original_name.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]
        )
        material_files = [f for f in project.files if f.kind in {FileKind.material, FileKind.screenshot}]
        screenshots = [f for f in project.files if is_img(f)]

        # If no screenshots were uploaded, auto-generate high-res interactive exhibits
        if not screenshots:
            gen = ExhibitGenerator()
            k1, b1 = gen.generate_dashboard(project)
            k2, b2 = gen.generate_console(project)
            screenshots = [
                GeneratedExhibit("Interactive Analytical Dashboard & User Interface.png", k1, b1),
                GeneratedExhibit("Terminal Execution Pipeline & Verification Log.png", k2, b2),
            ]

        profile = analyze_project(project, material_files)
        project.profile = profile
        extracted = "\n\n".join((f.extracted_text or "")[:12000] for f in material_files)
        ai = get_ai_provider()
        rag = RagService(ai)
        query = f"{project.title}\n{project.abstract}\n{project.description}\n{project.technologies}\n{profile}"
        chunks = rag.retrieve(
            query,
            metadata_hint={
                "college": project.college,
                "branch": project.branch,
                "technology": project.technologies,
            },
        )
        context = project_context(project, profile, extracted, chunks)
        chapters, chapter_guidance = sanitize_and_structure_chapters(project.custom_chapters)

        job.message = f"Writing report with Gemini ({len(material_files)} project file(s), {len(chunks)} reference chunk(s))"
        db.commit()
        report = ai.generate_json(report_prompt(context, chapters, chapter_guidance))

        # Filter any accidental duplicate preliminary chapters returned by LLM
        clean_report_chapters = []
        for ch in report.get("chapters", []):
            ch_t = ch.get("title", "").strip()
            if any(re.search(pat, ch_t.lower()) for pat in IGNORE_PATTERNS):
                continue
            ch["title"] = re.sub(r"^(?:chapter\s+\d+[:\s-]*|\d+[\.\)]\s*)", "", ch_t, flags=re.I).strip() or ch_t
            clean_report_chapters.append(ch)
        report["chapters"] = clean_report_chapters

        job.message = "Validating report against curriculum guidelines"
        db.commit()
        validation = ai.generate_json(validation_prompt(context, report))

        job.message = "Rendering architecture schematics"
        db.commit()
        diagrams = []
        try:
            diagram_defs = ai.generate_json(diagram_prompt(context))
            if isinstance(diagram_defs, dict) and diagram_defs.get("diagrams"):
                diagrams = DiagramRenderer().render_many(diagram_defs["diagrams"])
        except Exception as diagram_err:
            logger.warning("AI diagram generation skipped: %s", diagram_err)

        # Fallback to standard university schematics if empty
        if not diagrams:
            default_defs = [
                {
                    "title": "High-Level System Architecture",
                    "type": "mermaid",
                    "definition": "graph TD\n  Client[User Web Client / Browser] --> API[FastAPI / REST Backend Engine]\n  API --> DB[(Database / Storage Tier)]\n  API --> AI[AI Intelligence & Generation Service]\n  DB --> API\n  AI --> API",
                },
                {
                    "title": "System Use Case Diagram",
                    "type": "mermaid",
                    "definition": "graph LR\n  Student((Student / User)) --> Auth[Authentication & Account Setup]\n  Student --> Spec[Specification & Chapter Outline]\n  Student --> Up[Code & Materials Upload]\n  Student --> Gen[Automated Report Generation]\n  Admin((Faculty / Guide)) --> Eval[Report Evaluation & Audit]",
                },
                {
                    "title": "Data Flow Diagram (Level 1)",
                    "type": "mermaid",
                    "definition": "graph TD\n  Inputs[Project Materials & Source Code] --> Extractor[Parser & AST Extractor]\n  Extractor --> Context[Context Aggregator]\n  Context --> GenEngine[Deep Academic Generation Engine]\n  GenEngine --> DocBuilder[DOCX Document Compiler]\n  DocBuilder --> FinalDoc[University Thesis Document]",
                },
                {
                    "title": "Entity Relationship Model",
                    "type": "mermaid",
                    "definition": "graph TD\n  User[USER: id, email, role] --> Project[PROJECT: id, title, branch]\n  Project --> Files[STORED_FILES: id, path, kind]\n  Project --> Jobs[REPORT_JOBS: id, status, result]\n  Jobs --> FinalFile[OUTPUT_REPORT: file_id, docx]",
                },
            ]
            diagrams = DiagramRenderer().render_many(default_defs)

        project.generated_report = {**report, "diagrams": diagrams}
        project.validation = validation

        job.message = "Compiling Word DOCX document"
        db.commit()
        writer = DocxReportWriter()
        key, size = writer.build(project, report, diagrams, screenshots, validation)
        generated = StoredFile(
            owner_id=project.owner_id,
            project_id=project.id,
            kind=FileKind.generated,
            original_name=f"{project.title}.docx",
            storage_key=key,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=size,
            file_bytes=writer.storage.path_for(key).read_bytes(),
        )
        db.add(generated)
        db.flush()
        job.result_file_id = generated.id
        job.status = JobStatus.completed
        job.message = "Report generated"
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Report generation job %d failed: %s", job_id, exc)
        job = db.get(ReportJob, job_id)
        if job:
            job.status = JobStatus.failed
            job.message = str(exc)
            db.commit()
