# app/db/models/daily_analytics.py
from datetime import date, datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    Date,
    Float,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class DailyAnalytics(Base):
    __tablename__ = "daily_analytics"

    id = Column(Integer, primary_key=True, index=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The day this row summarizes (local to business timezone)
    date = Column(Date, nullable=False)

    # Core metrics
    total_sales = Column(Float, nullable=False, default=0.0)          # SALE
    total_purchases = Column(Float, nullable=False, default=0.0)      # PURCHASE
    total_expenses = Column(Float, nullable=False, default=0.0)       # EXPENSE (non‑stock)
    credit_given = Column(Float, nullable=False, default=0.0)         # CREDIT_GIVEN
    credit_received = Column(Float, nullable=False, default=0.0)      # CREDIT_RECEIVED

    # Cash & liquidity view
    opening_cash_balance = Column(Float, nullable=True)               # optional
    closing_cash_balance = Column(Float, nullable=True)
    net_cash_flow = Column(Float, nullable=False, default=0.0)        # inflow - outflow

    # Inventory + risk snapshot (optional but useful for FHE)
    inventory_value = Column(Float, nullable=True)                    # value of stock at end of day
    credit_outstanding = Column(Float, nullable=True)                 # total khata at end of day

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )

    business = relationship("Business", back_populates="daily_analytics")

    __table_args__ = (
        UniqueConstraint("business_id", "date", name="uq_daily_analytics_business_date"),
    )
