from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

#  data model
class NotificationSchema(BaseModel):
    message:str
    target_room:str

# The Connection Manager ---
class ConnectionManager:
    def __init__(self):
       
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_name: str):
        
        await websocket.accept()
        
        
        if room_name not in self.active_connections:
            self.active_connections[room_name] = []

        self.active_connections[room_name].append(websocket)
        print(f"Client joined room: {room_name}")

    async def broadcast_to_room(self, message: str, room_name: str):
        
        if room_name in self.active_connections:
            for connection in self.active_connections[room_name]:
                await connection.send_text(message)


manager = ConnectionManager()

#The WebSocket Endpoint ---
@app.websocket("/ws/{room_name}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, client_id: int):
    
    await manager.connect(websocket, room_name)
    
    try:
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_name)