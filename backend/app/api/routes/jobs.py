from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import current_user
from app.api.routes.customers import find_customer
from app.core.database import get_db
from app.models import Job, JobStatus, User
from app.schemas.job import JobCreate, JobOut, JobUpdate
from app.services.automation import handle_job_completed, handle_job_created

router = APIRouter(prefix="/jobs", tags=["jobs"])


def find_job(db: Session, business_id: int, job_id: int) -> Job:
    job = db.query(Job).options(joinedload(Job.customer)).filter_by(id=job_id, business_id=business_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("", response_model=list[JobOut])
def list_jobs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return (
        db.query(Job)
        .options(joinedload(Job.customer))
        .filter_by(business_id=user.business_id)
        .order_by(Job.scheduled_at)
        .all()
    )


@router.post("", response_model=JobOut, status_code=201)
def create_job(payload: JobCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    find_customer(db, user.business_id, payload.customer_id)
    job = Job(business_id=user.business_id, **payload.model_dump())
    db.add(job)
    db.flush()
    handle_job_created(db, job)
    db.commit()
    return find_job(db, user.business_id, job.id)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return find_job(db, user.business_id, job_id)


@router.put("/{job_id}", response_model=JobOut)
def update_job(job_id: int, payload: JobUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = find_job(db, user.business_id, job_id)
    old_status = job.status
    if payload.customer_id is not None:
        find_customer(db, user.business_id, payload.customer_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    if old_status != JobStatus.completed and job.status == JobStatus.completed:
        handle_job_completed(db, job)
    db.commit()
    return find_job(db, user.business_id, job.id)


@router.post("/{job_id}/complete", response_model=JobOut)
def complete_job(job_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    job = find_job(db, user.business_id, job_id)
    old_status = job.status
    job.status = JobStatus.completed
    if old_status != JobStatus.completed:
        handle_job_completed(db, job)
    db.commit()
    return find_job(db, user.business_id, job.id)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(find_job(db, user.business_id, job_id))
    db.commit()
