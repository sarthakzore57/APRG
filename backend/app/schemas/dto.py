from pydantic import BaseModel, EmailStr, Field
from app.models.entities import JobStatus, UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole

    class Config:
        from_attributes = True


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ProjectCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    student_details: str = ""
    college: str = ""
    branch: str = ""
    guide: str = ""
    academic_year: str = ""
    abstract: str = ""
    description: str = ""
    technologies: str = ""
    custom_chapters: list[str] | None = None


class ProjectUpdate(ProjectCreate):
    pass


class ProjectRead(ProjectCreate):
    id: int
    profile: dict | None = None
    validation: dict | None = None
    generated_report: dict | None = None

    class Config:
        from_attributes = True


class JobRead(BaseModel):
    id: int
    project_id: int
    status: JobStatus
    message: str
    result_file_id: int | None = None

    class Config:
        from_attributes = True


class KnowledgeMetadata(BaseModel):
    college: str = ""
    branch: str = ""
    project_type: str = ""
    technology: str = ""
    year: str = ""


class ChapterEdit(BaseModel):
    chapter: str
    content: str


class RegenerateRequest(BaseModel):
    chapter: str
    mode: str = Field(pattern="^(shorter|longer|simpler|more technical|regenerate)$")
