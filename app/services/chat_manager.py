from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict


class ConnectionManager:
    def __init__(self):
        self.user_connections: Dict[int, WebSocket] = {}
        self.admin_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int, is_admin: bool):
        """
        Подключение пользователя или администратора.
        """
        await websocket.accept()
        if is_admin:
            self.admin_connections[user_id] = websocket
        else:
            self.user_connections[user_id] = websocket

    def disconnect(self, user_id: int, is_admin: bool):
        """
        Отключение пользователя или администратора.
        """
        if is_admin:
            self.admin_connections.pop(user_id, None)
        else:
            self.user_connections.pop(user_id, None)

    async def send_to_admin(self, user_id: int, message: str):
        """
        Отправить сообщение от пользователя администратору.
        """
        for admin_id, admin_ws in self.admin_connections.items():
            try:
                await admin_ws.send_json({"from_user": user_id, "message": message})
            except WebSocketDisconnect:
                self.disconnect(admin_id, is_admin=True)

    async def send_to_user(self, user_id: int, message: str):
        """
        Отправить сообщение от администратора пользователю.
        """
        user_ws = self.user_connections.get(user_id)
        if user_ws:
            try:
                await user_ws.send_json({"from_admin": True, "message": message})
            except WebSocketDisconnect:
                self.disconnect(user_id, is_admin=False)


chat_manager = ConnectionManager()
