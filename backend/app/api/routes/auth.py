from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.routes.businesses import get_businessId_by_UserId
from app.db.session import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.db.models.users import User
from app.schema.users import UserCreate, UserLogin, UserResponse
from datetime import timedelta, datetime, timezone
from typing import cast

router = APIRouter()

@router.post("/login")
def login(user_login:UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user or not verify_password(user_login.password, cast(str, user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=timedelta(minutes=30)
    )
    business_id= get_businessId_by_UserId(db, cast(int,user.id))
    return {"access_token": access_token, "token_type": "bearer", "business_id": business_id, "user_id": user.id}

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        name=user_in.name,
        email=user_in.email,
        phone=user_in.phone,
        locale=user_in.locale,
        password_hash=get_password_hash(user_in.password),
        created_at=datetime.now(timezone.utc),
    )

    # Explicitly convert created_at to ISO format
    user.created_at = user.created_at.isoformat()
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
