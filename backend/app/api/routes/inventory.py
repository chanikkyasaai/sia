from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db_session
from app.db.models.inventory_items import InventoryItem
from app.schema.inventory_items import InventoryItemCreate, InventoryItemResponse

router = APIRouter()

@router.post("/", response_model=InventoryItemResponse)
def create_inventory_item(item: InventoryItemCreate, db: Session = Depends(get_db_session)):
    new_item = InventoryItem(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/{item_id}", response_model=InventoryItemResponse)
def get_inventory_item(item_id: int, db: Session = Depends(get_db_session)):
    return db.query(InventoryItem).filter(InventoryItem.id == item_id).first()

@router.get("/", response_model=list[InventoryItemResponse])
def get_all_inventory_items(db: Session = Depends(get_db_session)):
    return db.query(InventoryItem).all()

@router.put("/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(item_id: int, item: InventoryItemCreate, db: Session = Depends(get_db_session)):
    existing_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    for key, value in item.model_dump().items():
        setattr(existing_item, key, value)
    db.commit()
    db.refresh(existing_item)
    return existing_item

@router.delete("/{item_id}", response_model=dict)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db_session)):
    existing_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    db.delete(existing_item)
    db.commit()
    return {"message": "Inventory item deleted successfully"}