from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.api.deps import get_db_session
from app.db.models.expenses import Expense
from app.schema.expenses import ExpenseCreate, ExpenseUpdate, ExpenseResponse

router = APIRouter()


@router.post("/", response_model=ExpenseResponse)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new expense record"""
    db_expense = Expense(
        business_id=expense.business_id,
        amount=expense.amount,
        type=expense.type,
        note=expense.note,
        occurred_at=expense.occurred_at,
        source=expense.source
    )

    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return db_expense


@router.get("/", response_model=List[ExpenseResponse])
def get_expenses(
    business_id: int = Query(..., description="Business ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of records to return"),
    expense_type: Optional[str] = Query(
        None, description="Filter by expense type"),
    start_date: Optional[date] = Query(
        None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(
        None, description="Filter to date (YYYY-MM-DD)"),
    db: Session = Depends(get_db_session)
):
    """Get expenses for a business with optional filters"""
    query = db.query(Expense).filter(Expense.business_id == business_id)

    if expense_type:
        query = query.filter(Expense.type == expense_type.upper())

    if start_date:
        query = query.filter(Expense.occurred_at >= start_date)

    if end_date:
        # Add one day to include the end date
        end_datetime = datetime.combine(end_date, datetime.min.time()) + \
            timedelta(days=1)
        query = query.filter(Expense.occurred_at < end_datetime)

    expenses = query.order_by(Expense.occurred_at.desc()).offset(
        skip).limit(limit).all()
    return expenses


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db_session)
):
    """Get a specific expense by ID"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    db: Session = Depends(get_db_session)
):
    """Update an existing expense"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    update_data = expense_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    db.commit()
    db.refresh(expense)

    return expense


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete an expense record"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()

    return {"message": "Expense deleted successfully"}


@router.get("/business/{business_id}/summary")
def get_expense_summary(
    business_id: int,
    start_date: Optional[date] = Query(
        None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(
        None, description="Filter to date (YYYY-MM-DD)"),
    db: Session = Depends(get_db_session)
):
    """Get expense summary by type for a business"""
    from sqlalchemy import func

    query = db.query(
        Expense.type,
        func.sum(Expense.amount).label('total_amount'),
        func.count(Expense.id).label('count')
    ).filter(Expense.business_id == business_id)

    if start_date:
        query = query.filter(Expense.occurred_at >= start_date)

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.min.time()) + \
            timedelta(days=1)
        query = query.filter(Expense.occurred_at < end_datetime)

    summary = query.group_by(Expense.type).all()

    total_expenses = sum(item.total_amount for item in summary)

    return {
        "business_id": business_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_expenses": float(total_expenses),
        "by_type": [
            {
                "type": item.type,
                "total_amount": float(item.total_amount),
                "count": item.count
            }
            for item in summary
        ]
    }
