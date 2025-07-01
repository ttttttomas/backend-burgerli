from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from auth.authentication import get_current_user_ws
from typing import Dict
import json
from Database.orders import save_order_from_ws

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"🔌 Conectado {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"❌ Desconectado {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for conn in self.active_connections.values():
            await conn.send_text(json.dumps(message))


manager = ConnectionManager()

@router.websocket("/ws/orders")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        user_id = await get_current_user_ws(websocket, token)
    except:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user_id)

    try:
        while True:
            data_raw = await websocket.receive_text()
            try:
                data = json.loads(data_raw)
            except:
                print("❌ Error decodificando mensaje WebSocket")
                continue

            # Evento: nuevo pedido
            if data.get("event") == "new_order":
                pedido = data.get("pedido", {})
                print(f"📦 Pedido recibido de {user_id}: {pedido}")
                await manager.send_personal_message({
                    "event": "status_update",
                    "status": "confirmado",
                    "pedido": pedido
                }, user_id)

            # Evento: cambio de estado
            elif data.get("event") == "change_status":
                new_status = data.get("status", "")
                target = data.get("to", "")
                pedido_data = data.get("pedido", {})

                print(f"🔄 {user_id} cambió estado a {new_status} para {target}")
                await manager.send_personal_message({
                    "event": "status_update",
                    "status": new_status,
                    "pedido": pedido_data
                }, target)

                # Guardar si fue entregado
                if new_status == "entregado":
                    try:
                        pedido_data["status"] = new_status
                        pedido_data["user_client"] = target
                        ok = save_order_from_ws(pedido_data)
                        print(f"✅ Pedido guardado en DB: {ok}")
                    except Exception as e:
                        print(f"❌ Error al guardar pedido en DB: {e}")

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print("🔌 Desconectado WebSocket")
