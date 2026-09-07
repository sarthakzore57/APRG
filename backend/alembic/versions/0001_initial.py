"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-31
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"
    user_role = _enum_type("userrole", "student", "admin", native=is_postgresql)
    job_status = _enum_type("jobstatus", "queued", "running", "completed", "failed", native=is_postgresql)
    file_kind = _enum_type("filekind", "material", "screenshot", "knowledge_base", "generated", native=is_postgresql)
    if is_postgresql:
        user_role.create(bind, checkfirst=True)
        job_status.create(bind, checkfirst=True)
        file_kind.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("student_details", sa.Text(), nullable=False),
        sa.Column("college", sa.String(length=255), nullable=False),
        sa.Column("branch", sa.String(length=120), nullable=False),
        sa.Column("guide", sa.String(length=255), nullable=False),
        sa.Column("academic_year", sa.String(length=40), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("technologies", sa.Text(), nullable=False),
        sa.Column("custom_chapters", sa.JSON(), nullable=True),
        sa.Column("profile", sa.JSON(), nullable=True),
        sa.Column("validation", sa.JSON(), nullable=True),
        sa.Column("generated_report", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])

    op.create_table(
        "stored_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("kind", file_kind, nullable=False),
        sa.Column("original_name", sa.String(length=500), nullable=False),
        sa.Column("storage_key", sa.String(length=800), nullable=False),
        sa.Column("content_type", sa.String(length=200), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("file_bytes", sa.LargeBinary(), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("file_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_stored_files_owner_id", "stored_files", ["owner_id"])
    op.create_index("ix_stored_files_project_id", "stored_files", ["project_id"])

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("stored_files.id"), nullable=False),
        sa.Column("college", sa.String(length=255), nullable=False),
        sa.Column("branch", sa.String(length=120), nullable=False),
        sa.Column("project_type", sa.String(length=120), nullable=False),
        sa.Column("technology", sa.String(length=255), nullable=False),
        sa.Column("year", sa.String(length=40), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_knowledge_documents_file_id", "knowledge_documents", ["file_id"])

    op.create_table(
        "report_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("result_file_id", sa.Integer(), sa.ForeignKey("stored_files.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_report_jobs_project_id", "report_jobs", ["project_id"])


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_report_jobs_project_id", table_name="report_jobs")
    op.drop_table("report_jobs")
    op.drop_index("ix_knowledge_documents_file_id", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
    op.drop_index("ix_stored_files_project_id", table_name="stored_files")
    op.drop_index("ix_stored_files_owner_id", table_name="stored_files")
    op.drop_table("stored_files")
    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_table("projects")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    if bind.dialect.name == "postgresql":
        sa.Enum(name="filekind").drop(bind, checkfirst=True)
        sa.Enum(name="jobstatus").drop(bind, checkfirst=True)
        sa.Enum(name="userrole").drop(bind, checkfirst=True)


def _enum_type(name: str, *values: str, native: bool) -> sa.Enum:
    if native:
        return postgresql.ENUM(*values, name=name, create_type=False)
    return sa.Enum(*values, name=name, native_enum=False)
