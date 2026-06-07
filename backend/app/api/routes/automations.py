from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models import AutomationEvent, AutomationRule, User
from app.schemas.automation import AutomationEventOut, AutomationRuleCreate, AutomationRuleOut, AutomationRuleUpdate
from app.services.automation import handle_pending_quote_followups

router = APIRouter(tags=["automation"])


def find_rule(db: Session, business_id: int, rule_id: int) -> AutomationRule:
    rule = db.query(AutomationRule).filter_by(id=rule_id, business_id=business_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    return rule


@router.get("/automation-rules", response_model=list[AutomationRuleOut])
def list_rules(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(AutomationRule).filter_by(business_id=user.business_id).order_by(AutomationRule.id).all()


@router.post("/automation-rules", response_model=AutomationRuleOut, status_code=201)
def create_rule(payload: AutomationRuleCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rule = AutomationRule(business_id=user.business_id, **payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/automation-rules/{rule_id}", response_model=AutomationRuleOut)
def update_rule(rule_id: int, payload: AutomationRuleUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rule = find_rule(db, user.business_id, rule_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/automation-rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(find_rule(db, user.business_id, rule_id))
    db.commit()


@router.post("/automation-rules/{rule_id}/test", response_model=AutomationEventOut)
def test_rule(rule_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    rule = find_rule(db, user.business_id, rule_id)
    event = AutomationEvent(
        business_id=user.business_id,
        rule_id=rule.id,
        message=f"Test event queued: {rule.action}",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/automation-rules/run-quote-followups", response_model=list[AutomationEventOut])
def run_quote_followups(user: User = Depends(current_user), db: Session = Depends(get_db)):
    events = handle_pending_quote_followups(db, user.business_id)
    db.commit()
    for event in events:
        db.refresh(event)
    return events


@router.get("/automation-events", response_model=list[AutomationEventOut])
def list_events(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return (
        db.query(AutomationEvent)
        .filter_by(business_id=user.business_id)
        .order_by(AutomationEvent.created_at.desc())
        .all()
    )
