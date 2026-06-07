from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import current_user
from app.api.routes.customers import find_customer
from app.core.database import get_db
from app.models import Quote, User
from app.schemas.quote import QuoteCreate, QuoteOut, QuoteUpdate

router = APIRouter(prefix="/quotes", tags=["quotes"])


def find_quote(db: Session, business_id: int, quote_id: int) -> Quote:
    quote = (
        db.query(Quote)
        .options(joinedload(Quote.customer))
        .filter_by(id=quote_id, business_id=business_id)
        .first()
    )
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.get("", response_model=list[QuoteOut])
def list_quotes(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return (
        db.query(Quote)
        .options(joinedload(Quote.customer))
        .filter_by(business_id=user.business_id)
        .order_by(Quote.valid_until)
        .all()
    )


@router.post("", response_model=QuoteOut, status_code=201)
def create_quote(payload: QuoteCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    find_customer(db, user.business_id, payload.customer_id)
    quote = Quote(business_id=user.business_id, **payload.model_dump())
    db.add(quote)
    db.commit()
    return find_quote(db, user.business_id, quote.id)


@router.get("/{quote_id}", response_model=QuoteOut)
def get_quote(quote_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return find_quote(db, user.business_id, quote_id)


@router.put("/{quote_id}", response_model=QuoteOut)
def update_quote(quote_id: int, payload: QuoteUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    quote = find_quote(db, user.business_id, quote_id)
    if payload.customer_id is not None:
        find_customer(db, user.business_id, payload.customer_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(quote, key, value)
    db.commit()
    return find_quote(db, user.business_id, quote.id)


@router.delete("/{quote_id}", status_code=204)
def delete_quote(quote_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(find_quote(db, user.business_id, quote_id))
    db.commit()
