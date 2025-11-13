import asyncio
import websockets

active_connections = {}

async def connection_handler(websocket, path):
    user_ID = None
    try:
        user_ID = await websocket.recv()
        active_connections[user_ID] = websocket
        print(f" Connected: {user_ID}. (Total: {len(active_connections)})")
        await websocket.send(f"Welcome, {user_ID}!")
        
        async for message in websocket:
            await websocket.send(f"Server echoes: {message}")
            
    except websockets.exceptions.ConnectionClosed:
        pass 
    finally:
        
        if user_ID in active_connections:
            del active_connections[user_ID]
            print(f" Disconnected: {user_ID}. (Total: {len(active_connections)})")

async def main():
    async with websockets.serve(connection_handler, "localhost", 8765):
        print("Server started on ws://localhost:8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())