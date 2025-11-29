"""
Execution Engine for SIA Voice Agent

Handles atomic database operations for different intents with transaction management.
"""

from typing import Dict, Any, List, Optional, cast
from datetime import datetime, date
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from decimal import Decimal

from app.db.models.transactions import Transaction
from app.db.models.customers import Customer
from app.db.models.products import Product
from app.db.models.inventory_items import InventoryItem
from app.db.models.expenses import Expense
from app.db.models.businesses import Business
from app.db.models.daily_analytics import DailyAnalytics
from app.schema.transactions import TransactionCreate
from app.schema.customers import CustomerCreate
from app.schema.products import ProductCreate
from app.schema.inventory_items import InventoryItemCreate
from app.schema.expenses import ExpenseCreate
from app.services.llm import LLMService
from sqlalchemy import text

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Atomic database execution engine for voice agent actions"""

    def __init__(self):
        self.llm_service = LLMService()

        # Database schema for dynamic query generation
        self.database_schema = {
            "transactions": {
                "columns": ["id", "business_id", "customer_id", "product_id", "type", "amount", "quantity", "note", "source", "created_at"],
                "types": {"id": "INTEGER", "business_id": "INTEGER", "customer_id": "INTEGER", "product_id": "INTEGER", "type": "VARCHAR", "amount": "DECIMAL", "quantity": "DECIMAL", "note": "TEXT", "source": "VARCHAR", "created_at": "TIMESTAMP"},
                "description": "Business transactions including sales, purchases, and credit movements"
            },
            "customers": {
                "columns": ["id", "business_id", "name", "phone", "risk_level", "credit", "created_at"],
                "types": {"id": "INTEGER", "business_id": "INTEGER", "name": "VARCHAR", "phone": "VARCHAR", "risk_level": "LOW|HIGH", "credit": "DECIMAL", "created_at": "TIMESTAMP"},
                "description": "Customer information with outstanding balances"
            },
            "products": {
                "columns": ["id", "business_id", "name", "avg_sale_price", "avg_cost_price" ,"low_stock_threshold", "is_active", "created_at"],
                "types": {"id": "INTEGER", "business_id": "INTEGER", "name": "VARCHAR", "avg_sale_price": "DECIMAL", "avg_cost_price": "DECIMAL",  "low_stock_threshold": "INTEGER", "is_active": "BOOLEAN", "created_at": "TIMESTAMP"},
                "description": "Product catalog with pricing and stock thresholds"
            },
            "inventory_items": {
                "columns": ["id", "business_id", "product_id", "quantity_on_hand", "updated_at"],
                "types": {"id": "INTEGER", "business_id": "INTEGER", "product_id": "INTEGER", "quantity_on_hand": "DECIMAL", "updated_at": "TIMESTAMP"},
                "description": "Current inventory levels and stock management"
            },
            "daily_analytics": {
                "columns": ["id", "business_id", "date", "total_sales", "total_purchases", "total_expenses", "transaction_count", "customer_count"],
                "types": {"id": "INTEGER", "business_id": "INTEGER", "date": "DATE", "total_sales": "DECIMAL", "total_purchases": "DECIMAL", "total_expenses": "DECIMAL", "transaction_count": "INTEGER", "customer_count": "INTEGER"},
                "description": "Pre-aggregated daily business metrics"
            }
        }

    async def execute_intent(
        self,
        db: Session,
        business_id: str,
        user_id: str,
        intent: str,
        entities: Dict[str, Any],
        resolved_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an intent with atomic database operations

        Args:
            db: Database session
            business_id: Business UUID
            user_id: User UUID
            intent: Parsed intent
            entities: Raw entities
            resolved_entities: Resolved entities with IDs

        Returns:
            Dict with execution results
        """
        try:
            if intent in ["SALE_TRANSACTION", "TXN_SALE"]:
                return await self._execute_sale_transaction(
                    db, business_id, user_id, entities, resolved_entities
                )
            elif intent in ["PURCHASE_TRANSACTION", "TXN_PURCHASE"]:
                return await self._execute_purchase_transaction(
                    db, business_id, user_id, entities, resolved_entities
                )
            elif intent in ["CREDIT_GIVEN", "TXN_CREDIT_GIVEN"]:
                return await self._execute_credit_given(
                    db, business_id, user_id, entities, resolved_entities
                )
            elif intent in ["CREDIT_RECEIVED", "TXN_CREDIT_RECEIVED"]:
                return await self._execute_credit_received(
                    db, business_id, user_id, entities, resolved_entities
                )
            elif intent in ["EXPENSE_RECORD", "TXN_EXPENSE"]:
                return await self._execute_expense_record(
                    db, business_id, user_id, entities, resolved_entities
                )
            elif intent in ["INVENTORY_UPDATE", "UPDATE_INVENTORY"]:
                return await self._execute_inventory_update(
                    db, business_id, user_id, entities, resolved_entities
                )
            elif intent in ["CUSTOMER_CREATE", "CREATE_CUSTOMER"]:
                return await self._execute_customer_create(
                    db, business_id, user_id, entities, resolved_entities
                )
            elif intent in ["PRODUCT_CREATE", "CREATE_PRODUCT"]:
                return await self._execute_product_create(
                    db, business_id, user_id, entities, resolved_entities
                )
            else:
                # Query intents (no DB writes)
                return await self._execute_query_intent(
                    db, business_id, intent, entities
                )

        except SQLAlchemyError as e:
            logger.error(f"Database error executing {intent}: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "message": f"Database error: {str(e)}",
                "actions_taken": [],
                "data": None
            }
        except Exception as e:
            logger.error(f"Execution error for {intent}: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "message": f"Execution error: {str(e)}",
                "actions_taken": [],
                "data": None
            }

    async def _execute_sale_transaction(
        self,
        db: Session,
        business_id: str,
        user_id: str,
        entities: Dict[str, Any],
        resolved_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute sale transaction with inventory updates"""

        # Get resolved customer
        customer_info = resolved_entities.get("customer", {})
        customer_id = customer_info.get(
            "customer_id") or customer_info.get("id")

        # Get resolved product
        product_info = resolved_entities.get("product", {})
        product_id = product_info.get("product_id") or product_info.get("id")

        # Extract transaction details
        amount = Decimal(str(entities.get("sale_amount")
                         or entities.get("amount", 0)))
        quantity = Decimal(entities.get("quantity", 1))
        payment_method = entities.get("payment_method", "CASH")

        actions_taken = []

        try:
            # Create transaction record
            transaction = Transaction(
                business_id=int(business_id),
                customer_id=customer_id,
                product_id=product_id,
                type="SALE",
                amount=amount,
                quantity=quantity,
                note=entities.get("notes", ""),
                source="VOICE_AGENT",
                created_at=datetime.utcnow()
            )
            db.add(transaction)
            actions_taken.append(f"Created sale transaction for ₹{amount}")

            # Update inventory if product exists
            if product_id:
                inventory_item = db.query(InventoryItem).filter(
                    InventoryItem.business_id == business_id,
                    InventoryItem.product_id == product_id
                ).first()

                if inventory_item:
                    inventory_item.quantity_on_hand = inventory_item.quantity_on_hand - \
                        quantity  # type: ignore
                    inventory_item.updated_at = datetime.utcnow()  # type: ignore
                    actions_taken.append(
                        f"Updated inventory: -{quantity} units")

                    # Check for low stock warning using product's threshold
                    product = db.query(Product).filter(
                        Product.id == product_id).first()
                    if product and getattr(product, 'low_stock_threshold', None) is not None:
                        threshold = getattr(product, 'low_stock_threshold')
                        current_stock = getattr(
                            inventory_item, 'quantity_on_hand')
                        if current_stock <= threshold:
                            actions_taken.append(
                                f"⚠️ Low stock warning for {product_info.get('name', 'product')}")

            # Update daily analytics
            today = date.today()
            daily_analytics = db.query(DailyAnalytics).filter(
                DailyAnalytics.business_id == business_id,
                DailyAnalytics.date == today
            ).first()

            if not daily_analytics:
                daily_analytics = DailyAnalytics(
                    business_id=business_id,
                    date=today,
                    total_sales=float(amount),
                    total_purchases=0.0,
                    total_expenses=0.0,
                )
                db.add(daily_analytics)
            else:
                # Read current value and perform Python-side addition
                current_sales = float(
                    getattr(daily_analytics, 'total_sales', 0.0) or 0.0)
                daily_analytics.total_sales = current_sales + \
                    float(amount)  # type: ignore

            actions_taken.append("Updated daily analytics")

            # Commit transaction
            db.commit()

            return {
                "success": True,
                "actions_taken": actions_taken,
                "data": {
                    "transaction_id": str(transaction.id),
                    "amount": float(amount),
                    "customer": customer_info.get("name", "Unknown"),
                    "product": product_info.get("name", "Unknown"),
                    "quantity": quantity
                },
                "message": f"Sale of ₹{amount} recorded successfully"
            }

        except Exception as e:
            db.rollback()
            raise e

    async def _execute_purchase_transaction(
        self,
        db: Session,
        business_id: str,
        user_id: str,
        entities: Dict[str, Any],
        resolved_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute purchase transaction with inventory updates"""

        # Get resolved supplier (as customer)
        supplier_info = resolved_entities.get("customer", {})
        supplier_id = supplier_info.get("id")

        # Get resolved product
        product_info = resolved_entities.get("product", {})
        product_id = product_info.get("id")

        # Extract transaction details
        amount = Decimal(str(entities.get("amount", 0)))
        quantity = float(entities.get("quantity", 1))
        payment_method = entities.get("payment_method", "CASH")

        actions_taken = []

        try:
            # Begin transaction
            db.begin()

            # Create transaction record
            transaction = Transaction(
                business_id=business_id,
                user_id=user_id,
                customer_id=supplier_id,  # Supplier as customer
                product_id=product_id,
                type="PURCHASE",
                amount=amount,
                quantity=quantity,
                payment_method=payment_method,
                transaction_date=datetime.utcnow(),
                notes=entities.get("notes", ""),
                created_at=datetime.utcnow()
            )
            db.add(transaction)
            actions_taken.append(f"Created purchase transaction for ₹{amount}")

            # Update inventory if product exists
            if product_id:
                inventory_item = db.query(InventoryItem).filter(
                    InventoryItem.business_id == business_id,
                    InventoryItem.product_id == product_id
                ).first()

                if inventory_item:
                    inventory_item.quantity_on_hand = inventory_item.quantity_on_hand + \
                        Decimal(str(quantity))  # type: ignore
                    inventory_item.updated_at = datetime.utcnow()  # type: ignore
                    actions_taken.append(
                        f"Updated inventory: +{quantity} units")
                else:
                    # Create new inventory item
                    new_inventory = InventoryItem(
                        business_id=business_id,
                        product_id=product_id,
                        quantity_on_hand=Decimal(str(quantity)),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_inventory)
                    actions_taken.append(
                        f"Created inventory record: {quantity} units")

            # Update daily analytics
            today = date.today()
            daily_analytics = db.query(DailyAnalytics).filter(
                DailyAnalytics.business_id == business_id,
                DailyAnalytics.date == today
            ).first()

            if not daily_analytics:
                daily_analytics = DailyAnalytics(
                    business_id=business_id,
                    date=today,
                    total_sales=0.0,
                    total_purchases=float(amount),
                    total_expenses=0.0,
                )
                db.add(daily_analytics)
            else:
                # Read current value and perform Python-side addition
                current_purchases = float(
                    getattr(daily_analytics, 'total_purchases', 0.0) or 0.0)
                daily_analytics.total_purchases = current_purchases + \
                    float(amount)  # type: ignore

            actions_taken.append("Updated daily analytics")

            # Commit transaction
            db.commit()

            return {
                "success": True,
                "actions_taken": actions_taken,
                "data": {
                    "transaction_id": str(transaction.id),
                    "amount": float(amount),
                    "supplier": supplier_info.get("name", "Unknown"),
                    "product": product_info.get("name", "Unknown"),
                    "quantity": quantity
                },
                "message": f"Purchase of ₹{amount} recorded successfully"
            }

        except Exception as e:
            db.rollback()
            raise e

    async def _execute_expense_record(
        self,
        db: Session,
        business_id: str,
        user_id: str,
        entities: Dict[str, Any],
        resolved_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute expense recording"""

        # Extract expense details
        amount = Decimal(str(entities.get("amount", 0)))
        category = entities.get("category", "OTHER")
        description = entities.get("description", "")

        actions_taken = []

        try:
            # Begin transaction
            db.begin()

            # Create expense record
            expense = Expense(
                business_id=business_id,
                user_id=user_id,
                amount=amount,
                category=category,
                description=description,
                expense_date=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.add(expense)
            actions_taken.append(f"Created expense record for ₹{amount}")

            # Update daily analytics
            today = date.today()
            daily_analytics = db.query(DailyAnalytics).filter(
                DailyAnalytics.business_id == business_id,
                DailyAnalytics.date == today
            ).first()

            if not daily_analytics:
                daily_analytics = DailyAnalytics(
                    business_id=business_id,
                    date=today,
                    total_sales=0.0,
                    total_purchases=0.0,
                    total_expenses=float(amount),
                )
                db.add(daily_analytics)
            else:
                # Read current value and perform Python-side addition
                current_expenses = float(
                    getattr(daily_analytics, 'total_expenses', 0.0) or 0.0)
                daily_analytics.total_expenses = current_expenses + \
                    float(amount)  # type: ignore

            actions_taken.append("Updated daily analytics")

            # Commit transaction
            db.commit()

            return {
                "success": True,
                "actions_taken": actions_taken,
                "data": {
                    "expense_id": str(expense.id),
                    "amount": float(amount),
                    "category": category,
                    "description": description
                },
                "message": f"Expense of ₹{amount} for {category} recorded successfully"
            }

        except Exception as e:
            db.rollback()
            raise e

    async def _execute_customer_create(
        self,
        db: Session,
        business_id: str,
        user_id: str,
        entities: Dict[str, Any],
        resolved_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute customer creation"""

        # Extract customer details
        name = entities.get("customer_name", "")
        phone = entities.get("phone", "")
        address = entities.get("address", "")

        actions_taken = []

        try:
            # Begin transaction
            db.begin()

            # Create customer record
            customer = Customer(
                business_id=business_id,
                name=name,
                phone=phone,
                address=address,
                balance=Decimal('0'),
                created_at=datetime.utcnow()
            )
            db.add(customer)
            actions_taken.append(f"Created customer: {name}")

            # Commit transaction
            db.commit()

            return {
                "success": True,
                "actions_taken": actions_taken,
                "data": {
                    "customer_id": str(customer.id),
                    "name": name,
                    "phone": phone,
                    "address": address
                },
                "message": f"Customer {name} created successfully"
            }

        except Exception as e:
            db.rollback()
            raise e

    async def _execute_credit_given(
        self,
        db: Session,
        business_id: str,
        user_id: str,
        entities: Dict[str, Any],
        resolved_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute credit given transaction"""

        # Get resolved customer
        customer_info = resolved_entities.get("customer", {})
        customer_id = customer_info.get("id")

        # Extract transaction details
        amount = Decimal(str(entities.get("amount", 0)))

        actions_taken = []

        try:
            # Begin transaction
            db.begin()

            # Create transaction record
            transaction = Transaction(
                business_id=business_id,
                user_id=user_id,
                customer_id=customer_id,
                type="CREDIT_GIVEN",
                amount=amount,
                payment_method="CREDIT",
                transaction_date=datetime.utcnow(),
                notes=entities.get("notes", ""),
                created_at=datetime.utcnow()
            )
            db.add(transaction)
            actions_taken.append(f"Recorded credit given: ₹{amount}")

            # Update customer balance
            if customer_id:
                customer = db.query(Customer).filter(
                    Customer.id == customer_id).first()
                if customer:
                    customer.balance += amount  # Positive balance = money owed to business
                    actions_taken.append(
                        f"Updated {customer_info.get('name', 'customer')} balance")

            # Commit transaction
            db.commit()

            return {
                "success": True,
                "actions_taken": actions_taken,
                "data": {
                    "transaction_id": str(transaction.id),
                    "amount": float(amount),
                    "customer": customer_info.get("name", "Unknown")
                },
                "message": f"Credit of ₹{amount} given to {customer_info.get('name', 'customer')}"
            }

        except Exception as e:
            db.rollback()
            raise e

    async def _execute_credit_received(
        self,
        db: Session,
        business_id: str,
        user_id: str,
        entities: Dict[str, Any],
        resolved_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute credit received transaction"""

        # Get resolved customer
        customer_info = resolved_entities.get("customer", {})
        customer_id = customer_info.get("id")

        # Extract transaction details
        amount = Decimal(str(entities.get("amount", 0)))

        actions_taken = []

        try:
            # Begin transaction
            db.begin()

            # Create transaction record
            transaction = Transaction(
                business_id=business_id,
                user_id=user_id,
                customer_id=customer_id,
                type="CREDIT_RECEIVED",
                amount=amount,
                payment_method="CREDIT",
                transaction_date=datetime.utcnow(),
                notes=entities.get("notes", ""),
                created_at=datetime.utcnow()
            )
            db.add(transaction)
            actions_taken.append(f"Recorded credit received: ₹{amount}")

            # Update customer balance
            if customer_id:
                customer = db.query(Customer).filter(
                    Customer.id == customer_id).first()
                if customer:
                    customer.credit -= amount  # Reduce customer debt
                    actions_taken.append(
                        f"Updated {customer_info.get('name', 'customer')} balance")

            # Commit transaction
            db.commit()

            return {
                "success": True,
                "actions_taken": actions_taken,
                "data": {
                    "transaction_id": str(transaction.id),
                    "amount": float(amount),
                    "customer": customer_info.get("name", "Unknown")
                },
                "message": f"Payment of ₹{amount} received from {customer_info.get('name', 'customer')}"
            }

        except Exception as e:
            db.rollback()
            raise e

    async def _execute_inventory_update(
        self,
        db: Session,
        business_id: str,
        user_id: str,
        entities: Dict[str, Any],
        resolved_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute inventory update"""

        # Get resolved product
        product_info = resolved_entities.get("product", {})
        product_id = product_info.get("id")

        # Extract inventory details
        quantity_change = float(entities.get("quantity", 0))
        operation = entities.get("operation", "SET")  # SET, ADD, SUBTRACT

        actions_taken = []

        try:
            # Begin transaction
            db.begin()

            # Find or create inventory item
            inventory_item = db.query(InventoryItem).filter(
                InventoryItem.business_id == business_id,
                InventoryItem.product_id == product_id
            ).first()

            if not inventory_item:
                inventory_item = InventoryItem(
                    business_id=business_id,
                    product_id=product_id,
                    quantity_on_hand=Decimal('0'),
                    updated_at=datetime.utcnow()
                )
                db.add(inventory_item)
                actions_taken.append(
                    f"Created inventory record for {product_info.get('name', 'product')}")

            # Update quantity based on operation
            old_quantity = inventory_item.quantity_on_hand
            quantity_decimal = Decimal(str(quantity_change))
            if operation == "SET":
                inventory_item.quantity_on_hand = quantity_decimal  # type: ignore
            elif operation == "ADD":
                inventory_item.quantity_on_hand = inventory_item.quantity_on_hand + \
                    quantity_decimal  # type: ignore
            elif operation == "SUBTRACT":
                inventory_item.quantity_on_hand = inventory_item.quantity_on_hand - \
                    quantity_decimal  # type: ignore

            inventory_item.updated_at = datetime.utcnow()  # type: ignore

            actions_taken.append(
                f"Updated inventory: {old_quantity} → {inventory_item.quantity_on_hand} units"
            )

            # Check for warnings using product's threshold
            product = db.query(Product).filter(
                Product.id == product_id).first()
            if product and getattr(product, 'low_stock_threshold', None) is not None:
                threshold = getattr(product, 'low_stock_threshold')
                current_stock = getattr(inventory_item, 'quantity_on_hand')
                if current_stock <= threshold:
                    actions_taken.append(f"⚠️ Low stock warning")

            # Commit transaction
            db.commit()

            return {
                "success": True,
                "actions_taken": actions_taken,
                "data": {
                    "product": product_info.get("name", "Unknown"),
                    "old_quantity": old_quantity,
                    "new_quantity": inventory_item.quantity_on_hand,
                    "operation": operation
                },
                "message": f"Inventory updated for {product_info.get('name', 'product')}"
            }

        except Exception as e:
            db.rollback()
            raise e

    async def _execute_product_create(
        self,
        db: Session,
        business_id: str,
        user_id: str,
        entities: Dict[str, Any],
        resolved_entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute product creation"""

        # Extract product details
        name = entities.get("product_name", "")
        price = Decimal(str(entities.get("price", 0)))
        category = entities.get("category", "OTHER")
        description = entities.get("description", "")

        actions_taken = []

        try:
            # Begin transaction
            db.begin()

            # Create product record
            product = Product(
                business_id=business_id,
                name=name,
                price=price,
                category=category,
                description=description,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(product)
            actions_taken.append(f"Created product: {name}")

            # Create initial inventory record if quantity provided
            if entities.get("quantity"):
                quantity = float(entities.get("quantity", 0))
                inventory_item = InventoryItem(
                    business_id=business_id,
                    product_id=product.id,
                    quantity_on_hand=Decimal(str(quantity)),
                    updated_at=datetime.utcnow()
                )
                db.add(inventory_item)
                actions_taken.append(f"Created inventory: {quantity} units")

            # Commit transaction
            db.commit()

            return {
                "success": True,
                "actions_taken": actions_taken,
                "data": {
                    "product_id": str(product.id),
                    "name": name,
                    "price": float(price),
                    "category": category
                },
                "message": f"Product {name} created successfully"
            }

        except Exception as e:
            db.rollback()
            raise e

    async def _execute_query_intent(
        self,
        db: Session,
        business_id: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute query intents (read-only operations)"""

        try:
            if intent == "STOCK_INQUIRY":
                return await self._handle_stock_inquiry(db, business_id, entities)
            elif intent == "SALES_INQUIRY":
                return await self._handle_sales_inquiry(db, business_id, entities)
            elif intent == "CUSTOMER_INQUIRY":
                return await self._handle_customer_inquiry(db, business_id, entities)
            elif intent == "BALANCE_INQUIRY":
                return await self._handle_balance_inquiry(db, business_id, entities)
            else:
                # Use GPT-4 mini to generate dynamic query for unhandled intents
                return await self._generate_dynamic_query(db, business_id, intent, entities)

        except Exception as e:
            logger.error(f"Query execution error for {intent}: {str(e)}")
            return {
                "success": False,
                "error": f"Query error: {str(e)}",
                "actions_taken": [],
                "data": None
            }

    async def _handle_stock_inquiry(
        self,
        db: Session,
        business_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle stock level inquiries"""

        product_name = entities.get("product_name")

        if product_name:
            # Specific product stock
            product = db.query(Product).filter(
                Product.business_id == business_id,
                Product.name.ilike(f"%{product_name}%")
            ).first()

            if product:
                inventory = db.query(InventoryItem).filter(
                    InventoryItem.business_id == business_id,
                    InventoryItem.product_id == product.id
                ).first()

                stock_level = inventory.quantity_on_hand if inventory else 0

                return {
                    "success": True,
                    "actions_taken": [f"Retrieved stock for {product.name}"],
                    "data": {
                        "product": product.name,
                        "stock": stock_level,
                        "price": float(product.price)
                    },
                    "message": f"{product.name}: {stock_level} units in stock"
                }

        # General stock inquiry
        low_stock_items = db.query(InventoryItem, Product).join(Product).filter(
            InventoryItem.business_id == business_id,
            Product.low_stock_threshold.isnot(None),
            InventoryItem.quantity_on_hand <= Product.low_stock_threshold
        ).limit(5).all()

        return {
            "success": True,
            "actions_taken": ["Retrieved low stock items"],
            "data": {
                "low_stock_count": len(low_stock_items),
                "items": [
                    {
                        "product": item.Product.name,
                        "current_stock": item.InventoryItem.quantity_on_hand,
                        "low_stock_threshold": item.Product.low_stock_threshold
                    }
                    for item in low_stock_items
                ]
            },
            "message": f"{len(low_stock_items)} items need restocking"
        }

    async def _handle_sales_inquiry(
        self,
        db: Session,
        business_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle sales inquiries"""

        today = date.today()

        # Today's sales
        daily_analytics = db.query(DailyAnalytics).filter(
            DailyAnalytics.business_id == business_id,
            DailyAnalytics.date == today
        ).first()

        # Extract values and ensure proper types
        if daily_analytics:
            today_sales = float(
                getattr(daily_analytics, 'total_sales', 0.0) or 0.0)
            today_transactions = getattr(
                daily_analytics, 'transaction_count', 0) or 0
        else:
            today_sales = 0.0
            today_transactions = 0

        return {
            "success": True,
            "actions_taken": ["Retrieved sales data"],
            "data": {
                "today_sales": today_sales,
                "today_transactions": today_transactions,
                "date": today.isoformat()
            },
            "message": f"Today's sales: ₹{today_sales} from {today_transactions} transactions"
        }

    async def _handle_customer_inquiry(
        self,
        db: Session,
        business_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle customer inquiries"""

        customer_count = db.query(Customer).filter(
            Customer.business_id == business_id
        ).count()

        # Top customers by balance (who owe money)
        top_debtors = db.query(Customer).filter(
            Customer.business_id == business_id,
            Customer.credit > 0
        ).order_by(Customer.credit.desc()).limit(5).all()

        return {
            "success": True,
            "actions_taken": ["Retrieved customer data"],
            "data": {
                "total_customers": customer_count,
                "top_debtors": [
                    {
                        "name": customer.name,
                        "balance": float(customer.credit),
                        "phone": customer.phone
                    }
                    for customer in top_debtors
                ]
            },
            "message": f"Total customers: {customer_count}, {len(top_debtors)} have pending dues"
        }

    async def _handle_balance_inquiry(
        self,
        db: Session,
        business_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle balance inquiries"""

        # Calculate total receivables (money owed to business)
        total_receivables = db.query(
            func.sum(Customer.credit)
        ).filter(
            Customer.business_id == business_id,
            Customer.credit > 0
        ).scalar() or Decimal('0')

        # Calculate total payables (money business owes)
        total_payables = abs(db.query(
            func.sum(Customer.credit)
        ).filter(
            Customer.business_id == business_id,
            Customer.credit < 0
        ).scalar() or Decimal('0'))

        net_balance = total_receivables - total_payables

        return {
            "success": True,
            "actions_taken": ["Retrieved balance data"],
            "data": {
                "total_receivables": float(total_receivables),
                "total_payables": float(total_payables),
                "net_balance": float(net_balance)
            },
            "message": f"Receivables: ₹{total_receivables}, Payables: ₹{total_payables}, Net: ₹{net_balance}"
        }

    async def _generate_dynamic_query(
        self,
        db: Session,
        business_id: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate and execute dynamic SQL query using GPT-4 mini for unhandled intents"""

        try:
            # Create system prompt for SQL generation
            system_prompt = """You are a SQL expert for business intelligence queries. Generate ONLY SELECT queries that are safe and parameterized.

RULES:
- Generate ONLY SELECT statements (no INSERT, UPDATE, DELETE, DROP, CREATE, ALTER)  
- ALL queries MUST include WHERE business_id = :business_id
- Use proper parameterized queries with :param_name format
- Focus on business insights and analytics
- Limit results to maximum 100 rows
- Return ONLY valid JSON in exact format:

{
  "sql": "SELECT ... FROM ... WHERE business_id = :business_id AND ...",
  "parameters": {"business_id": "value", "param1": "value"},
  "description": "Business purpose of this query",
  "expected_insight": "What business insight this provides"
}"""

            # Create user prompt with context
            user_prompt = f"""Generate a SQL query for this business intelligence request:

INTENT: {intent}
ENTITIES: {entities}
BUSINESS_ID: {business_id}

DATABASE SCHEMA:
{self._format_schema_for_query()}

The query should provide actionable business insights related to the intent and entities provided.
Focus on practical business questions that help decision making.

Generate the SQL query now:"""

            # Call GPT-4 mini for SQL generation
            llm_response = await self.llm_service.call_full_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800
            )

            if not llm_response:
                return self._create_fallback_query_result(intent, "LLM call failed")

            # Extract SQL and parameters
            sql = llm_response.get("sql", "").strip()
            parameters = llm_response.get("parameters", {})
            description = llm_response.get(
                "description", f"Dynamic query for {intent}")
            expected_insight = llm_response.get(
                "expected_insight", "Business insights")

            # Validate SQL safety
            if not self._is_safe_sql(sql):
                return self._create_fallback_query_result(intent, "Unsafe SQL generated")

            # Ensure business_id parameter is set
            parameters["business_id"] = int(business_id)

            # Add entity-based parameters
            for key, value in entities.items():
                if key not in parameters and value is not None:
                    # Convert entity values to appropriate types
                    if isinstance(value, str) and value.isdigit():
                        parameters[key] = int(value)
                    elif isinstance(value, str):
                        parameters[key] = f"%{value}%"  # For LIKE queries
                    else:
                        parameters[key] = value

            # Execute the generated query
            query_results = await self._execute_dynamic_sql(db, sql, parameters)

            if query_results["success"]:
                # Format results for business insights
                formatted_results = self._format_query_results(
                    query_results["data"])

                return {
                    "success": True,
                    "actions_taken": [f"Generated and executed dynamic query for {intent}", description],
                    "data": {
                        "query_type": intent,
                        "results": formatted_results,
                        "row_count": len(query_results["data"]),
                        "insight": expected_insight
                    },
                    "message": f"Query completed: {expected_insight}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Query execution failed: {query_results['error']}",
                    "actions_taken": [f"Attempted dynamic query for {intent}"],
                    "data": None,
                    "message": f"Failed to execute query for {intent}"
                }

        except Exception as e:
            logger.error(
                f"Dynamic query generation failed for {intent}: {str(e)}")
            return self._create_fallback_query_result(intent, str(e))

    def _format_schema_for_query(self) -> str:
        """Format database schema for LLM query generation"""
        schema_lines = []
        for table_name, table_info in self.database_schema.items():
            columns_with_types = [
                f"{col} ({table_info['types'][col]})"
                for col in table_info['columns']
            ]
            schema_lines.append(
                f"{table_name}: {', '.join(columns_with_types)}\n  Purpose: {table_info['description']}"
            )
        return "\n\n".join(schema_lines)

    def _is_safe_sql(self, sql: str) -> bool:
        """Validate that SQL is safe (SELECT only)"""
        if not sql:
            return False

        sql_upper = sql.upper().strip()

        # Must start with SELECT
        if not sql_upper.startswith("SELECT"):
            return False

        # Must not contain dangerous operations
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
            "TRUNCATE", "EXEC", "EXECUTE", "MERGE", "CALL"
        ]

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False

        # Must include business_id filter
        if "business_id" not in sql.lower():
            return False

        return True

    async def _execute_dynamic_sql(
        self,
        db: Session,
        sql: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute dynamic SQL with proper error handling"""

        try:
            # Execute query with parameters
            result = db.execute(text(sql), parameters)

            # Fetch results with limit
            rows = result.fetchmany(100)  # Limit for safety

            if rows:
                columns = [col for col in result.keys()]
                data = [dict(zip(columns, row)) for row in rows]

                # Clean data (handle None values, format numbers)
                cleaned_data = []
                for row_data in data:
                    cleaned_row = {}
                    for key, value in row_data.items():
                        if value is None:
                            cleaned_row[key] = None
                        elif hasattr(value, 'isoformat'):  # datetime
                            cleaned_row[key] = value.isoformat()
                        elif isinstance(value, (float, int)):
                            cleaned_row[key] = round(value, 2) if isinstance(
                                value, float) else value
                        else:
                            cleaned_row[key] = str(value)
                    cleaned_data.append(cleaned_row)
            else:
                cleaned_data = []
                columns = []

            return {
                "success": True,
                "data": cleaned_data,
                "columns": columns,
                "row_count": len(cleaned_data)
            }

        except Exception as e:
            logger.error(f"Dynamic SQL execution error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "columns": [],
                "row_count": 0
            }

    def _format_query_results(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format query results for business presentation"""

        if not data:
            return []

        # Take top 10 results for presentation
        formatted_results = []
        for row in data[:10]:
            formatted_row = {}
            for key, value in row.items():
                # Make keys more readable
                readable_key = key.replace('_', ' ').title()
                formatted_row[readable_key] = value
            formatted_results.append(formatted_row)

        return formatted_results

    def _create_fallback_query_result(self, intent: str, error_msg: str) -> Dict[str, Any]:
        """Create fallback result when dynamic query fails"""

        return {
            "success": False,
            "error": f"Dynamic query generation failed: {error_msg}",
            "actions_taken": [f"Attempted to generate query for {intent}"],
            "data": {
                "query_type": intent,
                "fallback_used": True,
                "error_reason": error_msg
            },
            "message": f"Unable to process {intent} - {error_msg}"
        }


# Singleton instance
execution_engine = ExecutionEngine()
