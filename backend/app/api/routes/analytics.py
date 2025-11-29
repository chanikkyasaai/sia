from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db_session
from sqlalchemy.sql.expression import literal

router = APIRouter()
# app/api/routes/analytics.py
from datetime import date, datetime, time, timedelta
from typing import List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models.daily_analytics import DailyAnalytics
from app.db.models.transactions import Transaction
from app.schema.analytics import DailyAnalyticsRead, RangeAnalyticsSummary

router = APIRouter()


# ---------- Helpers ----------

def _compute_daily_from_transactions(
    db: Session,
    business_id: int,
    day: date,
) -> DailyAnalytics:
    """
    Fallback: compute a DailyAnalytics object in Python from raw transactions
    for a given business + date. You can later move this into services.analytics_core.
    """
    start_dt = datetime.combine(day, time.min)
    end_dt = datetime.combine(day, time.max)

    txs: List[Transaction] = (
        db.query(Transaction)
        .filter(
            Transaction.business_id == business_id,
            Transaction.created_at >= start_dt,
            Transaction.created_at <= end_dt,
        )
        .all()
    )

    total_sales = total_purchases = total_expenses = 0.0
    credit_given = credit_received = 0.0

    # Fix conditional operands and type extraction
    for tx in txs:
        if tx.type.scalar() == "SALE":
            total_sales += tx.amount.scalar()
        elif tx.type.scalar() == "PURCHASE":
            total_purchases += tx.amount.scalar()
        elif tx.type.scalar() == "EXPENSE":
            total_expenses += tx.amount.scalar()
        elif tx.type.scalar() == "CREDIT_GIVEN":
            credit_given += tx.amount.scalar()
        elif tx.type.scalar() == "CREDIT_RECEIVED":
            credit_received += tx.amount.scalar()

    net_cash_flow = (total_sales + credit_received) - (
        total_purchases + total_expenses + credit_given
    )

    # NOTE: inventory_value, credit_outstanding, opening/closing_cash
    # can be filled via other helpers later; keeping None/0 for now.
    daily = DailyAnalytics(
        business_id=business_id,
        date=day,
        total_sales=total_sales,
        total_purchases=total_purchases,
        total_expenses=total_expenses,
        credit_given=credit_given,
        credit_received=credit_received,
        net_cash_flow=net_cash_flow,
    )
    return daily


# ---------- Routes ----------


@router.get("/daily", response_model=DailyAnalyticsRead)
def get_daily_analytics(
    business_id: int = Query(...),
    day: date = Query(..., alias="date"),
    db: Session = Depends(get_db_session),
):
    """
    Return analytics for a single day.
    1) Try to read from daily_analytics table
    2) If not found, compute on the fly from transactions (no DB insert)
    """
    row: Optional[DailyAnalytics] = (
        db.query(DailyAnalytics)
        .filter(
            DailyAnalytics.business_id == business_id,
            DailyAnalytics.date == day,
        )
        .first()
    )

    if row is None:
        # Fallback computation (read‑only)
        row = _compute_daily_from_transactions(db, business_id, day)

    return row


@router.get("/summary", response_model=RangeAnalyticsSummary)
def get_range_summary(
    business_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db_session),
):
    """
    Aggregate analytics between start_date and end_date (inclusive)
    using daily_analytics rows. If a day is missing, it can be
    computed on the fly from transactions.
    """
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    # Load all existing daily rows in range
    rows: List[DailyAnalytics] = (
        db.query(DailyAnalytics)
        .filter(
            DailyAnalytics.business_id == business_id,
            DailyAnalytics.date >= start_date,
            DailyAnalytics.date <= end_date,
        )
        .order_by(DailyAnalytics.date)
        .all()
    )

    # Optionally fill gaps by computing from transactions
    existing_dates = {r.date for r in rows}
    current = start_date
    while current <= end_date:
        if current not in existing_dates:
            rows.append(_compute_daily_from_transactions(db, business_id, current))
        current = current + timedelta(days=1)

    # Ensure sorted
    rows.sort(key=lambda r: r.date)

    total_sales = sum(r.total_sales for r in rows)
    total_purchases = sum(r.total_purchases for r in rows)
    total_expenses = sum(r.total_expenses for r in rows)
    credit_given = sum(r.credit_given for r in rows)
    credit_received = sum(r.credit_received for r in rows)
    net_cash_flow = sum(r.net_cash_flow for r in rows)

    # Fix type mismatches for Pydantic schemas
    return RangeAnalyticsSummary(
        business_id=business_id,
        start_date=start_date,
        end_date=end_date,
        total_sales=cast(float, total_sales),
        total_purchases=cast(float, total_purchases),
        total_expenses=cast(float, total_expenses),
        credit_given=cast(float, credit_given),
        credit_received=cast(float, credit_received),
        net_cash_flow=cast(float, net_cash_flow),
        days=[DailyAnalyticsRead.model_validate(row) for row in rows],
    )
