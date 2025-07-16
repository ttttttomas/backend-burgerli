from sqlalchemy import text
from Database.getConnection import getConnection
import uuid
import json

def save_order_from_ws(order: dict) -> bool:
    db = getConnection()
    if db is None:
        return False

    try:
        id_order = str(uuid.uuid4())

        required_fields = ["user_client", "status", "price"]
        if not all(order.get(field) for field in required_fields):
            print("❌ Faltan campos obligatorios en el pedido")
            return False

        query = text("""
            INSERT INTO orders (
                id_order, combo, user_client, payment_method, delivery_mode,
                price, status, coupon, order_notes, local, burgers,
                fries, drinks, sin, extra
            ) VALUES (
                :id_order, :combo, :user_client, :payment_method, :delivery_mode,
                :price, :status, :coupon, :order_notes, :local, :burgers,
                :fries, :drinks, :sin, :extra
            )
        """)

        db.execute(query, {
            "id_order": id_order,
            "combo": order.get("combo", ""),
            "user_client": order.get("user_client"),
            "payment_method": order.get("payment_method", ""),
            "delivery_mode": order.get("delivery_mode", ""),
            "price": order.get("price"),
            "status": order.get("status"),
            "coupon": order.get("coupon", ""),
            "order_notes": order.get("order_notes", ""),
            "local": order.get("local", ""),
            "burgers": json.dumps(order.get("burgers", [])),
            "fries": json.dumps(order.get("fries", [])),
            "drinks": json.dumps(order.get("drinks", [])),
            "sin": json.dumps(order.get("sin", [])),
            "extra": json.dumps(order.get("extra", [])),
        })
        db.commit()
        return True
    except Exception as e:
        print(f"❌ Error al guardar pedido: {e}")
        db.rollback()
        return False
    finally:
        db.close()