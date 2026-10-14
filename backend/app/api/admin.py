from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.entities import FileKind, KnowledgeDocument, Project, StoredFile, User, UserRole
from app.schemas.dto import KnowledgeMetadata
from app.services.ai_provider import get_ai_provider
from app.services.extraction import chunk_text, clean_text, extract_text
from app.services.rag import RagService
from app.services.storage import StorageService


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def get_admin_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    total_projects = db.scalar(select(func.count(Project.id))) or 0
    total_reports = db.scalar(select(func.count(StoredFile.id)).where(StoredFile.kind == FileKind.generated)) or 0
    total_kb_docs = db.scalar(select(func.count(KnowledgeDocument.id))) or 0
    total_kb_chunks = db.scalar(select(func.sum(KnowledgeDocument.chunk_count))) or 0
    total_students = db.scalar(select(func.count(User.id)).where(User.role == UserRole.student)) or 0
    return {
        "total_projects": total_projects,
        "total_reports": total_reports,
        "total_kb_docs": total_kb_docs,
        "total_kb_chunks": total_kb_chunks or 0,
        "total_students": total_students,
    }


@router.get("/knowledge-base")
def list_knowledge_base(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    docs = db.execute(
        select(KnowledgeDocument, StoredFile.original_name, StoredFile.size_bytes)
        .join(StoredFile, KnowledgeDocument.file_id == StoredFile.id)
        .order_by(KnowledgeDocument.created_at.desc())
    ).all()
    return [
        {
            "id": row.KnowledgeDocument.id,
            "file_id": row.KnowledgeDocument.file_id,
            "filename": row.original_name,
            "college": row.KnowledgeDocument.college,
            "branch": row.KnowledgeDocument.branch,
            "project_type": row.KnowledgeDocument.project_type,
            "technology": row.KnowledgeDocument.technology,
            "year": row.KnowledgeDocument.year,
            "chunk_count": row.KnowledgeDocument.chunk_count,
            "size_bytes": row.size_bytes,
            "created_at": row.KnowledgeDocument.created_at.isoformat() if row.KnowledgeDocument.created_at else None,
        }
        for row in docs
    ]


@router.post("/knowledge-base")
async def upload_knowledge_base(
    college: str = Form(""),
    branch: str = Form(""),
    project_type: str = Form(""),
    technology: str = Form(""),
    year: str = Form(""),
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    storage = StorageService()
    key, size = await storage.save_upload(file, "uploads/knowledge-base")
    text = clean_text(extract_text(storage.path_for(key)))
    stored = StoredFile(
        owner_id=admin.id,
        kind=FileKind.knowledge_base,
        original_name=file.filename or "knowledge-base",
        storage_key=key,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size,
        file_bytes=storage.path_for(key).read_bytes(),
        extracted_text=text,
    )
    db.add(stored)
    db.flush()
    metadata = KnowledgeMetadata(college=college, branch=branch, project_type=project_type, technology=technology, year=year)
    chunks = chunk_text(text)
    count = RagService(get_ai_provider()).add_document(chunks, metadata.model_dump())
    kb = KnowledgeDocument(file_id=stored.id, chunk_count=count, **metadata.model_dump())
    db.add(kb)
    db.commit()
    return {"file_id": stored.id, "chunks": count, "metadata": metadata}


@router.delete("/knowledge-base/{doc_id}")
def delete_knowledge_document(
    doc_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    doc = db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    file_id = doc.file_id
    db.delete(doc)
    stored = db.get(StoredFile, file_id)
    if stored:
        db.delete(stored)
    db.commit()
    return {"status": "deleted", "id": doc_id}


@router.get("/projects")
def list_all_student_projects(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    projects = db.scalars(select(Project).order_by(Project.updated_at.desc())).all()
    results = []
    for p in projects:
        generated_file = next((f for f in p.files if f.kind == FileKind.generated), None)
        latest_job = p.jobs[-1] if p.jobs else None
        results.append({
            "id": p.id,
            "title": p.title,
            "student_name": p.student_details or (p.owner.full_name if p.owner else "Student"),
            "owner_email": p.owner.email if p.owner else "",
            "college": p.college,
            "branch": p.branch,
            "academic_year": p.academic_year,
            "guide": p.guide,
            "technologies": p.technologies,
            "has_report": bool(p.generated_report or generated_file),
            "generated_file_id": generated_file.id if generated_file else (latest_job.result_file_id if latest_job else None),
            "job_status": latest_job.status.value if latest_job else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })
    return results
