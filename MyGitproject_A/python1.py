import asyncio
import json
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
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
        await self.pubsub.subscribe("internship_notifications")
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
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

@app.get("/",response_class=HTMLResponse)
async def get_test_client():


    return """<!DOCTYPE html>
    <html>
        <head>
            <title>Week 7 Notification System Test Tool</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        </head>
        <body>
            <h1>Real-Time Notification System Testing Hub</h1>
            <div>
                <label for="roomInput">Room ID:</label>
                <input type="text" id="roomInput" value="room101" placeholder="Enter room ID...">
                <button onclick="connectWebSocket()">Connect WebSocket</button>
                <span id="connectionStatus" style="font-weight: bold; color: gray;"> Disconnected</span>
            </div>
            <hr>
            <h3>Live Streaming Notifications</h3>
            <ul id="notificationsLog" style="list-style-type: none; padding-left: 0;">
                <li style="color: gray; font-style: italic;">No active alerts streaming yet...</li>
            </ul>
            <script>
                let ws;
                function connectWebSocket() {
                    const roomId = document.getElementById('roomInput').value;
                    if (ws) { ws.close(); }
                    
                    // Open clean stateful routing back to API matching target parameter path
                    ws = new WebSocket(`ws://${window.location.host}/ws/${roomId}`);
                    const statusText = document.getElementById('connectionStatus');
                    
                    ws.onopen = () => {
                        statusText.innerText = ` Connected to: ${roomId}`;
                        statusText.style.color = "green";
                        const log = document.getElementById('notificationsLog');
                        log.innerHTML = `<li style='color: blue;'>[System]: Stream handshake authorized over channel ${roomId}</li>`;
                    };
                    
                    ws.onmessage = (event) => {
                        const log = document.getElementById('notificationsLog');
                        const newMsg = document.createElement('li');
                        newMsg.innerHTML = `<strong>[Alert]:</strong> ${event.data} <small style='color:gray;'>(${new Date().toLocaleTimeString()})</small>`;
                        log.prepend(newMsg);
                    };
                    
                    ws.onclose = () => {
                        statusText.innerText = " Disconnected";
                        statusText.style.color = "red";
                    };
                }
            </script>
        </body>
    </html>
    """