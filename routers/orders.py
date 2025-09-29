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

@router.post("/createOrder", tags=["Orders Clients"])
async def create_order(Order: OrderMan):
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with engine.connect() as connection:
                # Test the database connection
                connection.execute(text("SELECT 1"))
                
                # Verify that all product IDs exist
                if Order.products:
                    for product_id in Order.products:
                        product_exists = connection.execute(
                            text("SELECT id_product FROM Products WHERE id_product = :product_id"),
                            {"product_id": product_id}
                        ).fetchone()
                        
                        if not product_exists:
                            raise HTTPException(
                                status_code=404,
                                detail=f"Product with id {product_id} does not exist"
                            )

                order_id = str(uuid.uuid4())
                
                # 1. Create Order
                connection.execute(
                    text("""
                         INSERT INTO orders (
                             id_order, payment_method, delivery_mode, price, status, 
                             order_notes, local, fries, drinks, name, email, phone, 
                             address, created_at
                         ) VALUES (
                             :id_order, :payment_method, :delivery_mode, :price, :status, 
                             :order_notes, :local, :fries, :drinks, :name, :email, :phone, 
                             :address, CURRENT_TIMESTAMP
                         )
                         """),
                    {
                        "id_order": order_id,
                        "payment_method": Order.payment_method,
                        "delivery_mode": Order.delivery_mode,
                        "price": Order.price,
                        "status": Order.status,
                        "order_notes": Order.order_notes,
                        "local": Order.local,
                        "fries": Order.fries,
                        "drinks": Order.drinks,
                        "name": Order.name,
                        "email": Order.email,
                        "phone": Order.phone,
                        "address": Order.address
                    }
                )
                connection.commit()

                # 2. Process coupons if they exist and are not empty
                if Order.coupon and any(Order.coupon):
                    for coupon_id in Order.coupon:
                        if coupon_id.strip():  # Check if coupon is not empty
                            connection.execute(
                                text("""
                                    INSERT INTO order_coupons (id_order_coupons, id_order, id_coupons)
                                    VALUES (:id_order_coupons, :id_order, :id_coupons)
                                """),
                                {
                                    "id_order_coupons": str(uuid.uuid4()),
                                    "id_order": order_id,
                                    "id_coupons": coupon_id
                                }
                            )
                    connection.commit()

                # 3. Process products if they exist
                if Order.products:
                    for product_id in Order.products:
                        try:
                            connection.execute(
                                text("""
                                    INSERT INTO order_products (id, order_id, product_id)
                                    VALUES (:id, :order_id, :product_id)
                                """),
                                {
                                    "id": str(uuid.uuid4()),
                                    "order_id": order_id,
                                    "product_id": product_id
                                }
                            )
                            connection.commit()
                        except Exception as e:
                            # Si hay error al insertar productos, eliminamos la orden
                            connection.execute(
                                text("DELETE FROM orders WHERE id_order = :order_id"),
                                {"order_id": order_id}
                            )
                            connection.commit()
                            raise HTTPException(
                                status_code=500,
                                detail=f"Error inserting product {product_id}: {str(e)}"
                            )

                return {"message": "Order created successfully", "order_id": order_id}

        except OperationalError as e:
            retry_count += 1
            if retry_count == max_retries:
                raise HTTPException(
                    status_code=500,
                    detail=f"Database connection error after {max_retries} retries: {str(e)}"
                )
            time.sleep(1)  # Wait 1 second before retrying
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=500, detail="Failed to create order after maximum retries")

@router.get("/getOrders", tags=["Orders Clients"], response_model=List[OrderMan])
async def get_orders():
    try:
        with engine.connect() as connection:
            select_query = text("""
                SELECT o.*, 
                       array_agg(c.id_coupons) as coupon
                FROM orders o
                LEFT JOIN order_coupons oc ON o.id_order = oc.id_order
                LEFT JOIN coupons c ON oc.id_coupons = c.id_coupons
                GROUP BY o.id_order
            """)
            result = connection.execute(select_query)
            orders = [OrderMan(**dict(row)) for row in result.fetchall()]
            return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/createProduct", tags=["Products"])
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    quantity: int = Form(...),
    fries: str = Form(...),
    sins: List[str] = Form(...), 
    image: UploadFile = File(...)
):
    try:
        # Save the uploaded image
        if not os.path.exists(IMAGES_DIR):
            os.makedirs(IMAGES_DIR)
        
        image_extension = os.path.splitext(image.filename)[1]
        image_filename = f"{uuid.uuid4()}{image_extension}"
        image_path = os.path.join(IMAGES_DIR, image_filename)
        
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        image_url = f"{DOMAIN_URL}/{image_filename}"
        
        with engine.connect() as connection:
            # Iniciar transacción
            trans = connection.begin()
            try:
                product_id = str(uuid.uuid4())

                # 1. Create the product
                connection.execute(
                    text("""
                        INSERT INTO Products (id_product, name, description, quantity, price, fries)
                        VALUES (:id_product, :name, :description, :quantity, :price, :fries)
                    """),
                    {
                        "id_product": product_id,
                        "name": name,
                        "description": description,
                        "quantity": quantity,
                        "price": price,
                        "fries": fries
                    }
                )

                # 2. Add the image
                connection.execute(
                    text("""
                        INSERT INTO product_image (id, product_id, url)
                        VALUES (:id, :product_id, :url)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "product_id": product_id,
                        "url": image_url
                    }
                )

                # 3. Process sins
                if sins:
                    for sin_name in sins:
                        # Check if sin exists, if not create it
                        sin_result = connection.execute(
                            text("SELECT id_sin FROM sin WHERE name = :name"),
                            {"name": sin_name}
                        ).fetchone()

                        if sin_result:
                            sin_id = sin_result[0]
                        else:
                            # Create new sin
                            sin_id = str(uuid.uuid4())
                            connection.execute(
                                text("INSERT INTO sin (id_sin, name) VALUES (:id_sin, :name)"),
                                {"id_sin": sin_id, "name": sin_name}
                            )

                        # Create product_sin relationship
                        connection.execute(
                            text("""
                                INSERT INTO products_sin (id, product_id, sin_id)
                                VALUES (:id, :product_id, :sin_id)
                            """),
                            {
                                "id": str(uuid.uuid4()),
                                "product_id": product_id,
                                "sin_id": sin_id
                            }
                        )
                
                # Commit all changes
                trans.commit()
                
                return {
                    "message": "Product created successfully",
                    "product_id": product_id,
                    "image_url": image_url,
                    "sins": sins
                }
            
            except Exception as e:
                # Rollback en caso de error
                trans.rollback()
                raise e
    
    except Exception as e:
        print(f"Error: {str(e)}")  # Para debugging
        if os.path.exists(image_path):  # Eliminar imagen si hubo error
            os.remove(image_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getProducts", tags=["Products"])
async def get_products():
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT * FROM Products"))
            rows = result.mappings().all()
            if not rows:
                raise HTTPException(status_code=404, detail="No products found.")
            products = []  # Change the name from prod to products
            for prod in rows:  # Now prod is just the loop variable
                hid = prod["id_product"]
                main = conn.execute(
                    text("SELECT url FROM product_image WHERE product_id = :id"),
                    {"id": hid}
                ).fetchone()

                sins_list = conn.execute(
                    text("""
                        SELECT s.id_sin, s.name 
                        FROM products_sin ps
                        JOIN sin s ON ps.sin_id = s.id_sin
                        WHERE ps.product_id = :id
                    """),
                    {"id": hid}
                ).mappings().all()

                data = dict(prod)
                data["main_image"] = main[0] if main else None
                data["sins_list"] = [dict(sin) for sin in sins_list]  # Convert each sin to dict
                products.append(data)
            return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/getProduct/{product_id}", tags=["Products"])
async def get_product(product_id: str):
    try:
        with engine.begin() as conn:
            prod = conn.execute(
                text("SELECT * FROM Products WHERE id_product = :id"),
                {"id": product_id}
            ).mappings().first()
            if not prod:
                raise HTTPException(status_code=404, detail="Product not found.")

            hid = prod["id_product"]
            main = conn.execute(
                text("SELECT url FROM product_image WHERE product_id = :id"),
                {"id": hid}
            ).fetchone()

            sins_list = conn.execute(
                text("""
                    SELECT s.id_sin, s.name 
                    FROM products_sin ps
                    JOIN sin s ON ps.sin_id = s.id_sin
                    WHERE ps.product_id = :id
                """),
                {"id": hid}
            ).mappings().all()

            data = dict(prod)
            data["main_image"] = main[0] if main else None
            data["sins_list"] = [dict(sin) for sin in sins_list]  # Convert each sin to dict
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))