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

FRONT_MATTER_PATTERNS = [
    r"^page\s*no",
    r"^certificate",
    r"^bonafide",
    r"^acknowledg",
    r"^abstract",
    r"^table\s*of\s*content",
    r"^index$",
    r"^list\s*of\s*figure",
    r"^list\s*of\s*table",
    r"^list\s*of\s*abbreviation",
    r"^declaration",
]


def sanitize_and_structure_chapters(raw_chapters: list[str] | None) -> tuple[list[str], str]:
    """Sanitizes user and template chapter outlines by filtering out front-matter pages
    (Certificate, Abstract, etc.) while preserving all academic chapters in sequence."""
    if not raw_chapters:
        return (DEFAULT_CHAPTERS, "")

    filtered: list[str] = []
    for line in raw_chapters:
        t = line.strip()
        if not t or any(re.search(pat, t.lower()) for pat in FRONT_MATTER_PATTERNS):
            continue
        filtered.append(t)

    if not filtered:
        return (DEFAULT_CHAPTERS, "")

    # Group into chapters and nested subsections
    major_chapters: list[dict] = []
    current_chapter: dict | None = None

    for line in filtered:
        # Check if this line is an explicit sub-topic (e.g., "1.1 Background", "- item")
        is_sub = bool(
            re.match(r"^\d+\.\d+", line)
            or line.startswith(("- ", "* ", "• ", "> "))
        )
        cleaned_title = re.sub(r"^(?:chapter\s+\d+[:\s-]*|\d+[\.\)]\s*)", "", line, flags=re.I).strip() or line.strip()

        if is_sub and current_chapter:
            current_chapter["subsections"].append(line.lstrip("-*•> ").strip())
        else:
            current_chapter = {"title": cleaned_title, "subsections": []}
            major_chapters.append(current_chapter)

    names = [c["title"] for c in major_chapters if c["title"]]
    if not names:
        return (DEFAULT_CHAPTERS, "")

    guidance = ""
    has_subsections = any(c["subsections"] for c in major_chapters)
    if has_subsections:
        lines = ["Curriculum Chapter Structure & Required Subsections:"]
        for idx, c in enumerate(major_chapters, start=1):
            lines.append(f"Chapter {idx}: {c['title']}")
            for sub in c["subsections"]:
                lines.append(f"  - {sub}")
        guidance = "\n".join(lines)

    return (names, guidance)


def get_project_fallback_diagrams(project) -> list[dict]:
    tech = getattr(project, "technologies", "") or "Web Services, Database & APIs"
    title_short = getattr(project, "title", "Project Application")[:40]
    return [
        {
            "title": "High-Level System Architecture",
            "type": "mermaid",
            "definition": (
                f"graph TD\n"
                f"  Client[User Client / Presentation Layer] --> Gateway[API Gateway / Service Controller]\n"
                f"  Gateway --> Engine[Core Business Logic & Processing Engine]\n"
                f"  Engine --> Storage[(Database & Persistence Tier)]\n"
                f"  Engine --> ExtServices[Component Stack: {tech[:35]}]\n"
                f"  Storage --> Gateway\n"
                f"  Gateway --> Client"
            ),
        },
        {
            "title": "System Use Case Diagram",
            "type": "mermaid",
            "definition": (
                f"graph LR\n"
                f"  User((Primary Operator)) --> Auth[Login & Authentication]\n"
                f"  User --> InputData[Configure Parameters / Input Data]\n"
                f"  User --> Process[Execute Core Operations]\n"
                f"  User --> Results[View Reports & Visualizations]\n"
                f"  Admin((System Administrator)) --> Manage[System Audit & Maintenance]"
            ),
        },
        {
            "title": "Data Flow Diagram (Level 1)",
            "type": "mermaid",
            "definition": (
                f"graph TD\n"
                f"  DataInput[Raw Inputs / Source Data] --> P1[Process 1: Ingestion & Validation]\n"
                f"  P1 --> P2[Process 2: Core Algorithm / Computation Logic]\n"
                f"  P2 --> DBStore[(Project Database Storage)]\n"
                f"  P2 --> P3[Process 3: Output Formatting & Report Compilation]\n"
                f"  P3 --> FinalReport[Final Thesis Delivery / Dashboard]"
            ),
        },
        {
            "title": "Entity Relationship / Component Model",
            "type": "mermaid",
            "definition": (
                f"graph TD\n"
                f"  UserAccount[USER: id, credentials, role] --> SessionLog[SESSION: session_id, timestamp]\n"
                f"  UserAccount --> RecordEntity[RECORD: id, title, parameters]\n"
                f"  RecordEntity --> ExecutionResult[RESULT: status, output_data, metrics]\n"
                f"  ExecutionResult --> AuditReport[AUDIT: log_id, timestamp, verification]"
            ),
        },
    ]


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
            if any(re.search(pat, ch_t.lower()) for pat in FRONT_MATTER_PATTERNS):
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

        # Fallback to project-tailored schematics if empty
        if not diagrams:
            diagrams = DiagramRenderer().render_many(get_project_fallback_diagrams(project))

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
