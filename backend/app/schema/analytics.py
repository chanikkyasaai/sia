# app/schemas/analytics.py
from datetime import date, datetime
from typing import List
from pydantic import BaseModel


class DailyAnalyticsBase(BaseModel):
    date: date
    total_sales: float = 0.0
    total_purchases: float = 0.0
    total_expenses: float = 0.0
    credit_given: float = 0.0
    credit_received: float = 0.0
    opening_cash_balance: float | None = None
    closing_cash_balance: float | None = None
    net_cash_flow: float = 0.0
    inventory_value: float | None = None
    credit_outstanding: float | None = None


class DailyAnalyticsCreate(DailyAnalyticsBase):
    business_id: int


class DailyAnalyticsRead(DailyAnalyticsBase):
    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
class RangeAnalyticsSummary(BaseModel):
    business_id: int
    start_date: date
    end_date: date

    total_sales: float
    total_purchases: float
    total_expenses: float
    credit_given: float
    credit_received: float
    net_cash_flow: float

    # optional extra info for charts
    days: List[DailyAnalyticsRead] = []

    class Config:
        from_attributes = True