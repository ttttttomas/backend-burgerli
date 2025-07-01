from sqlalchemy import text
from Database.getConnection import getConnection
import uuid

def save_order_from_ws(order: dict) -> bool:
    db = getConnection()
    if db is None:
        return False

    try:
        id_order = str(uuid.uuid4())
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
            "combo": order.get("combo"),
            "user_client": order.get("user_client"),
            "payment_method": order.get("payment_method"),
            "delivery_mode": order.get("delivery_mode"),
            "price": order.get("price"),
            "status": order.get("status"),
            "coupon": order.get("coupon"),
            "order_notes": order.get("order_notes"),
            "local": order.get("local"),
            "burgers": order.get("burgers"),
            "fries": order.get("fries"),
            "drinks": order.get("drinks"),
            "sin": order.get("sin"),
            "extra": order.get("extra"),
        })
        db.commit()
        return True
    except Exception as e:
        print(f"❌ Error al guardar pedido: {e}")
        db.rollback()
        return False
    finally:
        db.close()
