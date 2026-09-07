from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    student = "student"
    admin = "admin"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class FileKind(str, Enum):
    material = "material"
    screenshot = "screenshot"
    knowledge_base = "knowledge_base"
    generated = "generated"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.student)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    projects: Mapped[list["Project"]] = relationship(back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    student_details: Mapped[str] = mapped_column(Text, default="")
    college: Mapped[str] = mapped_column(String(255), default="")
    branch: Mapped[str] = mapped_column(String(120), default="")
    guide: Mapped[str] = mapped_column(String(255), default="")
    academic_year: Mapped[str] = mapped_column(String(40), default="")
    abstract: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    technologies: Mapped[str] = mapped_column(Text, default="")
    custom_chapters: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    generated_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped[User] = relationship(back_populates="projects")
    files: Mapped[list["StoredFile"]] = relationship(back_populates="project")
    jobs: Mapped[list["ReportJob"]] = relationship(back_populates="project")


class StoredFile(Base):
    __tablename__ = "stored_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    kind: Mapped[FileKind] = mapped_column(SAEnum(FileKind), default=FileKind.material)
    original_name: Mapped[str] = mapped_column(String(500))
    storage_key: Mapped[str] = mapped_column(String(800))
    content_type: Mapped[str] = mapped_column(String(200), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer)
    file_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project | None] = relationship(back_populates="files")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"), index=True)
    college: Mapped[str] = mapped_column(String(255), default="")
    branch: Mapped[str] = mapped_column(String(120), default="")
    project_type: Mapped[str] = mapped_column(String(120), default="")
    technology: Mapped[str] = mapped_column(String(255), default="")
    year: Mapped[str] = mapped_column(String(40), default="")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReportJob(Base):
    __tablename__ = "report_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.queued)
    message: Mapped[str] = mapped_column(Text, default="")
    result_file_id: Mapped[int | None] = mapped_column(ForeignKey("stored_files.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped[Project] = relationship(back_populates="jobs")
