from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ExpenseBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Expense amount")
    type: str = Field(...,
                      description="Expense type: PURCHASE, OPERATING, FUEL, TRANSPORT, MISC")
    note: Optional[str] = Field(
        None, description="Optional note about the expense")
    occurred_at: datetime = Field(..., description="When the expense occurred")


class ExpenseCreate(ExpenseBase):
    business_id: int = Field(..., description="Business ID")
    source: str = Field(
        default="MANUAL", description="Source: VOICE, MANUAL, IMPORT")


class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0)
    type: Optional[str] = None
    note: Optional[str] = None
    occurred_at: Optional[datetime] = None


class ExpenseResponse(ExpenseBase):
    id: int
    business_id: int
    created_at: datetime
    source: str

    class Config:
        from_attributes = True
