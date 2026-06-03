from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models import MessageTemplate, User
from app.schemas.template import MessageTemplateCreate, MessageTemplateOut, MessageTemplateUpdate

router = APIRouter(prefix="/templates", tags=["templates"])


def find_template(db: Session, business_id: int, template_id: int) -> MessageTemplate:
    template = db.query(MessageTemplate).filter_by(id=template_id, business_id=business_id).first()
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("", response_model=list[MessageTemplateOut])
def list_templates(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(MessageTemplate).filter_by(business_id=user.business_id).order_by(MessageTemplate.type).all()


@router.post("", response_model=MessageTemplateOut, status_code=201)
def create_template(payload: MessageTemplateCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    template = MessageTemplate(business_id=user.business_id, **payload.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/{template_id}", response_model=MessageTemplateOut)
def update_template(template_id: int, payload: MessageTemplateUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    template = find_template(db, user.business_id, template_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(find_template(db, user.business_id, template_id))
    db.commit()
