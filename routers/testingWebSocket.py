from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from auth.authentication import get_current_user_ws
from typing import Dict
import json
from Database.orders import save_order_from_ws

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.dashboards: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.dashboards:
            del self.dashboards[user_id]

    def register_dashboard(self, user_id: str):
        if user_id in self.active_connections:
            self.dashboards[user_id] = self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

    async def broadcast_to_dashboards(self, message: dict):
        for conn in self.dashboards.values():
            await conn.send_text(json.dumps(message))

manager = ConnectionManager()

@router.websocket("/ws/orders")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    
    if not token:
        user_id = f"dashboard_{id(websocket)}"
        await manager.connect(websocket, user_id)
    else:
        try:
            user_id = await get_current_user_ws(websocket, token)
            await manager.connect(websocket, user_id)
        except:
            await websocket.close(code=1008)
            return

    try:
        while True:
            data_raw = await websocket.receive_text()
            try:
                data = json.loads(data_raw)
            except:
                continue

            if data.get("event") == "identify" and data.get("type") == "dashboard":
                manager.register_dashboard(user_id)

            elif data.get("event") == "new_order":
                pedido = data.get("pedido", {})
                await manager.send_personal_message({
                    "event": "status_update",
                    "status": "confirmado",
                    "pedido": pedido
                }, user_id)
                mensaje_dashboard = {
                    "event": "new_order",
                    "pedido": pedido,
                    "user_id": user_id
                }
                await manager.broadcast_to_dashboards(mensaje_dashboard)

            elif data.get("event") == "change_status":
                new_status = data.get("status", "")
                target = data.get("to", "")
                pedido_data = data.get("pedido", {})

                await manager.send_personal_message({
                    "event": "status_update",
                    "status": new_status,
                    "pedido": pedido_data
                }, target)

                if new_status == "entregado":
                    try:
                        pedido_data["status"] = new_status
                        pedido_data["user_client"] = target
                        save_order_from_ws(pedido_data)
                    except Exception as e:
                        print(f"❌ Error al guardar pedido en DB: {e}")

    except WebSocketDisconnect:
        manager.disconnect(user_id)