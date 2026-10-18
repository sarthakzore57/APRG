from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import User
from app.schemas.dto import PasswordReset, TokenRead, UserCreate, UserRead


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenRead)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenRead:
    clean_email = (payload.email or "").strip().lower()
    if not clean_email:
        raise HTTPException(status_code=422, detail="Email is required")
    if db.scalar(select(User).where(func.lower(User.email) == clean_email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=clean_email,
        full_name=(payload.full_name or "Student").strip(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenRead(access_token=create_access_token(user.email), user=user)


@router.post("/login", response_model=TokenRead)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenRead:
    clean_email = (form.username or "").strip().lower()
    clean_password = (form.password or "").strip()
    user = db.scalar(select(User).where(func.lower(User.email) == clean_email))
    if not user or not verify_password(clean_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenRead(access_token=create_access_token(user.email), user=user)


@router.post("/reset-password", response_model=TokenRead)
def reset_password(payload: PasswordReset, db: Session = Depends(get_db)) -> TokenRead:
    clean_email = (payload.email or "").strip().lower()
    clean_password = (payload.new_password or "").strip()
    if not clean_email:
        raise HTTPException(status_code=422, detail="Email is required")
    user = db.scalar(select(User).where(func.lower(User.email) == clean_email))
    if not user:
        user = User(email=clean_email, full_name="Student", password_hash=hash_password(clean_password))
        db.add(user)
    else:
        user.password_hash = hash_password(clean_password)
    db.commit()
    db.refresh(user)
    return TokenRead(access_token=create_access_token(user.email), user=user)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(current_user)) -> User:
    return user
