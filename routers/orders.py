from typing import List, Optional
from fastapi import APIRouter, HTTPException, Form, Body, UploadFile, File
import os
import shutil
from sqlalchemy import text
from Database.getConnection import engine
import uuid
from models.order import OrderMan
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from enum import Enum
from pydantic import BaseModel
import time

router = APIRouter()

IMAGES_DIR = "images/"
DOMAIN_URL = "https://api-burgerli.iwebtecnology.com/api/images"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")

@router.post("/createOrder", tags=["Orders"])
async def create_order(order: OrderMan):
    try:
        id_order = str(uuid.uuid4())
        payment_method = order.payment_method
        delivery_mode = order.delivery_mode
        price = order.price
        status = "confirmed"
        local = order.local
        order_notes = order.order_notes
        name = order.name
        phone = order.phone
        email = order.email
        address = order.address
        coupon = order.coupon
        products = order.products or []


        normalized_products = []
        for product in products:
            if isinstance(product, str) and "," in product:
                normalized_products.extend([p.strip() for p in product.split(",") if p.strip()])
            elif product:
                normalized_products.append(product.strip())

        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO orders (id_order, payment_method, delivery_mode, price, status, order_notes, local, name, phone, email, address)
                VALUES (:id_order, :payment_method, :delivery_mode, :price, :status, :order_notes, :local, :name, :phone, :email, :address)
            """), {
                "id_order": id_order,
                "payment_method": payment_method,
                "delivery_mode": delivery_mode,
                "price": price,
                "status": status, 
                "order_notes": order_notes,
                "local": local,
                "name": name,
                "phone": phone,
                "email": email,
                "address": address
            })

            # Products insertion
            for product_id in normalized_products:
                id_order_products = str(uuid.uuid4())
                conn.execute(text("""
                    INSERT INTO order_products (id, products, order_id) VALUES (:id, :products, :order_id)
                """), {
                    "id": id_order_products,
                    "products": product_id,
                    "order_id": id_order
                })
            
            # Coupon insertion 
            if coupon:
                id_order_coupons = str(uuid.uuid4())
                conn.execute(text("""
                    INSERT INTO order_coupons (id_order_coupons, id_order, name) VALUES (:id_order_coupons, :id_order, :name)
                """), {
                    "id_order_coupons": id_order_coupons,
                    "id_order": id_order,
                    "name": coupon
                })

            # ACA VA WEBSOCKET
            
            
            # Transaction will auto-commit here
            return {"message": "Order created successfully", "order_id": id_order}
        
    except OperationalError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
    
@router.get("/getOrders", tags=["Orders"])
async def get_orders():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM orders"))

            products = []
            for row in result.mappings().all():
                order_id = row['id_order']
                prod_result = conn.execute(text("SELECT products FROM order_products WHERE order_id = :order_id"), {"order_id": order_id})
                product_list = [prod_row['products'] for prod_row in prod_result.mappings().all()]
                row = dict(row)
                row['products'] = product_list
                products.append(row)

            return products
        
    except OperationalError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
    
@router.get("/getOrderById/{id_order}", tags=["Orders"])
async def get_order_by_id(id_order: str):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM orders WHERE id_order = :id_order"), {"id_order": id_order})
            order = result.mappings().first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            prod_result = conn.execute(text("SELECT products FROM order_products WHERE order_id = :order_id"), {"order_id": id_order})
            product_list = [prod_row['products'] for prod_row in prod_result.mappings().all()]

            order = dict(order)
            order['products'] = product_list
            return order
    except OperationalError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
    
@router.put("/updateOrderStatus/{id_order}", tags=["Orders"])
async def update_order_status_simple(id_order: str, status: str = Body(..., embed=True)):
    try:
        with engine.begin() as conn:
            result = conn.execute(text("UPDATE orders SET status = :status WHERE id_order = :id_order"), {
                "status": status,
                "id_order": id_order
            })
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")
            return {"message": "Order status updated successfully"}
    except OperationalError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
    
class OrderStatus(str, Enum):
    confirmed = "confirmed" 
    in_preparation = "in_preparation"
    on_the_way = "on_the_way"     
    delivered = "delivered"

VALID_TRANSITIONS = {
    "confirmed": {"in_preparation"},
    "in_preparation": {"on_the_way", "delivered"},
    "on_the_way": {"delivered"},
    "delivered": set(),
}

class StatusUpdate(BaseModel):
    status: OrderStatus

@router.patch("/{id_order}/status", tags=["Orders"])
async def update_order_status(
    id_order: str,
    body: StatusUpdate = Body(..., embed=False),
):
    try:
        with engine.begin() as conn:
            # 1) Traer estado actual
            row = conn.execute(
                text("SELECT status FROM orders WHERE id_order = :id_order"),
                {"id_order": id_order},
            ).mappings().first()

            if not row:
                raise HTTPException(status_code=404, detail="Order not found")

            old_status: str = row["status"]
            new_status: str = body.status.value

            if old_status not in VALID_TRANSITIONS:
                pass
            else:
                if new_status not in VALID_TRANSITIONS[old_status] and new_status != old_status:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Invalid transition: {old_status} -> {new_status}"
                    )

            if new_status == old_status:
                return {
                    "message": "Order status unchanged",
                    "id_order": id_order,
                    "old_status": old_status,
                    "new_status": new_status,
                }

            result = conn.execute(
                text("""
                    UPDATE orders
                    SET status = :status
                    WHERE id_order = :id_order
                """),
                {"status": new_status, "id_order": id_order},
            )

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")

            return {
                "message": "Order status updated successfully",
                "id_order": id_order,
                "old_status": old_status,
                "new_status": new_status,
            }

    except OperationalError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error")
    
@router.delete("/deleteOrder/{id_order}", tags=["Orders"])
async def delete_order(id_order: str):
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM order_products WHERE order_id = :order_id"), {"order_id": id_order})
            
            conn.execute(text("DELETE FROM order_coupons WHERE id_order = :id_order"), {"id_order": id_order})

            result = conn.execute(text("DELETE FROM orders WHERE id_order = :id_order"), {"id_order": id_order})
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")
            return {"message": "Order deleted successfully"}
    except OperationalError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")