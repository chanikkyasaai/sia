# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
from app.db.session import engine
from app.db.models.users import User
from app.db.models.businesses import Business
from app.db.models.customers import Customer
from app.db.models.products import Product
from app.db.models.inventory_items import InventoryItem
from app.db.models.transactions import Transaction
from app.db.models.reminders import Reminder
from app.db.models.edit_logs import EditLog
from app.db.models.conversation_logs import ConversationLog
from app.db.models.daily_analytics import DailyAnalytics

from app.api.routes.businesses import router as businesses_router
from app.api.routes.customers import router as customers_router
from app.api.routes.products import router as products_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.transactions import router as transactions_router
from app.api.routes.reminders import router as reminders_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.auth import router as auth_router
from app.api.routes.voice import router as voice_router
from app.core.twilio_sms import sms_route
from app.api.routes.expenses import router as expenses_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.db.session import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed (will continue without DB): {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# ---------- CORS (allow your RN app) ----------

origins = [
    "http://localhost:19006",   # Expo default
    "http://localhost:3000",
    "*",                        # relax in hackathon; tighten later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Health check ----------

@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "env": settings.ENV}

@app.get("/", tags=["system"])
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}!"}

# Include routers
app.include_router(businesses_router, prefix="/businesses", tags=["businesses"])
app.include_router(customers_router, prefix="/customers", tags=["customers"])
app.include_router(products_router, prefix="/products", tags=["products"])
app.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
app.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
app.include_router(reminders_router, prefix="/reminders", tags=["reminders"])
app.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(voice_router, prefix="/voice", tags=["voice"])
app.include_router(sms_route, prefix="/sms", tags=["sms"])
app.include_router(expenses_router, prefix="/expenses", tags=["expenses"])
