from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Business, MessageTemplate, User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.services.automation import DEFAULT_TEMPLATES, seed_default_rules

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if not settings.allow_signups:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Signups are disabled")
    if settings.signup_invite_code and payload.invite_code != settings.signup_invite_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signup invite code")
    if db.query(User).filter_by(email=payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    business = Business(name=payload.business_name)
    db.add(business)
    db.flush()
    user = User(
        business_id=business.id,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="owner",
    )
    db.add(user)
    seed_default_rules(db, business.id)
    for template_type, name, body in DEFAULT_TEMPLATES:
        db.add(MessageTemplate(business_id=business.id, type=template_type, name=name, body=body))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenOut(access_token=create_access_token(user.email))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
