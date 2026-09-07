from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.entities import FileKind, KnowledgeDocument, StoredFile, User
from app.schemas.dto import KnowledgeMetadata
from app.services.ai_provider import get_ai_provider
from app.services.extraction import chunk_text, clean_text, extract_text
from app.services.rag import RagService
from app.services.storage import StorageService


router = APIRouter(prefix="/admin", tags=["admin"])


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
