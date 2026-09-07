from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, projects
from app.core.config import get_settings


settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_origin.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.get("/")
def root() -> dict:
    return {
        "app": settings.app_name,
        "status": "running",
        "api_docs": "/docs",
        "health": "/health",
        "api_prefix": "/api",
    }
