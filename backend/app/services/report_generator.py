import logging
import re
from sqlalchemy.orm import Session

from app.models.entities import FileKind, JobStatus, ReportJob, StoredFile
from app.services.ai_provider import get_ai_provider
from app.services.diagram import DiagramRenderer, ExhibitGenerator, GeneratedExhibit, get_domain_fallback_diagrams
from app.services.docx_writer import DocxReportWriter
from app.services.extraction import extract_text
from app.services.project_analyzer import analyze_project
from app.services.prompting import (
    DEFAULT_CHAPTERS,
    diagram_prompt,
    project_context,
    report_prompt,
    validation_prompt,
)
from app.services.rag import RagService
from app.services.storage import StorageService

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


def run_report_job(db: Session, job_id: int) -> None:
    job = db.get(ReportJob, job_id)
    if not job:
        return
    job.status = JobStatus.running
    job.message = "Analyzing uploads and attached files"
    db.commit()
    try:
        project = job.project
        storage = StorageService()

        is_img = lambda f: f.kind == FileKind.screenshot or any(
            f.original_name.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]
        )
        material_files = [f for f in project.files if f.kind in {FileKind.material, FileKind.screenshot}]
        screenshots = [f for f in project.files if is_img(f)]

        # Ensure extracted text is populated for all files (including images via Gemini vision)
        file_extracts: list[str] = []
        for f in material_files:
            text = f.extracted_text or ""
            if (not text or "Student-provided" in text) and f.storage_key:
                try:
                    p = storage.restore_if_missing(f.storage_key, f.file_bytes)
                    text = extract_text(p)
                    f.extracted_text = text
                except Exception as ex:
                    logger.debug("Extraction refresh error for %s: %s", f.original_name, ex)
            file_extracts.append(f"ATTACHMENT: {f.original_name} (Category: {f.kind.value}):\n{text[:15000]}")

        extracted = "\n\n".join(file_extracts)

        profile = analyze_project(project, material_files)
        project.profile = profile
        domain_key = profile.get("domain_key", "tech")
        domain_name = profile.get("domain_name", "Academic Research")

        # If no screenshots were uploaded, dynamically generate high-res domain-tailored exhibits
        if not screenshots:
            gen = ExhibitGenerator()
            screenshots = gen.generate_exhibits_for_project(project, domain_key=domain_key)

        ai = get_ai_provider()
        rag = RagService(ai)
        query = f"{project.title}\n{project.branch}\n{domain_name}\n{project.technologies}\n{project.abstract}"
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

        job.message = f"Writing {domain_name} report with Gemini ({len(material_files)} file(s), {len(chunks)} reference(s))"
        db.commit()
        report = ai.generate_json(report_prompt(context, chapters, chapter_guidance, domain_info=profile))

        # Filter any accidental duplicate preliminary chapters returned by LLM
        clean_report_chapters = []
        for ch in report.get("chapters", []):
            ch_t = ch.get("title", "").strip()
            if any(re.search(pat, ch_t.lower()) for pat in FRONT_MATTER_PATTERNS):
                continue
            ch["title"] = re.sub(r"^(?:chapter\s+\d+[:\s-]*|\d+[\.\)]\s*)", "", ch_t, flags=re.I).strip() or ch_t
            clean_report_chapters.append(ch)
        report["chapters"] = clean_report_chapters

        job.message = "Validating report against academic standards"
        db.commit()
        validation = ai.generate_json(validation_prompt(context, report))

        job.message = f"Rendering {domain_name} schematics and diagrams"
        db.commit()
        diagrams = []
        try:
            diagram_defs = ai.generate_json(diagram_prompt(context, domain_info=profile))
            if isinstance(diagram_defs, dict) and diagram_defs.get("diagrams"):
                diagrams = DiagramRenderer().render_many(diagram_defs["diagrams"])
        except Exception as diagram_err:
            logger.warning("AI diagram generation skipped: %s", diagram_err)

        # Fallback to domain-tailored schematics if empty
        if not diagrams:
            diagrams = DiagramRenderer().render_many(get_domain_fallback_diagrams(project, domain_key=domain_key))

        # Associate diagrams directly to relevant chapters for clear UI manuscript preview
        diag_idx = 0
        for ch in report.get("chapters", []):
            t_low = ch.get("title", "").lower()
            is_design = any(w in t_low for w in ["architecture", "design", "methodology", "structural", "model", "workflow", "schematic", "system"])
            if is_design and diag_idx < len(diagrams):
                ch["diagram"] = diagrams[diag_idx]
                diag_idx += 1

        project.generated_report = {**report, "diagrams": diagrams}
        project.validation = validation

        job.message = "Compiling Word DOCX document"
        db.commit()
        writer = DocxReportWriter()
        key, size = writer.build(project, report, diagrams, screenshots, validation, domain_info=profile)
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
        job.message = "Report generated successfully"
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Report generation job %d failed: %s", job_id, exc)
        job = db.get(ReportJob, job_id)
        if job:
            job.status = JobStatus.failed
            job.message = str(exc)
            db.commit()
