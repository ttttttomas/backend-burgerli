import uuid
from Database.getConnection import getConnection

from models.order import (
    Order, OrderBurger, OrderDrinks, OrderFries,
    OrderExtra, OrderSin, OrderCoupons, OrderUserClient
)


def save_order_from_ws(pedido: dict):
    db = getConnection()
    if not db:
        print("❌ No se pudo conectar a la base de datos.")
        return

    try:
        order_id = str(uuid.uuid4())

        # 1. Crear la orden base
        new_order = Order(
            id_order=order_id,
            user_client=pedido.get("user_client"),
            combo=pedido.get("combo"),
            payment_method=pedido.get("payment_method"),
            delivery_mode=pedido.get("delivery_mode"),
            price=pedido.get("price"),
            status=pedido.get("status", "entregado"),
            coupon=None,  # si tenés cupones individuales abajo
            order_notes=pedido.get("order_notes"),
            local=pedido.get("local"),
        )
        db.add(new_order)

        # 2. Guardar los productos relacionados

        for burger_id in pedido.get("burgers", []):
            db.add(OrderBurger(
                id_order_burger=str(uuid.uuid4()),
                id_order=order_id,
                id_burger=burger_id
            ))

        for drink_id in pedido.get("drinks", []):
            db.add(OrderDrinks(
                id_order_drinks=str(uuid.uuid4()),
                id_order=order_id,
                id_drinks=drink_id
            ))

        for fries_id in pedido.get("fries", []):
            db.add(OrderFries(
                id_order_fries=str(uuid.uuid4()),
                id_order=order_id,
                id_fries=fries_id
            ))

        for extra_id in pedido.get("extras", []):
            db.add(OrderExtra(
                id_order_extra=str(uuid.uuid4()),
                id_order=order_id,
                id_extra=extra_id
            ))

        for sin_id in pedido.get("sins", []):
            db.add(OrderSin(
                id_order_sin=str(uuid.uuid4()),
                id_order=order_id,
                id_sin=sin_id
            ))

        for coupon_id in pedido.get("coupons", []):
            db.add(OrderCoupons(
                id_order_coupons=str(uuid.uuid4()),
                id_order=order_id,
                id_coupons=coupon_id
            ))

        # 3. Relación con el cliente
        db.add(OrderUserClient(
            id_order_user_client=str(uuid.uuid4()),
            id_order=order_id,
            id_user_client=pedido.get("user_client")
        ))

        # 4. Commit final
        db.commit()
        print(f"✅ Pedido {order_id} guardado correctamente.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error al guardar el pedido: {e}")

    finally:
        db.close()