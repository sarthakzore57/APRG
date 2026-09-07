from sqlalchemy.orm import Session

from app.models.entities import FileKind, JobStatus, ReportJob, StoredFile
from app.services.ai_provider import get_ai_provider
from app.services.diagram import DiagramRenderer
from app.services.docx_writer import DocxReportWriter
from app.services.project_analyzer import analyze_project
from app.services.prompting import DEFAULT_CHAPTERS, diagram_prompt, project_context, report_prompt, validation_prompt
from app.services.rag import RagService


def run_report_job(db: Session, job_id: int) -> None:
    job = db.get(ReportJob, job_id)
    if not job:
        return
    job.status = JobStatus.running
    job.message = "Analyzing uploads"
    db.commit()
    try:
        project = job.project
        material_files = [f for f in project.files if f.kind in {FileKind.material, FileKind.screenshot}]
        screenshots = [f for f in project.files if f.kind == FileKind.screenshot]
        profile = analyze_project(project, material_files)
        project.profile = profile
        extracted = "\n\n".join((f.extracted_text or "")[:12000] for f in material_files)
        ai = get_ai_provider()
        rag = RagService(ai)
        query = f"{project.title}\n{project.abstract}\n{project.description}\n{project.technologies}\n{profile}"
        chunks = rag.retrieve(query)
        context = project_context(project, profile, extracted, chunks)
        chapters = project.custom_chapters or DEFAULT_CHAPTERS

        job.message = "Generating report with Gemini"
        db.commit()
        report = ai.generate_json(report_prompt(context, chapters))

        job.message = "Validating report"
        db.commit()
        validation = ai.generate_json(validation_prompt(context, report))

        job.message = "Generating and rendering diagrams"
        db.commit()
        diagram_defs = ai.generate_json(diagram_prompt(context))
        diagrams = DiagramRenderer().render_many(diagram_defs.get("diagrams", []))

        project.generated_report = {**report, "diagrams": diagrams}
        project.validation = validation

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
        job = db.get(ReportJob, job_id)
        if job:
            job.status = JobStatus.failed
            job.message = str(exc)
            db.commit()
