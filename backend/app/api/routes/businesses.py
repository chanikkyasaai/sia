from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db_session
from app.db.models.businesses import Business
from app.schema.businesses import BusinessCreate, BusinessResponse
from typing import cast

router = APIRouter()

@router.post("/", response_model=BusinessResponse)
def create_business(business: BusinessCreate, db: Session = Depends(get_db_session)):
    new_business = Business(**business.model_dump())
    db.add(new_business)
    db.commit()
    db.refresh(new_business)
    return new_business

@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(business_id: int, db: Session = Depends(get_db_session)):
    return db.query(Business).filter(Business.id == business_id).first()

@router.get("/", response_model=list[BusinessResponse])
def get_all_businesses(db: Session = Depends(get_db_session)):
    return db.query(Business).all()

@router.put("/{business_id}", response_model=BusinessResponse)
def update_business(business_id: int, business: BusinessCreate, db: Session = Depends(get_db_session)):
    existing_business = db.query(Business).filter(Business.id == business_id).first()
    for key, value in business.model_dump().items():
        setattr(existing_business, key, value)
    db.commit()
    db.refresh(existing_business)
    return existing_business

@router.delete("/{business_id}", response_model=dict)
def delete_business(business_id: int, db: Session = Depends(get_db_session)):
    existing_business = db.query(Business).filter(Business.id == business_id).first()
    db.delete(existing_business)
    db.commit()
    return {"message": "Business deleted successfully"}
def get_businessId_by_UserId(db: Session, user_id: int) -> int | None:
    business = db.query(Business).filter(Business.user_id == user_id).first()
    if business:
        return cast(int, business.id)
    return None