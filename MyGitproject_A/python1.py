import asyncio
import json
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app:FastAPI):
    task = asyncio.create_task(manager.listen_for_broadcasts())
    yield
    task.cancel() #stoping from task shutdown

app = FastAPI(lifespan=lifespan)

# The Connection Manager ---
class ConnectionManager:
    def __init__(self):
       self.active_connections: dict = {}
       self.redis_client=redis.from_url("redis://localhost:6379",decode_responses=True)
       self.pubsub=self.redis_client.pubsub()

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
            #store in the user room 
        self.active_connections[room_id].append(websocket)
    
    def disconnect(self,websocket:WebSocket,room_id:str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)

    async def listen_for_broadcasts(self):
        #background task for hears messages
        await self.pubsub.subscribe("internship_notification")
        async for message in self.pubsub.listen():
            if message["type"]=="message":
                data = json.loads(message["data"])
                #send the message to local client
                await self.broadcasts_locally(data["room_id"],data["message"])

        async def broadcasts_locally(self,room_id:str,message:str):
            #send the message only to people connected to this specific server.
            if room_id in self.active_connections:
                for connection in self.active_connections[room_id]:
                    await connection.send_text(message)

manager = ConnectionManager()
#HTTP  ENDPOINT
class Notification(BaseModel):
    room_id:str
    message:str

@app.post("/notify/")
async def trigger_notification(notification:Notification):
    payload = json.dumps({
        "room_id":notification.room_id,
        "message":notification.message
        })
    await manager.redis_client.publish("internship_notifications",payload)
    return {"status": "Notification sent to Redis bus"}

#The WebSocket Endpoint ---
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)