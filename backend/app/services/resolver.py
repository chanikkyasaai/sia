"""
Entity resolver service for customer, product, and data resolution
"""
import logging
from typing import Optional, Dict, Any, List, cast
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models.customers import Customer
from app.db.models.products import Product
from app.db.models.transactions import Transaction
from app.db.models.daily_analytics import DailyAnalytics
from app.services.cache import cache_service
from datetime import date, datetime

logger = logging.getLogger(__name__)


class ResolverService:

    async def resolve_customer(self, db: Session, business_id: int, customer_name: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """Resolve customer by name/phone, create if not found"""

        # Try exact phone match first
        if phone:
            customer = db.query(Customer).filter_by(
                business_id=business_id,
                phone=phone
            ).first()
            if customer:
                return {
                    "customer_id": customer.id,
                    "name": customer.name,
                    "phone": customer.phone,
                    "created_new": False
                }

        # Try fuzzy name match
        customers = db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.name.ilike(f"%{customer_name}%")
        ).all()

        if len(customers) == 1:
            customer = customers[0]
            return {
                "customer_id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "created_new": False
            }
        elif len(customers) > 1:
            # Multiple matches - return candidates for user selection
            candidates = [
                {
                    "customer_id": c.id,
                    "name": c.name,
                    "phone": c.phone,
                    "similarity_score": self._calculate_similarity(customer_name, cast(str, c.name)) 
                }
                for c in customers[:5]  # Top 5 matches
            ]
            return {
                "multiple_matches": True,
                "candidates": candidates
            }

        # No match found - create new customer
        new_customer = Customer(
            business_id=business_id,
            name=customer_name.title(),
            phone=phone or "",
            info="Created by voice agent",
            risk_level="LOW",
            avg_delay_days=0,
            created_at=datetime.utcnow()
        )
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)

        return {
            "customer_id": new_customer.id,
            "name": new_customer.name,
            "phone": new_customer.phone,
            "created_new": True
        }

    def resolve_product(self, db: Session, business_id: int, product_name: str) -> Optional[Dict[str, Any]]:
        """Resolve product by name"""

        # Try exact match first
        product = db.query(Product).filter(
            Product.business_id == business_id,
            func.lower(Product.name) == product_name.lower()
        ).first()

        if product:
            return {
                "product_id": product.id,
                "name": product.name,
                "unit_price": product.avg_sale_price
            }

        # Try fuzzy match
        products = db.query(Product).filter(
            Product.business_id == business_id,
            Product.name.ilike(f"%{product_name}%")
        ).limit(3).all()

        if products:
            return {
                "product_id": products[0].id,
                "name": products[0].name,
                "unit_price": products[0].avg_sale_price,
                "fuzzy_match": True
            }

        return None

    def normalize_amount(self, amount_str: str) -> Optional[float]:
        """Normalize currency amount"""
        try:
            # Remove common currency symbols and text
            import re
            cleaned = re.sub(r'[₹$,\s]', '', str(amount_str))
            cleaned = re.sub(r'[^\d.]', '', cleaned)

            if cleaned:
                amount = float(cleaned)
                return amount if amount > 0 else None
        except (ValueError, TypeError):
            pass

        return None

    async def get_business_snapshot(self, db: Session, business_id: int) -> Dict[str, Any]:
        """Get or build business snapshot with caching"""

        # Try cache first
        cached_snapshot = await cache_service.get_business_snapshot(business_id)
        if cached_snapshot:
            return cached_snapshot

        # Build snapshot from database
        today = date.today()

        # Today's analytics
        today_analytics = db.query(DailyAnalytics).filter_by(
            business_id=business_id,
            date=today
        ).first()

        # Calculate credit outstanding
        credit_outstanding = db.query(func.sum(Transaction.amount)).filter(
            Transaction.business_id == business_id,
            Transaction.type == "CREDIT_GIVEN",
            Transaction.note == "PENDING"
        ).scalar() or 0.0

        # Top debtors
        top_debtors_query = db.query(
            Customer.id,
            Customer.name,
            func.sum(Transaction.amount).label('total_due')
        ).join(Transaction).filter(
            Transaction.business_id == business_id,
            Transaction.type == "CREDIT_GIVEN",
            Transaction.note == "PENDING"
        ).group_by(Customer.id, Customer.name).order_by(
            func.sum(Transaction.amount).desc()
        ).limit(5)

        top_debtors = [
            {
                "customer_id": row.id,
                "name": row.name,
                "due": float(row.total_due),
                "avg_delay": 14  # TODO: Calculate actual delay
            }
            for row in top_debtors_query
        ]

        # Low stock count (placeholder)
        low_stock_count = 2  # TODO: Calculate from inventory

        today_sales_value = 0.0
        if today_analytics and hasattr(today_analytics, 'total_sales'):
            sales_val = getattr(today_analytics, 'total_sales', 0.0)
            today_sales_value = float(
                sales_val) if sales_val is not None else 0.0

        credit_val = credit_outstanding if credit_outstanding is not None else 0.0

        snapshot = {
            "today_sales": today_sales_value,
            "credit_outstanding": float(credit_val),
            "low_stock_count": low_stock_count,
            "top_debtors": top_debtors,
            "last_updated": datetime.utcnow().isoformat()
        }

        # Cache for 5 minutes
        await cache_service.set_business_snapshot(business_id, snapshot, 300)

        return snapshot

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Simple similarity score between two strings"""
        str1_lower = str1.lower()
        str2_lower = str2.lower()

        if str1_lower == str2_lower:
            return 1.0

        if str1_lower in str2_lower or str2_lower in str1_lower:
            return 0.8

        # Simple character overlap
        overlap = len(set(str1_lower) & set(str2_lower))
        total_chars = len(set(str1_lower) | set(str2_lower))

        return overlap / total_chars if total_chars > 0 else 0.0


# Global resolver service
resolver_service = ResolverService()
