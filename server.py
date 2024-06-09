import asyncio
import websockets
import json

connected_clients = set()  # 存储已连接的客户端
message_history = []  # 存储消息历史记录

async def handler(websocket, path):
    '''
    处理每个客户端的连接和消息
    
    Args:
        websocket: WebSocket 连接对象
        path: WebSocket 路径（未使用）
    '''
    # 将新连接的客户端添加到集合中
    connected_clients.add(websocket)
    
    # 发送历史消息给新连接的客户端
    for message in message_history:
        await websocket.send(message)
    
    try:
        # 处理收到的每条消息
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'message':
                # 将消息添加到历史消息列表
                message_history.append(json.dumps(data))
                
                # 广播消息给所有连接的客户端
                broadcast_message = json.dumps(data)
                await asyncio.wait([client.send(broadcast_message) for client in connected_clients])
    finally:
        # 客户端断开连接时，从集合中移除
        connected_clients.remove(websocket)

# 启动 WebSocket 服务器，监听所有 IP 地址的 8765 端口
start_server = websockets.serve(handler, "0.0.0.0", 8765)

# 获取事件循环并启动服务器
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
