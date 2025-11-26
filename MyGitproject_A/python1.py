from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict

app = FastAPI()

# --- 1. The Connection Manager ---
class ConnectionManager:
    def __init__(self):
       
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_name: str):
        
        await websocket.accept()
        
        
        if room_name not in self.active_connections:
            self.active_connections[room_name] = []
            
       
        self.active_connections[room_name].append(websocket)
        print(f"Client joined room: {room_name}")

    def disconnect(self, websocket: WebSocket, room_name: str):
        
        if room_name in self.active_connections:
            self.active_connections[room_name].remove(websocket)
           
            if not self.active_connections[room_name]:
                del self.active_connections[room_name]
        print(f"Client left room: {room_name}")

    async def broadcast_to_room(self, message: str, room_name: str):
        
        if room_name in self.active_connections:
            for connection in self.active_connections[room_name]:
                await connection.send_text(message)


manager = ConnectionManager()

#The WebSocket Endpoint ---
@app.websocket("/ws/{room_name}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, client_id: int):
    
    await manager.connect(websocket, room_name)
    
    try:
        
        await manager.broadcast_to_room(f"Client #{client_id} has joined the chat", room_name)
        
        # Keep the connection open and listen for messages
        while True:
            data = await websocket.receive_text()
            # Send message only to users in the same room
            await manager.broadcast_to_room(f"Client #{client_id}: {data}", room_name)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_name)
        await manager.broadcast_to_room(f"Client #{client_id} left the chat", room_name)