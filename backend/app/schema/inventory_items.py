from pydantic import BaseModel
from typing import Optional

class InventoryItemBase(BaseModel):
    business_id: int
    product_id: int
    quantity_on_hand: float

class InventoryItemCreate(InventoryItemBase):
    business_id: int
    product_id: int

class InventoryItemUpdate(InventoryItemBase):
    pass

class InventoryItemResponse(InventoryItemBase):
    id: int

    class Config:
        from_attributes = True