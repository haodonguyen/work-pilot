from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models import AutomationEvent, Job, JobStatus, User

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/suggest-automations")
def suggest_automations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    completed = db.query(Job).filter_by(business_id=user.business_id, status=JobStatus.completed).count()
    events = db.query(AutomationEvent).filter_by(business_id=user.business_id).count()
    suggestions = []
    if completed:
        suggestions.append(
            {
                "title": "Ask completed customers for reviews",
                "reason": f"{completed} completed jobs could become review requests.",
                "rule": "When job is completed -> generate review request",
            }
        )
    suggestions.append(
        {
            "title": "Keep booking confirmations enabled",
            "reason": f"Your automations have already simulated {events} admin tasks.",
            "rule": "When booking is created -> generate confirmation",
        }
    )
    return {"suggestions": suggestions}


@router.post("/generate-message-template")
def generate_message_template(template_type: str, user: User = Depends(current_user)):
    return {
        "business_id": user.business_id,
        "type": template_type,
        "body": "Hi {{customerName}}, this is {{businessName}} confirming your {{serviceType}} booking on {{jobDate}} at {{jobTime}}.",
    }
