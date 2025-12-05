import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

#  data model
class NotificationSchema(BaseModel):
    message:str
    room_name:str

# The Connection Manager ---
class ConnectionManager:
    def __init__(self):
       self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_name: str):
        
        await websocket.accept()
        if room_name not in self.active_connections:
            self.active_connections[room_name] = []
            #store in the user room 
        self.active_connections[room_name].append(websocket)
        print(f"user joined room : {room_name}")
    
    def disconnect(self,websocket:WebSocket,room_name:str):
        if room_name in self.active_connections:
            self.active_connections[room_name].remove(websocket)

    async def relay_notification(self,message:str,room_name:str):
        if room_name in self.active_connections:
            for connection in self.active_connections[room_name]:
                await connection.send_text(message)

    async def broadcast_chat(self,message:str,room_name:str,sender:WebSocket):
        if room_name in self.active_connections:
            for connection in self.active_connections[room_name]:
                if connection != sender:
                    await connection.send_text(message)

manager = ConnectionManager()
#HTTP  ENDPOINT
@app.post("/api/notify")
async def send_notification(notification:NotificationSchema):
    print(f"Received API request for room : {notification.room_name}")

    await manager.relay_notification(notification.message,notification.room_name)

    return {"status": "notification send"}

#The WebSocket Endpoint ---
@app.websocket("/ws/{room_name}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, user_id: str):
    await manager.connect(websocket, room_name)
    try:
        await manager.relay_notification(f"system:{user_id}joined the chat.",room_name)
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_name)
        await manager.relay_notification(f"system:{user_id} left.",room_name)
#server start
if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0",port=8000)