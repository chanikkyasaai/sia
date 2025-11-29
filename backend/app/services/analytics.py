from sqlalchemy.orm import Session
from app.db.models.daily_analytics import DailyAnalytics
from datetime import date, datetime

# Helper: Get or create daily_analytics row for a business and date


def get_or_create_daily_analytics(db: Session, business_id: int, day: date) -> DailyAnalytics:
    row = db.query(DailyAnalytics).filter_by(
        business_id=business_id, date=day).first()
    if row:
        return row
    row = DailyAnalytics(
        business_id=business_id,
        date=day,
        total_sales=0.0,
        total_purchases=0.0,
        total_expenses=0.0,
        credit_given=0.0,
        credit_received=0.0,
        opening_cash_balance=None,
        closing_cash_balance=None,
        net_cash_flow=0.0,
        inventory_value=None,
        credit_outstanding=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

# Helper: Update daily_analytics metrics for a business and date


def update_daily_analytics(db: Session, business_id: int, day: date, **kwargs) -> DailyAnalytics:
    row = get_or_create_daily_analytics(db, business_id, day)
    for key, value in kwargs.items():
        if hasattr(row, key):
            setattr(row, key, value)
    # row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row
