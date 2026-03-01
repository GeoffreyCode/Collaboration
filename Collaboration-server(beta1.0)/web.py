#!/usr/bin/env python3
"""
WebSocket聊天服务器
支持浏览器直接连接
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Set, Dict

# 配置
HOST = '0.0.0.0'
PORT = 14725
PEANUTSHELL_DOMAIN = '118sx152ry310.vicp.fun'

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 存储连接的客户端
connected_clients: Set[websockets.WebSocketServerProtocol] = set()
# 用户名映射
usernames: Dict[websockets.WebSocketServerProtocol, str] = {}


async def handle_connection(websocket, path):
    """处理WebSocket连接"""
    # 记录新连接
    client_ip = websocket.remote_address[0] if websocket.remote_address else 'unknown'
    logger.info(f"新连接: {client_ip}")

    # 添加到连接集合
    connected_clients.add(websocket)
    username = None

    try:
        # 等待客户端发送用户名
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get('type')

                if message_type == 'login':
                    # 登录消息
                    username = data.get('username', f'用户{client_ip}')
                    usernames[websocket] = username

                    # 发送欢迎消息
                    welcome_msg = {
                        'type': 'system',
                        'content': f'欢迎 {username} 进入聊天室！',
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    }
                    await websocket.send(json.dumps(welcome_msg))

                    # 广播新用户加入
                    join_msg = {
                        'type': 'notification',
                        'content': f'{username} 加入了聊天室',
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    }
                    await broadcast(join_msg, exclude=websocket)

                    # 发送当前在线用户列表
                    await send_user_list()

                    logger.info(f"用户登录: {username}")

                elif message_type == 'message':
                    # 聊天消息
                    if username:
                        content = data.get('content', '')
                        chat_msg = {
                            'type': 'message',
                            'sender': username,
                            'content': content,
                            'timestamp': datetime.now().strftime('%H:%M:%S')
                        }
                        await broadcast(chat_msg, exclude=websocket)
                        logger.info(f"消息来自 {username}: {content[:50]}...")

                elif message_type == 'ping':
                    # 心跳响应
                    pong_msg = {
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(pong_msg))

            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析错误: {e}")
                error_msg = {
                    'type': 'error',
                    'content': '消息格式错误',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                await websocket.send(json.dumps(error_msg))

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"连接关闭: {client_ip}")
    except Exception as e:
        logger.error(f"处理连接时出错: {e}")
    finally:
        # 客户端断开连接
        if websocket in connected_clients:
            connected_clients.remove(websocket)

        if websocket in usernames:
            username = usernames[websocket]
            del usernames[websocket]

            # 广播用户离开
            if username:
                leave_msg = {
                    'type': 'notification',
                    'content': f'{username} 离开了聊天室',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                await broadcast(leave_msg)
                logger.info(f"用户离开: {username}")

            # 更新用户列表
            await send_user_list()


async def broadcast(message, exclude=None):
    """广播消息给所有客户端"""
    message_json = json.dumps(message)

    for client in connected_clients.copy():
        if client != exclude:
            try:
                await client.send(message_json)
            except:
                # 移除失效的客户端
                if client in connected_clients:
                    connected_clients.remove(client)
                if client in usernames:
                    del usernames[client]


async def send_user_list():
    """发送在线用户列表给所有客户端"""
    user_list = list(usernames.values())
    list_msg = {
        'type': 'user_list',
        'users': user_list,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }
    await broadcast(list_msg)


async def periodic_tasks():
    """定期任务"""
    while True:
        try:
            # 每30秒发送心跳检测
            await asyncio.sleep(30)

            # 检查连接状态
            for client in connected_clients.copy():
                try:
                    ping_msg = {
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat()
                    }
                    await client.send(json.dumps(ping_msg))
                except:
                    # 移除失效的客户端
                    if client in connected_clients:
                        connected_clients.remove(client)
                    if client in usernames:
                        del usernames[client]

            # 更新用户列表
            await send_user_list()

        except Exception as e:
            logger.error(f"定期任务出错: {e}")


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info(f"WebSocket聊天服务器 v1.0")
    logger.info(f"监听地址: ws://{HOST}:{PORT}")
    logger.info(f"花生壳地址: ws://{PEANUTSHELL_DOMAIN}:{PORT}")
    logger.info("=" * 50)
    logger.info("等待客户端连接...")

    # 启动WebSocket服务器
    server = await websockets.serve(
        handle_connection,
        HOST,
        PORT,
        ping_interval=20,
        ping_timeout=10,
        max_size=10 * 1024 * 1024  # 10MB
    )

    # 启动定期任务
    asyncio.create_task(periodic_tasks())

    # 保持服务器运行
    await server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器正在停止...")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")