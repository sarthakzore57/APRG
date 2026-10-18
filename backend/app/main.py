from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, projects
from app.core.config import get_settings


settings = get_settings()
app = FastAPI(title=settings.app_name)

origins = [origin.strip() for origin in settings.frontend_origin.split(",") if origin.strip()]
for default_origin in [
    "https://draftly-aprg.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]:
    if default_origin not in origins:
        origins.append(default_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$|^https://.*\.onrender\.com$|^http://localhost:\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.on_event("startup")
def startup_sync_users():
    try:
        from sqlalchemy import func, select
        from app.core.database import SessionLocal
        from app.core.security import hash_password
        from app.models.entities import User, UserRole

        with SessionLocal() as db:
            clean_email = "sarthakzore237@gmail.com"
            user = db.scalar(select(User).where(func.lower(User.email) == clean_email))
            if not user:
                user = User(
                    email=clean_email,
                    full_name="Sarthak Zore",
                    password_hash=hash_password("Sarthak@123"),
                    role=UserRole.student,
                )
                db.add(user)
                db.commit()
            elif not user.password_hash:
                user.password_hash = hash_password("Sarthak@123")
                db.commit()

            clean_admin_email = "admin@example.com"
            admin = db.scalar(select(User).where(func.lower(User.email) == clean_admin_email))
            if not admin:
                admin = User(
                    email=clean_admin_email,
                    full_name="Administrator",
                    password_hash=hash_password("Admin@123"),
                    role=UserRole.admin,
                )
                db.add(admin)
                db.commit()
            else:
                admin.role = UserRole.admin
                admin.password_hash = hash_password("Admin@123")
                db.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Startup user sync skipped: %s", e)


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
