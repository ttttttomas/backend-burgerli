from email import message
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
from routers.testingWebSocket import manager

router = APIRouter()

IMAGES_DIR = "images/"
DOMAIN_URL = "https://api-burgerli.iwebtecnology.com/api/images"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")

class ChangeLocalBody(BaseModel):
    local: str

@router.post("/createOrder", tags=["Orders"])
async def create_order(order: OrderMan):
    try:
        id_order = str(uuid.uuid4())
        # Validar que id_user_client sea un UUID válido
        user_client_id = None
        if order.id_user_client:
            try:
                uuid.UUID(order.id_user_client)
                user_client_id = order.id_user_client
            except (ValueError, AttributeError):
                user_client_id = None
        
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
                INSERT INTO orders (id_order, id_user_client, payment_method, delivery_mode, price, status, order_notes, local, name, phone, email, address)
                VALUES (:id_order, :id_user_client, :payment_method, :delivery_mode, :price, :status, :order_notes, :local, :name, :phone, :email, :address)
            """), {
                "id_order": id_order,
                "id_user_client": user_client_id,
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
            
            # Coupon is already stored in the orders table's coupon column

            # ACA VA WEBSOCKET
                # 2️⃣ Notificar a dashboards
            message_dashboard = {
                "event": "new_order",
                "pedido": {
                    "id_order": id_order,
                    "user_client_id": user_client_id,
                    "payment_method": payment_method,
                    "delivery_mode": delivery_mode,
                    "price": price,
                    "status": status, 
                    "order_notes": order_notes,
                    "local": local,
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    'products': products
                },
                'order_id': id_order
            }
            await manager.broadcast_to_dashboards(message_dashboard)
            
            # Transaction will auto-commit here
            return {"message": "Order created successfully", "order_id": id_order}
        
    except OperationalError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
    
@router.patch("/{order_id}/local")
async def change_order_local(order_id: str, body: ChangeLocalBody):
    try:
        print(f"[PATCH /orders/{{order_id}}/local] INICIANDO - order_id={order_id}, nuevo_local={body.local}")
        with engine.begin() as conn:
            # Buscar la orden
            result = conn.execute(
                text("SELECT * FROM orders WHERE id_order = :order_id"),
                {"order_id": order_id}
            )

            order = result.mappings().first()

            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            old_local = order["local"]

            # Buscar los productos de esa orden
            prod_result = conn.execute(
                text("""
                    SELECT products 
                    FROM order_products 
                    WHERE order_id = :order_id
                """),
                {"order_id": order_id}
            )

            product_list = [
                prod_row["products"]
                for prod_row in prod_result.mappings().all()
            ]

            # Actualizar local
            conn.execute(
                text("""
                    UPDATE orders 
                    SET local = :local 
                    WHERE id_order = :id_order
                """),
                {
                    "local": body.local,
                    "id_order": order_id
                }
            )

            # Convertir orden a dict
            order_dict = dict(order)

            pedido_dict = {
                "id_order": order_dict.get("id_order"),
                "local": body.local,
                "status": order_dict.get("status"),
                "name": order_dict.get("name"),
                "email": order_dict.get("email"),
                "phone": order_dict.get("phone"),
                "address": order_dict.get("address"),
                "payment_method": order_dict.get("payment_method"),
                "delivery_mode": order_dict.get("delivery_mode"),
                "delivery_time": order_dict.get("delivery_time"),
                "price": order_dict.get("price"),
                "order_notes": order_dict.get("order_notes"),
                "coupon": order_dict.get("coupon"),
                "coupon_amount": order_dict.get("coupon_amount"),
                "products": order_dict.get("product_list"),
                "created_at": (
                    order_dict.get("created_at").isoformat()
                    if order_dict.get("created_at")
                    else None
                ),
            }

            payload = {
               "event": "order_transferred",
                "id_order": order_id,
                "order_id": order_id,
                "old_local": old_local,
                "new_local": body.local,
                "from": old_local,
                "to": body.local,
                "pedido": pedido_dict
                }

            print(f"[PATCH] payload armado: event={payload['event']}, from={old_local}, to={body.local}")
            print(f"[PATCH] Dashboards conectados: {len(manager.dashboard_connections)}")
            print(f"[PATCH] Llamando broadcast_to_dashboards...")
            
            # Avisar a TODOS los DASHBOARDS (igual que new_order)
            await manager.broadcast_to_dashboards(payload)
            
            print(f"[PATCH] broadcast_to_dashboards COMPLETADO")


        return {
            "success": True,
            "old_local": old_local,
            "new_local": body.local,
            "pedido": pedido_dict,
        }

    except OperationalError as e:
        print(f"[PATCH] Database error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(e)}"
        )
    except Exception as e:
        print(f"[PATCH] Error general: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
    
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
            # si StatusUpdate usa Enum, .value te deja el string
            new_status: str = body.status.value

            # 2) Validar transición
            if old_status not in VALID_TRANSITIONS:
                # si no está en el dict, dejás pasar (como ya tenías)
                pass
            else:
                if (
                    new_status not in VALID_TRANSITIONS[old_status]
                    and new_status != old_status
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=f"Invalid transition: {old_status} -> {new_status}",
                    )

            # 3) Si no cambió nada, devolvés y NO emitís eventos
            if new_status == old_status:
                return {
                    "message": "Order status unchanged",
                    "id_order": id_order,
                    "old_status": old_status,
                    "new_status": new_status,
                }

            # 4) Actualizar en la DB
            result = conn.execute(
                text(
                    """
                    UPDATE orders
                    SET status = :status
                    WHERE id_order = :id_order
                    """
                ),
                {"status": new_status, "id_order": id_order},
            )

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")

        # 5) Armar payload común para WS
        payload = {
            "event": "status_update",
            "id_order": id_order,
            "old_status": old_status,
            "new_status": new_status,
        }

        # 6) Avisar a la TIENDA (solo esa orden)
        await manager.broadcast_order(id_order, payload)

        # 7) Avisar a TODOS los DASHBOARDS
        await manager.broadcast_to_dashboards(payload)

        print(f"[PATCH /orders/{id_order}/status] status updated successfully")
        print(f"payload: {payload}")
        # 8) Respuesta HTTP
        return {
            "message": "Order status updated successfully",
            **payload,
        }
    except HTTPException:
        # re-lanzo las HTTPException tal cual
        raise
    except Exception as e:
        print(f"[PATCH /orders/{id_order}/status] error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    
@router.delete("/deleteOrder/{id_order}", tags=["Orders"])
async def delete_order(id_order: str):
    try:
        with engine.begin() as conn:
            # 1) Eliminar dependencias
            conn.execute(
                text("DELETE FROM order_products WHERE order_id = :order_id"),
                {"order_id": id_order},
            )

            # 2) Eliminar la orden
            result = conn.execute(
                text("DELETE FROM orders WHERE id_order = :id_order"),
                {"id_order": id_order},
            )

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")

        # 3) Payload WS (igual que PATCH pero con otro event)
        payload = {
            "event": "order_deleted",
            "id_order": id_order,
        }

        # DEBUG: ver si el manager tiene conexiones
        print("[DELETE] manager id:", id(manager))
        print("[DELETE] order_connections keys:", list(manager.order_connections.keys()))
        print("[DELETE] dashboards activos:", len(manager.dashboard_connections))

        # 4) Avisar a la TIENDA (tracking de esa orden)
        await manager.broadcast_order(id_order, payload)

        # 5) Avisar a TODOS los DASHBOARDS
        await manager.broadcast_to_dashboards(payload)

        # 6) Respuesta HTTP
        return {
            "message": "Order deleted successfully",
            **payload,
        }

    except OperationalError as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(e)}",
        )
    except Exception as e:
        print(f"[DELETE /deleteOrder/{id_order}] error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error" + str(e))
