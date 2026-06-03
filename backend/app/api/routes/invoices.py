from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import current_user
from app.api.routes.customers import find_customer
from app.core.database import get_db
from app.models import Invoice, User
from app.schemas.invoice import InvoiceCreate, InvoiceOut, InvoiceUpdate

router = APIRouter(prefix="/invoices", tags=["invoices"])


def find_invoice(db: Session, business_id: int, invoice_id: int) -> Invoice:
    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.customer))
        .filter_by(id=invoice_id, business_id=business_id)
        .first()
    )
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("", response_model=list[InvoiceOut])
def list_invoices(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return (
        db.query(Invoice)
        .options(joinedload(Invoice.customer))
        .filter_by(business_id=user.business_id)
        .order_by(Invoice.due_date)
        .all()
    )


@router.post("", response_model=InvoiceOut, status_code=201)
def create_invoice(payload: InvoiceCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    find_customer(db, user.business_id, payload.customer_id)
    invoice = Invoice(business_id=user.business_id, **payload.model_dump())
    db.add(invoice)
    db.commit()
    return find_invoice(db, user.business_id, invoice.id)


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return find_invoice(db, user.business_id, invoice_id)


@router.put("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(invoice_id: int, payload: InvoiceUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    invoice = find_invoice(db, user.business_id, invoice_id)
    if payload.customer_id is not None:
        find_customer(db, user.business_id, payload.customer_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(invoice, key, value)
    db.commit()
    return find_invoice(db, user.business_id, invoice.id)


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(find_invoice(db, user.business_id, invoice_id))
    db.commit()
