import asyncio
import websockets
import json
#this is server 
connected_clients = {}

async def handle_connection(websocket, path):
    """
    This function is called for each new client that connects.
    """
    user_id = None
    try:

        first_message = await websocket.recv()
        data = json.loads(first_message)
        
        
        if 'user_id' in data:
            user_id = data['user_id']  
            connected_clients[user_id] = websocket
            print(f" New connection: {user_id} has joined.")
            print(f"   Total active users: {list(connected_clients.keys())}")
            
            await websocket.send(json.dumps({"status": "success", "message": f"Welcome {user_id}!"}))
        else:
            await websocket.send(json.dumps({"status": "error", "message": "User ID is required."}))
            await websocket.close()
            return

        async for message in websocket:
            print(f"Message from {user_id}: {message}")
            await websocket.send(f"Server received your message: {message}")

    except websockets.exceptions.ConnectionClosed:
        print(f"Connection lost with {user_id}.")
    
    finally:
        if user_id in connected_clients:
            del connected_clients[user_id]
            print(f" Disconnected: {user_id} has left.")
            print(f"   Total active users: {list(connected_clients.keys())}")

# START THE SERVER
async def main():
    print("Starting WebSocket server on ws://localhost:8765")
    async with websockets.serve(handle_connection, "localhost", 8765):
        await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())