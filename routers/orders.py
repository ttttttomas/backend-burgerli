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
import time

router = APIRouter()

IMAGES_DIR = "images/"
DOMAIN_URL = "https://api-burgerli.iwebtecnology.com/api/images"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")

@router.post("/createOrder", tags=["Orders"])
async def create_order(order: OrderMan):
    try:
        id_order = order.id_order
        payment_method = order.payment_method
        delivery_mode = order.delivery_mode
        price = order.price
        status = order.status
        local = order.local
        order_notes = order.order_notes
        name = order.name
        phone = order.phone
        email = order.email
        address = order.address
        coupon = order.coupon
        products = order.products

        normalized_products = []
        for product in products:
            if isinstance(product, str) and "," in product:
                normalized_products.extend([p.strip() for p in product.split(",") if p.strip()])
            elif product:
                normalized_products.append(product.strip())
        
        # Use transaction context with begin()
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
            return order
    except OperationalError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")