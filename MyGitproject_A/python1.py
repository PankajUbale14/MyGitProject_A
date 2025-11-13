import asyncio
import websockets

async def echo(websocket, path):
    async for message in websocket:
        print(f"received message:{message}")

    await websocket.send(f"You said: {message}")

async def main():
    async with websockets.serve (echo,"127.0.0.1",12345):
        print("websocket server started at ws://localhost:12345")  
        await asyncio.Future()
    
    if __name__=="__main__":
        asyncio.run(main())