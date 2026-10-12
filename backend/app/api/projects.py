from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, owned_project
from app.core.database import SessionLocal, get_db
from app.models.entities import FileKind, JobStatus, Project, ReportJob, StoredFile, User
from app.schemas.dto import ChapterEdit, JobRead, ProjectCreate, ProjectRead, ProjectUpdate, RegenerateRequest
from app.services.ai_provider import get_ai_provider
from app.services.extraction import clean_text, extract_text
from app.services.prompting import TEMPLATE_PRESETS, project_context
from app.services.report_generator import run_report_job
from app.services.storage import StorageService


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/templates")
def list_templates() -> list[dict]:
    return TEMPLATE_PRESETS


@router.get("", response_model=list[ProjectRead])
def list_projects(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Project]:
    return list(db.scalars(select(Project).where(Project.owner_id == user.id).order_by(Project.updated_at.desc())))


@router.post("", response_model=ProjectRead)
def create_project(payload: ProjectCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Project:
    project = Project(owner_id=user.id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project: Project = Depends(owned_project)) -> Project:
    return project


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(payload: ProjectUpdate, project: Project = Depends(owned_project), db: Session = Depends(get_db)) -> Project:
    for key, value in payload.model_dump().items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/files")
async def upload_file(
    project: Project = Depends(owned_project),
    kind: FileKind = Form(FileKind.material),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    if kind == FileKind.knowledge_base:
        raise HTTPException(status_code=400, detail="Use admin knowledge-base endpoint")
    storage = StorageService()
    key, size = await storage.save_upload(file, f"uploads/projects/{project.id}")
    text = clean_text(extract_text(storage.path_for(key)))
    stored = StoredFile(
        owner_id=project.owner_id,
        project_id=project.id,
        kind=kind,
        original_name=file.filename or "upload",
        storage_key=key,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size,
        file_bytes=storage.path_for(key).read_bytes(),
        extracted_text=text,
    )
    db.add(stored)
    db.commit()
    return {"id": stored.id, "name": stored.original_name, "kind": stored.kind, "size_bytes": stored.size_bytes}


def run_job_with_fresh_session(job_id: int) -> None:
    db = SessionLocal()
    try:
        run_report_job(db, job_id)
    finally:
        db.close()


@router.post("/{project_id}/generate", response_model=JobRead)
def generate_report(background: BackgroundTasks, project: Project = Depends(owned_project), db: Session = Depends(get_db)) -> ReportJob:
    job = ReportJob(project_id=project.id, status=JobStatus.queued, message="Queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    background.add_task(run_job_with_fresh_session, job.id)
    return job


@router.get("/{project_id}/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, project: Project = Depends(owned_project), db: Session = Depends(get_db)) -> ReportJob:
    job = db.get(ReportJob, job_id)
    if not job or job.project_id != project.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{project_id}/chapters", response_model=ProjectRead)
def edit_chapter(payload: ChapterEdit, project: Project = Depends(owned_project), db: Session = Depends(get_db)) -> Project:
    report = project.generated_report or {"chapters": []}
    for chapter in report.get("chapters", []):
        if chapter.get("title") == payload.chapter:
            chapter["content"] = payload.content
            break
    else:
        report.setdefault("chapters", []).append({"title": payload.chapter, "content": payload.content, "tables": []})
    project.generated_report = report
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/chapters/regenerate", response_model=ProjectRead)
def regenerate_chapter(payload: RegenerateRequest, project: Project = Depends(owned_project), db: Session = Depends(get_db)) -> Project:
    ai = get_ai_provider()
    files = [f for f in project.files if f.kind in {FileKind.material, FileKind.screenshot}]
    extracted = "\n\n".join((f.extracted_text or "")[:12000] for f in files)
    context = project_context(project, project.profile or {}, extracted, [])
    report = project.generated_report or {"chapters": []}
    prompt = f"{context}\nRewrite only the chapter '{payload.chapter}' in mode '{payload.mode}'. Return plain chapter text only."
    content = ai.generate_text(prompt)
    for chapter in report.get("chapters", []):
        if chapter.get("title") == payload.chapter:
            chapter["content"] = content
            break
    project.generated_report = report
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/download/{file_id}")
def download(file_id: int, project: Project = Depends(owned_project), db: Session = Depends(get_db)):
    stored = db.get(StoredFile, file_id)
    if not stored or stored.project_id != project.id:
        raise HTTPException(status_code=404, detail="File not found")
    storage = StorageService()
    path = storage.restore_if_missing(stored.storage_key, stored.file_bytes)
    if path.exists():
        return FileResponse(path, filename=stored.original_name, media_type=stored.content_type)
    if stored.file_bytes:
        return Response(
            stored.file_bytes,
            media_type=stored.content_type,
            headers={"Content-Disposition": f'attachment; filename="{stored.original_name}"'},
        )
    raise HTTPException(status_code=410, detail="File is no longer available")
