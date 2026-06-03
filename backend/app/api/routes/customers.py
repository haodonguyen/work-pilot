from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.database import get_db
from app.models import Customer, User
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


def find_customer(db: Session, business_id: int, customer_id: int) -> Customer:
    customer = db.query(Customer).filter_by(id=customer_id, business_id=business_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("", response_model=list[CustomerOut])
def list_customers(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(Customer).filter_by(business_id=user.business_id).order_by(Customer.name).all()


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    customer = Customer(business_id=user.business_id, **payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return find_customer(db, user.business_id, customer_id)


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, payload: CustomerUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    customer = find_customer(db, user.business_id, customer_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(find_customer(db, user.business_id, customer_id))
    db.commit()
