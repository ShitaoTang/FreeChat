import asyncio
import websockets
import json

connected_clients = set()
message_history = []

async def handler(websocket, path):
    # 将新连接的客户端添加到集合中
    connected_clients.add(websocket)
    
    # 发送历史消息给新连接的客户端
    for message in message_history:
        await websocket.send(message)
    
    try:
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'message':
                # 将消息添加到历史消息列表
                message_history.append(json.dumps(data))
                
                # 广播消息给所有连接的客户端
                broadcast_message = json.dumps(data)
                await asyncio.gather(*[client.send(broadcast_message) for client in connected_clients])
    finally:
        # 客户端断开连接时，从集合中移除
        connected_clients.remove(websocket)

start_server = websockets.serve(handler, "0.0.0.0", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

