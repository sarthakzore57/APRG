from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.entities import User, UserRole


def create_admin(db: Session, email: str, full_name: str, password: str) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        existing.role = UserRole.admin
        db.commit()
        db.refresh(existing)
        return existing
    user = User(email=email, full_name=full_name, password_hash=hash_password(password), role=UserRole.admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
