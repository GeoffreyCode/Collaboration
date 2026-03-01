#!/usr/bin/env python3
"""
Collaboration 服务端主程序
支持花生壳HTTP内网穿透和更新推送
"""

import socket
import threading
import json
import time
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib
import uuid

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collaboration_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 服务器配置（从config.py中复制必要部分，避免导入问题）
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 14725
BUFFER_SIZE = 8192
ENCODING = 'utf-8'
MAX_CLIENTS = 100
HEARTBEAT_INTERVAL = 30
CONNECTION_TIMEOUT = 60

# 消息类型定义
MSG_TYPE = {
    'SYSTEM': 'system',
    'NOTIFICATION': 'notification',
    'MESSAGE': 'message',
    'PRIVATE': 'private',
    'FILE': 'file',
    'IMAGE': 'image',
    'COMMAND': 'command',
    'HEARTBEAT': 'heartbeat',
    'USERS': 'users',
    'ERROR': 'error',
    'UPDATE': 'update',
    'UPDATE_CHECK': 'update_check',
    'UPDATE_AVAILABLE': 'update_available',
    'UPDATE_DOWNLOAD': 'update_download',
    'UPDATE_PROGRESS': 'update_progress',
    'UPDATE_COMPLETE': 'update_complete'
}


class ClientInfo:
    """客户端信息"""

    def __init__(self, socket, address, username, user_id):
        self.socket = socket
        self.address = address
        self.username = username
        self.user_id = user_id
        self.connected_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.status = 'online'


class CollaborationServer:
    """Collaboration 服务端"""

    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.clients: Dict[socket.socket, ClientInfo] = {}
        self.user_sockets: Dict[str, socket.socket] = {}  # user_id -> socket
        self.lock = threading.Lock()
        self.running = False
        self.message_count = 0
        self.total_connections = 0
        self.start_time = datetime.now()

        # 用户数据
        self.users_file = 'users.json'
        self.users = self.load_users()

        logger.info("Collaboration Server 初始化完成")

    def load_users(self) -> Dict:
        """加载用户数据"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        else:
            # 创建默认用户
            default_users = {
                'admin': {
                    'user_id': str(uuid.uuid4()),
                    'username': 'admin',
                    'password': self.hash_password('admin123'),
                    'email': 'admin@example.com',
                    'created_at': datetime.now().isoformat(),
                    'last_login': None,
                    'status': 'offline'
                }
            }
            self.save_users(default_users)
            return default_users

    def save_users(self, users: Optional[Dict] = None):
        """保存用户数据"""
        if users is None:
            users = self.users

        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}")

    def hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate_user(self, username: str, password: str):
        """验证用户"""
        user = self.users.get(username)

        if not user:
            # 新用户自动注册
            return self.register_user(username, password)

        # 验证密码
        hashed_password = self.hash_password(password)
        if user['password'] == hashed_password:
            # 更新最后登录时间
            user['last_login'] = datetime.now().isoformat()
            user['status'] = 'online'
            self.save_users()
            return user['user_id'], 'success'
        else:
            return '', 'invalid_password'

    def register_user(self, username: str, password: str):
        """注册新用户"""
        if username in self.users:
            return '', 'username_exists'

        user_id = str(uuid.uuid4())
        hashed_password = self.hash_password(password)

        self.users[username] = {
            'user_id': user_id,
            'username': username,
            'password': hashed_password,
            'email': f'{username}@collaboration.com',
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'status': 'online'
        }

        self.save_users()
        logger.info(f"新用户注册: {username}")
        return user_id, 'success'

    def start(self):
        """启动服务器"""
        try:
            self.server.bind((SERVER_HOST, SERVER_PORT))
            self.server.listen(MAX_CLIENTS)
            self.running = True

            logger.info(f"服务器启动在 {SERVER_HOST}:{SERVER_PORT}")
            logger.info("等待客户端连接...")

            # 启动心跳检测线程
            heartbeat_thread = threading.Thread(target=self.check_heartbeats, daemon=True)
            heartbeat_thread.start()

            # 接受客户端连接
            while self.running:
                try:
                    client_socket, client_addr = self.server.accept()
                    client_socket.settimeout(CONNECTION_TIMEOUT)

                    logger.info(f"新连接: {client_addr}")
                    self.total_connections += 1

                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except Exception as e:
                    if self.running:
                        logger.error(f"接受连接时出错: {e}")

        except Exception as e:
            logger.error(f"服务器启动失败: {e}")
            raise
        finally:
            self.stop()

    def handle_client(self, client_socket: socket.socket, client_addr: tuple):
        """处理客户端连接"""
        client_info = None

        try:
            # 接收客户端初始数据
            data = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
            if not data:
                logger.warning(f"空数据来自 {client_addr}")
                client_socket.close()
                return

            try:
                login_data = json.loads(data)
                message_type = login_data.get('type')

                if message_type == MSG_TYPE['HEARTBEAT']:
                    # 心跳包响应
                    response = {
                        'type': MSG_TYPE['HEARTBEAT'],
                        'status': 'alive',
                        'timestamp': datetime.now().isoformat()
                    }
                    client_socket.send(json.dumps(response).encode(ENCODING))
                    client_socket.close()
                    return

                elif message_type == 'login':
                    # 处理登录
                    username = login_data.get('username', '').strip()
                    password = login_data.get('password', '')

                    if not username:
                        self.send_error(client_socket, "用户名不能为空")
                        client_socket.close()
                        return

                    # 用户验证
                    user_id, status = self.authenticate_user(username, password)

                    if status == 'success':
                        # 创建客户端信息
                        client_info = ClientInfo(
                            socket=client_socket,
                            address=client_addr,
                            username=username,
                            user_id=user_id
                        )

                        with self.lock:
                            self.clients[client_socket] = client_info
                            self.user_sockets[user_id] = client_socket

                        # 更新用户状态
                        self.update_user_status(user_id, 'online')

                        # 发送登录成功响应
                        login_response = {
                            'type': 'login_response',
                            'status': 'success',
                            'user_id': user_id,
                            'username': username,
                            'timestamp': datetime.now().isoformat(),
                            'message': '登录成功'
                        }
                        client_socket.send(json.dumps(login_response).encode(ENCODING))

                        # 广播用户上线通知
                        self.broadcast_user_status(user_id, username, 'online')

                        # 发送在线用户列表
                        self.send_online_users(client_socket)

                        logger.info(f"用户登录: {username} ({user_id})")

                        # 处理客户端消息
                        while self.running:
                            try:
                                data = client_socket.recv(BUFFER_SIZE)
                                if not data:
                                    break

                                message = json.loads(data.decode(ENCODING))
                                self.handle_message(client_socket, message)

                                # 更新心跳时间
                                with self.lock:
                                    if client_socket in self.clients:
                                        self.clients[client_socket].last_heartbeat = datetime.now()

                            except socket.timeout:
                                continue
                            except json.JSONDecodeError:
                                logger.warning(f"无效的JSON数据来自 {username}")
                            except Exception as e:
                                logger.error(f"处理消息时出错: {e}")
                                break

                    else:
                        self.send_error(client_socket, f"登录失败: {status}")
                        client_socket.close()
                        return

                else:
                    self.send_error(client_socket, "无效的消息类型")
                    client_socket.close()
                    return

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误来自 {client_addr}: {e}")
                self.send_error(client_socket, "无效的JSON数据")
                client_socket.close()
                return

        except ConnectionResetError:
            logger.info(f"连接重置: {client_info.username if client_info else 'unknown'}")
        except Exception as e:
            logger.error(f"客户端处理错误: {e}")
        finally:
            # 客户端断开连接
            if client_info:
                with self.lock:
                    if client_socket in self.clients:
                        del self.clients[client_socket]
                    if client_info.user_id in self.user_sockets:
                        del self.user_sockets[client_info.user_id]

                # 更新用户状态
                self.update_user_status(client_info.user_id, 'offline')

                # 广播用户离线通知
                if client_info.username:
                    self.broadcast_user_status(
                        client_info.user_id,
                        client_info.username,
                        'offline'
                    )
                    logger.info(f"用户离线: {client_info.username}")

            try:
                client_socket.close()
            except:
                pass

    def handle_message(self, client_socket: socket.socket, message: Dict[str, Any]):
        """处理消息"""
        with self.lock:
            if client_socket not in self.clients:
                return

            client_info = self.clients[client_socket]
            msg_type = message.get('type')

            if msg_type == MSG_TYPE['MESSAGE']:
                # 处理文本消息
                content = message.get('content', '')

                text_message = {
                    'type': MSG_TYPE['MESSAGE'],
                    'user_id': client_info.user_id,
                    'username': client_info.username,
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                }

                # 广播消息
                self.broadcast(text_message, exclude=client_socket)
                self.message_count += 1

                logger.info(f"消息来自 {client_info.username}: {content[:50]}...")

            elif msg_type == MSG_TYPE['PRIVATE']:
                # 处理私聊消息
                target_user_id = message.get('target_user_id')
                content = message.get('content', '')

                private_message = {
                    'type': MSG_TYPE['PRIVATE'],
                    'from_user_id': client_info.user_id,
                    'from_username': client_info.username,
                    'to_user_id': target_user_id,
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                }

                # 发送给目标用户
                if self.send_to_user(target_user_id, private_message):
                    # 也发送回发送者
                    self.send_to_user(client_info.user_id, private_message)
                    logger.info(f"私聊 {client_info.username} -> {target_user_id}")

            elif msg_type == MSG_TYPE['COMMAND']:
                # 处理命令
                command = message.get('command', '')

                if command == 'get_users':
                    self.send_online_users(client_socket)
                elif command == 'get_server_info':
                    server_info = self.get_server_info()
                    response = {
                        'type': MSG_TYPE['COMMAND'],
                        'command': 'server_info',
                        'data': server_info,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.send_to_socket(client_socket, response)

    def broadcast(self, message: Dict[str, Any], exclude: Optional[socket.socket] = None):
        """广播消息给所有客户端"""
        message_json = json.dumps(message)

        with self.lock:
            for client_socket in list(self.clients.keys()):
                if client_socket != exclude and client_socket.fileno() != -1:
                    try:
                        client_socket.send(message_json.encode(ENCODING))
                    except:
                        # 移除失效的客户端
                        client_info = self.clients.get(client_socket)
                        if client_info:
                            self.update_user_status(client_info.user_id, 'offline')
                        del self.clients[client_socket]

    def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """发送消息给指定用户"""
        with self.lock:
            client_socket = self.user_sockets.get(user_id)
            if client_socket and client_socket.fileno() != -1:
                try:
                    message_json = json.dumps(message)
                    client_socket.send(message_json.encode(ENCODING))
                    return True
                except:
                    pass
        return False

    def send_to_socket(self, client_socket: socket.socket, message: Dict[str, Any]):
        """发送消息到指定socket"""
        try:
            message_json = json.dumps(message)
            client_socket.send(message_json.encode(ENCODING))
        except:
            pass

    def send_error(self, client_socket: socket.socket, error_message: str):
        """发送错误消息"""
        error_msg = {
            'type': MSG_TYPE['ERROR'],
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        try:
            client_socket.send(json.dumps(error_msg).encode(ENCODING))
        except:
            pass

    def broadcast_user_status(self, user_id: str, username: str, status: str):
        """广播用户状态变化"""
        status_message = {
            'type': MSG_TYPE['NOTIFICATION'],
            'subtype': 'user_status',
            'user_id': user_id,
            'username': username,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        self.broadcast(status_message)

    def send_online_users(self, client_socket: socket.socket):
        """发送在线用户列表"""
        with self.lock:
            online_users = []
            for info in self.clients.values():
                online_users.append({
                    'user_id': info.user_id,
                    'username': info.username,
                    'status': info.status
                })

        users_message = {
            'type': MSG_TYPE['USERS'],
            'users': online_users,
            'timestamp': datetime.now().isoformat()
        }

        self.send_to_socket(client_socket, users_message)

    def update_user_status(self, user_id: str, status: str):
        """更新用户状态"""
        for username, user in self.users.items():
            if user['user_id'] == user_id:
                user['status'] = status
                self.save_users()
                break

    def check_heartbeats(self):
        """检查客户端心跳"""
        while self.running:
            time.sleep(HEARTBEAT_INTERVAL)

            with self.lock:
                current_time = datetime.now()
                disconnected_clients = []

                for client_socket, client_info in list(self.clients.items()):
                    time_diff = (current_time - client_info.last_heartbeat).total_seconds()

                    if time_diff > HEARTBEAT_INTERVAL * 3:  # 3倍间隔
                        disconnected_clients.append(client_info)

                # 处理断开连接的客户端
                for client_info in disconnected_clients:
                    logger.info(f"心跳超时: {client_info.username}")
                    del self.clients[client_info.socket]
                    if client_info.user_id in self.user_sockets:
                        del self.user_sockets[client_info.user_id]

                    # 更新用户状态
                    self.update_user_status(client_info.user_id, 'offline')

                    # 广播用户离线
                    self.broadcast_user_status(
                        client_info.user_id,
                        client_info.username,
                        'offline'
                    )

    def stop(self):
        """停止服务器"""
        self.running = False

        # 更新所有用户状态为离线
        for client_info in self.clients.values():
            self.update_user_status(client_info.user_id, 'offline')

        # 关闭所有客户端连接
        with self.lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
            self.user_sockets.clear()

        # 关闭服务器socket
        try:
            self.server.close()
        except:
            pass

        logger.info("服务器已停止")

    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        with self.lock:
            return {
                'name': 'Collaboration Server',
                'version': '1.0.0',
                'host': SERVER_HOST,
                'port': SERVER_PORT,
                'online_users': len(self.clients),
                'max_clients': MAX_CLIENTS,
                'message_count': self.message_count,
                'total_connections': self.total_connections,
                'uptime': str(datetime.now() - self.start_time),
                'start_time': self.start_time.isoformat()
            }

    def broadcast_system_message(self, message: str):
        """广播系统消息"""
        system_message = {
            'type': MSG_TYPE['SYSTEM'],
            'content': message,
            'timestamp': datetime.now().isoformat()
        }
        self.broadcast(system_message)


def main():
    """主函数"""
    print("=" * 60)
    print("Collaboration Server v1.0.0")
    print("即时通讯协作软件服务端")
    print("=" * 60)

    server = CollaborationServer()

    try:
        server.start()
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        server.stop()
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()