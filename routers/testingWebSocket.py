# testingWebsocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json

# Importá tu verificador WS y la excepción custom
# (ver auth/authentication.py tal como te pasé: get_current_user_ws(token) + WSAuthError)
from auth.authentication import get_current_user_ws, WSAuthError

# Opcional: si guardás pedidos desde el WS
from Database.orders import save_order_from_ws

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # conexiones activas por user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # dashboards registrados (subset de active_connections)
        self.dashboards: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"[WS] conectado: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            try:
                del self.active_connections[user_id]
            except Exception:
                pass
        if user_id in self.dashboards:
            try:
                del self.dashboards[user_id]
            except Exception:
                pass
        print(f"[WS] desconectado: {user_id}")

    def register_dashboard(self, user_id: str):
        # registra como dashboard la conexión existente
        if user_id in self.active_connections:
            self.dashboards[user_id] = self.active_connections[user_id]
            print(f"[WS] dashboard registrado: {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        conn = self.active_connections.get(user_id)
        if conn:
            try:
                await conn.send_text(json.dumps(message))
            except Exception as e:
                print(f"[WS] error al enviar a {user_id}: {e}")

    async def broadcast_to_dashboards(self, message: dict):
        # se hace copia de valores por si cambian durante iteración
        for uid, conn in list(self.dashboards.items()):
            try:
                await conn.send_text(json.dumps(message))
            except Exception as e:
                print(f"[WS] error broadcast dashboard {uid}: {e}")


manager = ConnectionManager()


@router.websocket("/ws/orders")
async def websocket_endpoint(websocket: WebSocket):
    """
    Conexiones:
      - Dashboard sin token: ?token ausente -> user_id = dashboard_<id(socket)>
      - Cliente autenticado: ?token=<JWT> -> user_id = el del token
    Mensajes esperados:
      - {"event":"identify","type":"dashboard"}
      - {"event":"new_order","pedido":{...}}
      - {"event":"change_status","status":"...","to":"<user_id>","pedido":{...}}
    """
    token = websocket.query_params.get("token")

    # Autenticación/identidad durante el handshake
    try:
        if not token:
            # Permitís dashboards sin auth (anónimo controlado)
            user_id = f"dashboard_{id(websocket)}"
            await manager.connect(websocket, user_id)
        else:
            user_id = await get_current_user_ws(token)  # puede lanzar WSAuthError
            await manager.connect(websocket, user_id)
    except WSAuthError as e:
        # Cerrá explícitamente con el código que trae la excepción (1008 por defecto)
        try:
            await websocket.close(code=e.code)
        except Exception:
            pass
        print(f"[WS AUTH] rechazo handshake: {e.reason if hasattr(e, 'reason') else 'auth error'}")
        return
    except Exception as e:
        print(f"[WS AUTH ERROR] {e}")
        try:
            await websocket.close(code=1008)
        except Exception:
            pass
        return

    # Loop de mensajes
    try:
        while True:
            data_raw = await websocket.receive_text()

            # Parseo robusto
            try:
                data = json.loads(data_raw)
            except Exception:
                # mensaje no-JSON -> ignorar silenciosamente
                continue

            event = data.get("event")

            # 1) Identificar dashboards (para recibir broadcasts)
            if event == "identify" and data.get("type") == "dashboard":
                manager.register_dashboard(user_id)

            # 2) Nuevo pedido de un cliente
            elif event == "new_order":
                pedido = data.get("pedido", {}) or {}

                # Confirmación al cliente (mismo user_id)
                await manager.send_personal_message(
                    {
                        "event": "status_update",
                        "status": "confirmado",
                        "pedido": pedido,
                    },
                    user_id,
                )

                # Broadcast a todos los dashboards
                mensaje_dashboard = {
                    "event": "new_order",
                    "pedido": pedido,
                    "user_id": user_id,
                }
                await manager.broadcast_to_dashboards(mensaje_dashboard)

            # 3) Cambio de estado desde dashboard hacia un cliente
            elif event == "change_status":
                new_status = data.get("status", "")
                target = data.get("to", "")
                pedido_data = data.get("pedido", {}) or {}

                # Aviso al cliente objetivo
                await manager.send_personal_message(
                    {
                        "event": "status_update",
                        "status": new_status,
                        "pedido": pedido_data,
                    },
                    target,
                )

                # Si se entregó, persistimos (opcional)
                if new_status == "entregado":
                    try:
                        pedido_data["status"] = new_status
                        # guardamos el user_id del cliente en el pedido
                        pedido_data["user_client"] = target
                        save_order_from_ws(pedido_data)
                    except Exception as e:
                        print(f"❌ Error al guardar pedido en DB: {e}")

            # (Opcional) Podés agregar eventos ping/pong custom si querés mantener viva la conexión
            # elif event == "ping":
            #     await manager.send_personal_message({"event": "pong"}, user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"[WS LOOP ERROR] {e}")
        manager.disconnect(user_id)
        try:
            await websocket.close(code=1011)  # error interno
        except Exception:
            pass