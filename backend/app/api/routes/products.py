from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db_session
from app.db.models.products import Product
from app.schema.products import ProductCreate, ProductResponse

router = APIRouter()

@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db_session)):
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db_session)):
    return db.query(Product).filter(Product.id == product_id).first()

@router.get("/", response_model=list[ProductResponse])
def get_all_products(db: Session = Depends(get_db_session)):
    return db.query(Product).all()

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db_session)):
    existing_product = db.query(Product).filter(Product.id == product_id).first()
    for key, value in product.model_dump().items():
        setattr(existing_product, key, value)
    db.commit()
    db.refresh(existing_product)
    return existing_product

@router.delete("/{product_id}", response_model=dict)
def delete_product(product_id: int, db: Session = Depends(get_db_session)):
    existing_product = db.query(Product).filter(Product.id == product_id).first()
    db.delete(existing_product)
    db.commit()
    return {"message": "Product deleted successfully"}