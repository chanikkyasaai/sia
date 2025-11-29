from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db_session
from app.db.models.customers import Customer
from app.schema.customers import CustomerCreate, CustomerResponse

router = APIRouter()

@router.post("/", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db_session)):
    new_customer = Customer(**customer.model_dump())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db_session)):
    return db.query(Customer).filter(Customer.id == customer_id).first()

@router.get("/", response_model=list[CustomerResponse])
def get_all_customers(db: Session = Depends(get_db_session)):
    return db.query(Customer).all()

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, customer: CustomerCreate, db: Session = Depends(get_db_session)):
    existing_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    for key, value in customer.model_dump().items():
        setattr(existing_customer, key, value)
    db.commit()
    db.refresh(existing_customer)
    return existing_customer

@router.delete("/{customer_id}", response_model=dict)
def delete_customer(customer_id: int, db: Session = Depends(get_db_session)):
    existing_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    db.delete(existing_customer)
    db.commit()
    return {"message": "Customer deleted successfully"}