import asyncio
import websockets
import json
# this is client 
async def connect_and_identify():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # Send our User ID as the first message
        my_id = "Pankaj" 
        await websocket.send(json.dumps({"user_id": my_id}))
        
        # Wait for the server
        response = await websocket.recv()
        print(f"< Server: {response}")

        # SEND A NORMAL MESSAGE
        await websocket.send("Hello from the client!")
        
        # Get the response
        response = await websocket.recv()
        print(f"< Server: {response}")

        # Keep connection open for a bit
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(connect_and_identify())