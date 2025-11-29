from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_db_session
from app.db.models.transactions import Transaction
from app.schema.transactions import TransactionCreate, TransactionResponse

router = APIRouter()

@router.post("/", response_model=TransactionResponse)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db_session)):
    new_transaction = Transaction(**transaction.model_dump())
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db_session)):
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

@router.get("/", response_model=list[TransactionResponse])
def get_all_transactions(db: Session = Depends(get_db_session)):
    return (
        db.query(Transaction)
        .options(joinedload(Transaction.customer), joinedload(Transaction.product))
        .all()
    )

@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: int, transaction: TransactionCreate, db: Session = Depends(get_db_session)):
    existing_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    for key, value in transaction.model_dump().items():
        setattr(existing_transaction, key, value)
    db.commit()
    db.refresh(existing_transaction)
    return existing_transaction

@router.delete("/{transaction_id}", response_model=dict)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db_session)):
    existing_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    db.delete(existing_transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}

@router.get("/add_many")
def add_many_transactions(transactions: list[TransactionCreate], db: Session = Depends(get_db_session)):
    new_transactions = [Transaction(**transaction.model_dump()) for transaction in transactions]
    db.add_all(new_transactions)
    db.commit()
    return {"message": f"Added {len(new_transactions)} transactions successfully"}
