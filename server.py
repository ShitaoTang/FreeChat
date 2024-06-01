import asyncio
import websockets
import json

connected_clients = set()

async def handler(websocket, path):
    # 将新连接的客户端添加到集合中
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'message':
                broadcast_message = json.dumps(data)
                await asyncio.wait([client.send(broadcast_message) for client in connected_clients])
    finally:
        # 客户端断开连接时，从集合中移除
        connected_clients.remove(websocket)

start_server = websockets.serve(handler, "0.0.0.0", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
