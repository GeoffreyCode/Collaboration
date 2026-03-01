#!/usr/bin/env python3
"""
简化版聊天服务器 - Qt6 GUI 界面
"""

import sys
import socket
import threading
import json
import time
from datetime import datetime
from typing import Dict, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QListWidget, QGroupBox,
    QTabWidget, QStatusBar, QMessageBox, QSplitter, QFrame,
    QSystemTrayIcon, QMenu, QToolBar, QStyle
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize,
    QDateTime, QPoint
)
from PyQt6.QtGui import (
    QFont, QIcon, QAction, QTextCursor, QTextCharFormat,
    QColor, QPalette, QBrush, QKeySequence, QShortcut
)

# 服务器配置
HOST = '0.0.0.0'
PORT = 14725
BUFFER_SIZE = 4096
PEANUTSHELL_DOMAIN = '118sx152ry310.vicp.fun'


class ServerThread(QThread):
    """服务器线程"""

    # 定义信号
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)
    log_message = pyqtSignal(str, str)  # level, message
    user_connected = pyqtSignal(str, str)  # username, address
    user_disconnected = pyqtSignal(str, str)  # username, address
    user_list_updated = pyqtSignal(list)  # 在线用户列表
    message_received = pyqtSignal(str, str, str)  # sender, content, timestamp

    def __init__(self):
        super().__init__()
        self.server = None
        self.clients = {}
        self.running = False
        self.lock = threading.Lock()

    def run(self):
        """运行服务器"""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.server.bind((HOST, PORT))
            self.server.listen(5)
            self.server.settimeout(1)  # 设置超时以便可以检查running状态

            self.running = True
            self.server_started.emit()

            self.log_message.emit('info', f"服务器启动在 {HOST}:{PORT}")
            self.log_message.emit('info', f"花生壳地址: http://{PEANUTSHELL_DOMAIN}:{PORT}")

            while self.running:
                try:
                    client_socket, address = self.server.accept()

                    # 为新客户端创建线程
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.log_message.emit('error', f"接受连接错误: {e}")

        except Exception as e:
            self.server_error.emit(str(e))
        finally:
            self.stop_server()
            self.server_stopped.emit()

    def handle_client(self, client_socket, address):
        """处理客户端连接"""
        username = None

        try:
            # 接收客户端数据
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                return

            try:
                login_data = json.loads(data.decode('utf-8'))
                username = login_data.get('username', f'用户{address[1]}')

                with self.lock:
                    self.clients[client_socket] = username

                # 发送用户连接信号
                self.user_connected.emit(username, f"{address[0]}:{address[1]}")

                # 发送欢迎消息
                welcome_msg = {
                    'type': 'system',
                    'content': f'服务器连接成功，'f'欢迎{username}',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                client_socket.send(json.dumps(welcome_msg).encode('utf-8'))

                # 广播新用户加入
                join_msg = {
                    'type': 'notification',
                    'content': f'{username} 加入了聊天室',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                self.broadcast(join_msg, exclude=client_socket)

                # 发送用户列表更新
                self.update_user_list()

                # 处理客户端消息
                while self.running:
                    data = client_socket.recv(BUFFER_SIZE)
                    if not data:
                        break

                    try:
                        msg_data = json.loads(data.decode('utf-8'))

                        if msg_data.get('type') == 'message':
                            content = msg_data.get('content', '')
                            timestamp = datetime.now().strftime('%H:%M:%S')

                            # 发送消息接收信号
                            self.message_received.emit(username, content, timestamp)

                            # 广播消息
                            chat_msg = {
                                'type': 'message',
                                'sender': username,
                                'content': content,
                                'timestamp': timestamp
                            }
                            self.broadcast(chat_msg, exclude=client_socket)

                    except json.JSONDecodeError:
                        pass

            except json.JSONDecodeError:
                self.log_message.emit('warning', f"JSON解析错误来自 {address}")

        except ConnectionResetError:
            if username:
                self.log_message.emit('info', f"连接重置: {username}")
        except Exception as e:
            if username:
                self.log_message.emit('error', f"客户端处理错误 ({username}): {e}")
        finally:
            # 客户端断开
            if username:
                with self.lock:
                    if client_socket in self.clients:
                        del self.clients[client_socket]

                # 发送用户断开信号
                self.user_disconnected.emit(username, f"{address[0]}:{address[1]}")

                # 广播用户离开
                leave_msg = {
                    'type': 'notification',
                    'content': f'{username} 离开了聊天室',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }
                self.broadcast(leave_msg)

                # 发送用户列表更新
                self.update_user_list()

            try:
                client_socket.close()
            except:
                pass

    def broadcast(self, message, exclude=None):
        """广播消息"""
        message_json = json.dumps(message)

        with self.lock:
            for client in list(self.clients.keys()):
                if client != exclude:
                    try:
                        client.send(message_json.encode('utf-8'))
                    except:
                        # 移除失效的客户端
                        if client in self.clients:
                            del self.clients[client]

    def update_user_list(self):
        """更新用户列表"""
        with self.lock:
            users = list(self.clients.values())
            self.user_list_updated.emit(users)

    def stop_server(self):
        """停止服务器"""
        self.running = False

        # 关闭所有客户端连接
        with self.lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()

        # 关闭服务器socket
        if self.server:
            try:
                self.server.close()
            except:
                pass

    def get_server_stats(self):
        """获取服务器统计信息"""
        with self.lock:
            return {
                'online_users': len(self.clients),
                'total_users': len(self.clients)
            }


class ServerGUI(QMainWindow):
    """服务器GUI主窗口"""

    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.current_status = 'stopped'  # stopped, starting, running, stopping

        self.init_ui()
        self.setup_connections()
        self.setup_tray_icon()

    def init_ui(self):
        """初始化界面"""
        # 窗口设置
        self.setWindowTitle("简易聊天服务器")
        self.setGeometry(100, 100, 1000, 700)

        # 设置窗口图标
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 顶部控制栏
        control_bar = self.create_control_bar()
        main_layout.addWidget(control_bar)

        # 分割器（左侧用户列表，右侧日志）
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：用户管理
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 用户列表组
        user_group = QGroupBox("在线用户")
        user_group.setMinimumWidth(250)
        user_layout = QVBoxLayout(user_group)

        # 用户统计
        self.user_stats_label = QLabel("在线: 0")
        self.user_stats_label.setStyleSheet("font-weight: bold; color: #3498db; padding: 5px;")
        user_layout.addWidget(self.user_stats_label)

        # 用户列表
        self.user_list = QListWidget()
        self.user_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d1d9e6;
                border-radius: 5px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #ecf0f1;
            }
        """)
        self.user_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.user_list.customContextMenuRequested.connect(self.show_user_context_menu)

        user_layout.addWidget(self.user_list)
        left_layout.addWidget(user_group)

        # 服务器信息组
        info_group = QGroupBox("服务器信息")
        info_layout = QVBoxLayout(info_group)

        info_text = f"""
        <b>监听地址:</b> {HOST}:{PORT}<br>
        <b>花生壳地址:</b><br>
        http://{PEANUTSHELL_DOMAIN}:{PORT}<br>
        <b>缓冲区大小:</b> {BUFFER_SIZE} bytes<br>
        <b>支持协议:</b> JSON over TCP
        """
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)

        left_layout.addWidget(info_group)
        left_layout.addStretch()

        splitter.addWidget(left_widget)

        # 右侧：日志和消息
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 标签页
        self.tab_widget = QTabWidget()

        # 系统日志标签页
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        log_layout.setContentsMargins(0, 0, 0, 0)

        # 日志工具栏
        log_toolbar = QHBoxLayout()

        self.clear_logs_button = QPushButton("清空日志")
        self.clear_logs_button.clicked.connect(self.clear_logs)

        self.save_logs_button = QPushButton("保存日志")
        self.save_logs_button.clicked.connect(self.save_logs)

        log_toolbar.addWidget(self.clear_logs_button)
        log_toolbar.addWidget(self.save_logs_button)
        log_toolbar.addStretch()

        log_layout.addLayout(log_toolbar)

        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 5px;
                font-family: Consolas, 'Courier New', monospace;
            }
        """)
        log_layout.addWidget(self.log_text)

        self.tab_widget.addTab(log_tab, "📝 系统日志")

        # 消息监控标签页
        message_tab = QWidget()
        message_layout = QVBoxLayout(message_tab)
        message_layout.setContentsMargins(0, 0, 0, 0)

        # 消息工具栏
        msg_toolbar = QHBoxLayout()

        self.clear_messages_button = QPushButton("清空消息")
        self.clear_messages_button.clicked.connect(self.clear_messages)

        msg_toolbar.addWidget(self.clear_messages_button)
        msg_toolbar.addStretch()

        message_layout.addLayout(msg_toolbar)

        # 消息显示区域
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setFont(QFont("Microsoft YaHei", 10))
        self.message_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #d1d9e6;
                border-radius: 5px;
            }
        """)
        message_layout.addWidget(self.message_text)

        self.tab_widget.addTab(message_tab, "💬 消息监控")

        right_layout.addWidget(self.tab_widget)
        splitter.addWidget(right_widget)

        # 设置分割器比例
        splitter.setSizes([300, 700])

        main_layout.addWidget(splitter)

        # 创建状态栏
        self.create_status_bar()

        # 创建菜单栏
        self.create_menu_bar()

        # 应用样式
        self.apply_style()

        # 设置初始状态
        self.update_ui_status()

    def create_control_bar(self):
        """创建控制栏"""
        control_frame = QFrame()
        control_frame.setObjectName("controlFrame")
        control_frame.setStyleSheet("""
            QFrame#controlFrame {
                background-color: #34495e;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        control_layout = QHBoxLayout(control_frame)

        # 服务器状态
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_light = QLabel()
        self.status_light.setFixedSize(20, 20)
        self.status_light.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                border-radius: 10px;
                border: 2px solid #c0392b;
            }
        """)

        self.status_label = QLabel("服务器已停止")
        self.status_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")

        status_layout.addWidget(self.status_light)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        # 控制按钮
        self.start_button = QPushButton("▶ 启动服务器")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.start_button.clicked.connect(self.start_server)

        self.stop_button = QPushButton("⏹ 停止服务器")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)

        self.restart_button = QPushButton("↻ 重启服务器")
        self.restart_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.restart_button.clicked.connect(self.restart_server)

        control_layout.addWidget(status_widget)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.restart_button)

        return control_frame

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态标签
        self.connection_label = QLabel("连接: 0")
        self.status_bar.addWidget(self.connection_label)

        self.message_count_label = QLabel("消息: 0")
        self.status_bar.addWidget(self.message_count_label)

        # 时间标签
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)

        # 更新时间
        self.update_time()
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        start_action = QAction("启动服务器", self)
        start_action.triggered.connect(self.start_server)
        file_menu.addAction(start_action)

        stop_action = QAction("停止服务器", self)
        stop_action.triggered.connect(self.stop_server)
        file_menu.addAction(stop_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 查看菜单
        view_menu = menubar.addMenu("查看")

        show_logs_action = QAction("显示日志", self)
        show_logs_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(show_logs_action)

        show_messages_action = QAction("显示消息", self)
        show_messages_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(show_messages_action)

        # 工具菜单
        tools_menu = menubar.addMenu("工具")

        broadcast_action = QAction("发送广播消息", self)
        broadcast_action.triggered.connect(self.send_broadcast)
        tools_menu.addAction(broadcast_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_tray_icon(self):
        """设置系统托盘图标"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)

            # 设置托盘图标
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            self.tray_icon.setIcon(icon)

            # 创建托盘菜单
            tray_menu = QMenu()

            show_action = QAction("显示", self)
            show_action.triggered.connect(self.show_normal)
            tray_menu.addAction(show_action)

            hide_action = QAction("隐藏", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)

            tray_menu.addSeparator()

            start_action = QAction("启动服务器", self)
            start_action.triggered.connect(self.start_server)
            tray_menu.addAction(start_action)

            stop_action = QAction("停止服务器", self)
            stop_action.triggered.connect(self.stop_server)
            tray_menu.addAction(stop_action)

            tray_menu.addSeparator()

            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

            # 托盘图标点击事件
            self.tray_icon.activated.connect(self.tray_icon_activated)

    def setup_connections(self):
        """设置信号连接"""
        # 服务器状态定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_info)
        self.status_timer.start(2000)  # 2秒更新一次

    def apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #d1d9e6;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2c3e50;
            }

            QTabWidget::pane {
                border: 1px solid #d1d9e6;
                border-radius: 5px;
                background-color: white;
                padding: 5px;
            }

            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }

            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #d6dbdf;
            }

            QPushButton {
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }

            QStatusBar {
                background-color: #ecf0f1;
                color: #7f8c8d;
                border-top: 1px solid #d5dbdb;
            }

            QStatusBar QLabel {
                padding: 2px 10px;
                border-left: 1px solid #d5dbdb;
            }

            QMenuBar {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
            }

            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }

            QMenuBar::item:selected {
                background-color: #34495e;
                border-radius: 3px;
            }

            QMenu {
                background-color: white;
                border: 1px solid #d1d9e6;
                border-radius: 5px;
                padding: 5px;
            }

            QMenu::item {
                padding: 8px 30px 8px 20px;
                border-radius: 3px;
            }

            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)

    def start_server(self):
        """启动服务器"""
        if self.current_status == 'running':
            QMessageBox.information(self, "提示", "服务器已经在运行中")
            return

        self.current_status = 'starting'
        self.update_ui_status()

        # 创建服务器线程
        self.server_thread = ServerThread()

        # 连接信号
        self.server_thread.server_started.connect(self.on_server_started)
        self.server_thread.server_stopped.connect(self.on_server_stopped)
        self.server_thread.server_error.connect(self.on_server_error)
        self.server_thread.log_message.connect(self.on_log_message)
        self.server_thread.user_connected.connect(self.on_user_connected)
        self.server_thread.user_disconnected.connect(self.on_user_disconnected)
        self.server_thread.user_list_updated.connect(self.on_user_list_updated)
        self.server_thread.message_received.connect(self.on_message_received)

        # 启动服务器线程
        self.server_thread.start()

        self.log_message('info', "正在启动服务器...")

    def stop_server(self):
        """停止服务器"""
        if self.current_status != 'running':
            return

        reply = QMessageBox.question(
            self,
            "确认停止",
            "确定要停止服务器吗？所有客户端将断开连接。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_status = 'stopping'
            self.update_ui_status()

            if self.server_thread:
                self.server_thread.stop_server()

            self.log_message('info', "正在停止服务器...")

    def restart_server(self):
        """重启服务器"""
        if self.current_status == 'running':
            self.stop_server()
            # 延迟启动
            QTimer.singleShot(2000, self.start_server)
        else:
            self.start_server()

    def on_server_started(self):
        """服务器启动成功"""
        self.current_status = 'running'
        self.update_ui_status()
        self.log_message('success', "服务器启动成功")

        # 显示通知
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(
                "简易聊天服务器",
                "服务器已启动",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

    def on_server_stopped(self):
        """服务器停止"""
        self.current_status = 'stopped'
        self.update_ui_status()
        self.log_message('info', "服务器已停止")

        # 清空用户列表
        self.user_list.clear()
        self.user_stats_label.setText("在线: 0")

        # 显示通知
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(
                "简易聊天服务器",
                "服务器已停止",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

    def on_server_error(self, error_message):
        """服务器错误"""
        self.current_status = 'error'
        self.update_ui_status()
        self.log_message('error', f"服务器错误: {error_message}")

        QMessageBox.critical(self, "服务器错误", error_message)

    def on_log_message(self, level, message):
        """处理日志消息"""
        self.log_message(level, message)

    def on_user_connected(self, username, address):
        """用户连接"""
        self.log_message('info', f"用户连接: {username} ({address})")

    def on_user_disconnected(self, username, address):
        """用户断开连接"""
        self.log_message('info', f"用户断开: {username} ({address})")

    def on_user_list_updated(self, users):
        """用户列表更新"""
        self.user_list.clear()
        for user in users:
            self.user_list.addItem(f"👤 {user}")

        self.user_stats_label.setText(f"在线: {len(users)}")
        self.connection_label.setText(f"连接: {len(users)}")

    def on_message_received(self, sender, content, timestamp):
        """收到消息"""
        # 在消息监控中显示
        cursor = self.message_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        format = QTextCharFormat()
        format.setForeground(QColor("#3498db"))  # 蓝色
        format.setFontWeight(QFont.Weight.Bold)

        cursor.insertText(f"[{timestamp}] {sender}: ", format)

        # 消息内容
        content_format = QTextCharFormat()
        content_format.setForeground(QColor("#2c3e50"))
        cursor.insertText(f"{content}\n", content_format)

        # 滚动到底部
        self.message_text.ensureCursorVisible()

        # 更新消息计数
        if hasattr(self, 'message_count'):
            self.message_count += 1
        else:
            self.message_count = 1

        self.message_count_label.setText(f"消息: {self.message_count}")

    def log_message(self, level, message):
        """添加日志消息"""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 设置颜色
        format = QTextCharFormat()

        if level == 'error':
            format.setForeground(QColor("#e74c3c"))
            prefix = "[错误] "
        elif level == 'warning':
            format.setForeground(QColor("#f39c12"))
            prefix = "[警告] "
        elif level == 'info':
            format.setForeground(QColor("#3498db"))
            prefix = "[信息] "
        elif level == 'success':
            format.setForeground(QColor("#2ecc71"))
            prefix = "[成功] "
        else:
            format.setForeground(QColor("#ecf0f1"))
            prefix = ""

        # 添加时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor.insertText(f"[{timestamp}] {prefix}{message}\n", format)

        # 自动滚动到底部
        self.log_text.ensureCursorVisible()

    def update_ui_status(self):
        """更新UI状态"""
        status_config = {
            'stopped': {
                'text': "服务器已停止",
                'color': "#e74c3c",
                'start_enabled': True,
                'stop_enabled': False
            },
            'starting': {
                'text': "服务器启动中...",
                'color': "#f39c12",
                'start_enabled': False,
                'stop_enabled': False
            },
            'running': {
                'text': "服务器运行中",
                'color': "#2ecc71",
                'start_enabled': False,
                'stop_enabled': True
            },
            'stopping': {
                'text': "服务器停止中...",
                'color': "#f39c12",
                'start_enabled': False,
                'stop_enabled': False
            },
            'error': {
                'text': "服务器错误",
                'color': "#e74c3c",
                'start_enabled': True,
                'stop_enabled': False
            }
        }

        config = status_config.get(self.current_status, status_config['stopped'])

        self.status_label.setText(config['text'])
        self.status_light.setStyleSheet(f"""
            QLabel {{
                background-color: {config['color']};
                border-radius: 10px;
                border: 2px solid {self.darken_color(config['color'])};
            }}
        """)

        self.start_button.setEnabled(config['start_enabled'])
        self.stop_button.setEnabled(config['stop_enabled'])

    def darken_color(self, color_hex, factor=0.8):
        """加深颜色"""
        import colorsys

        # 将十六进制颜色转换为RGB
        color_hex = color_hex.lstrip('#')
        r, g, b = tuple(int(color_hex[i:i + 2], 16) for i in (0, 2, 4))

        # 转换为HSV，降低亮度
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        v = max(0, v * factor)

        # 转换回RGB
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)

        return f'#{r:02x}{g:02x}{b:02x}'

    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    def update_status_info(self):
        """更新状态信息"""
        # 这里可以添加更多的状态信息更新
        pass

    def clear_logs(self):
        """清空日志"""
        self.log_text.clear()
        self.log_message('info', "日志已清空")

    def clear_messages(self):
        """清空消息"""
        self.message_text.clear()
        self.log_message('info', "消息记录已清空")

    def save_logs(self):
        """保存日志"""
        # 这里可以实现保存日志到文件的功能
        QMessageBox.information(self, "保存日志", "保存日志功能开发中...")

    def send_broadcast(self):
        """发送广播消息"""
        if self.current_status != 'running':
            QMessageBox.warning(self, "错误", "服务器未运行，无法发送广播")
            return

        from PyQt6.QtWidgets import QDialog, QTextEdit, QHBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("发送广播消息")
        dialog.setFixedSize(400, 200)

        layout = QVBoxLayout(dialog)

        label = QLabel("请输入广播消息内容:")
        layout.addWidget(label)

        message_input = QTextEdit()
        message_input.setMaximumHeight(80)
        layout.addWidget(message_input)

        button_layout = QHBoxLayout()

        send_button = QPushButton("发送")
        send_button.clicked.connect(lambda: self.do_send_broadcast(message_input.toPlainText(), dialog))

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)

        button_layout.addWidget(send_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.exec()

    def do_send_broadcast(self, message, dialog):
        """执行发送广播"""
        if not message.strip():
            QMessageBox.warning(self, "错误", "消息内容不能为空")
            return

        if self.server_thread:
            # 这里可以添加发送广播消息的逻辑
            # 例如：self.server_thread.send_broadcast(message)
            self.log_message('info', f"发送广播消息: {message}")
            dialog.accept()

    def show_user_context_menu(self, position):
        """显示用户右键菜单"""
        item = self.user_list.itemAt(position)
        if not item:
            return

        username = item.text().replace("👤 ", "").strip()

        menu = QMenu()

        # 查看信息
        info_action = QAction(f"查看 {username} 信息", self)
        menu.addAction(info_action)

        # 发送私信
        message_action = QAction(f"发送消息给 {username}", self)
        menu.addAction(message_action)

        menu.exec(self.user_list.mapToGlobal(position))

    def show_about(self):
        """显示关于对话框"""
        about_text = f"""
        <div style="text-align: center;">
            <h2>简易聊天服务器</h2>
            <h3>基于 PyQt6 的图形化管理界面</h3>
            <hr>
            <p><b>服务器配置:</b></p>
            <p>监听地址: {HOST}:{PORT}</p>
            <p>花生壳地址: http://{PEANUTSHELL_DOMAIN}:{PORT}</p>
            <p>缓冲区大小: {BUFFER_SIZE} bytes</p>
            <hr>
            <p>支持功能:</p>
            <ul style="text-align: left;">
                <li>多用户聊天室</li>
                <li>实时消息监控</li>
                <li>用户连接管理</li>
                <li>系统日志记录</li>
                <li>系统托盘支持</li>
            </ul>
            <hr>
            <p>© 2023 简易聊天服务器</p>
        </div>
        """

        QMessageBox.about(self, "关于", about_text)

    def tray_icon_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal()

    def show_normal(self):
        """显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """关闭事件"""
        if self.current_status == 'running':
            reply = QMessageBox.question(
                self,
                "确认退出",
                "服务器正在运行，退出将停止服务器。确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # 停止服务器
        if self.server_thread:
            self.server_thread.stop_server()
            self.server_thread.wait(3000)  # 等待3秒

        # 隐藏到托盘或退出
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("简易聊天服务器")
    app.setStyle("Fusion")  # 使用 Fusion 风格

    # 创建并显示窗口
    window = ServerGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()