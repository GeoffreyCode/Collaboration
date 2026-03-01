#!/usr/bin/env python3
"""
基于 PyQt6 的即时通讯客户端
支持通过花生壳内网穿透进行远程通信
"""

import sys
import socket
import json
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QListWidget, QLabel, QStatusBar, QMessageBox,
    QSplitter, QListWidgetItem, QMenu, QSystemTrayIcon,
    QMenuBar, QStyle, QWidgetAction
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QObject, QThread, QTimer,
    QSize, QPoint, QDateTime
)
from PyQt6.QtGui import (
    QFont, QIcon, QColor, QTextCursor, QAction,
    QPixmap, QTextCharFormat, QPalette, QBrush
)

from login_dialog import LoginDialog
from config import PEANUTSHELL_HOST, PEANUTSHELL_PORT, SERVER_PORT
from styles import APP_STYLE, BUTTON_STYLE, LIST_STYLE, INPUT_STYLE


class NetworkThread(QThread):
    """网络通信线程"""
    message_received = pyqtSignal(dict)
    connection_status = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self.client = None
        self.host = PEANUTSHELL_HOST
        self.port = PEANUTSHELL_PORT
        self.username = ""
        self.running = False
        self.buffer_size = 4096
        self.encoding = 'utf-8'

    def set_connection_info(self, host, port, username):
        """设置连接信息"""
        self.host = host
        self.port = port
        self.username = username

    def connect_server(self):
        """连接到服务器"""
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(5)
            self.client.connect((self.host, self.port))

            # 发送登录信息
            login_data = {"username": self.username}
            self.client.send(json.dumps(login_data).encode(self.encoding))

            self.running = True
            self.connection_status.emit(True, "连接成功")
            return True

        except Exception as e:
            error_msg = f"连接失败: {str(e)}"
            self.connection_status.emit(False, error_msg)
            return False

    def run(self):
        """线程主循环 - 接收消息"""
        if not self.client:
            return

        while self.running:
            try:
                data = self.client.recv(self.buffer_size)
                if not data:
                    self.connection_status.emit(False, "服务器断开连接")
                    self.running = False
                    break

                try:
                    message = json.loads(data.decode(self.encoding))
                    self.message_received.emit(message)
                except json.JSONDecodeError:
                    print("JSON解析错误")

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.connection_status.emit(False, f"接收错误: {str(e)}")
                self.running = False
                break

    def send_message(self, message_type, content, target=None):
        """发送消息到服务器"""
        if not self.client or not self.running:
            return False

        try:
            message_data = {"type": message_type, "content": content}
            if target:
                message_data["target"] = target

            self.client.send(json.dumps(message_data).encode(self.encoding))
            return True
        except Exception as e:
            print(f"发送失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        self.running = False
        if self.client:
            try:
                self.client.close()
            except:
                pass


class ChatWindow(QMainWindow):
    """聊天主窗口"""

    def __init__(self, username, host, port):
        super().__init__()
        self.username = username
        self.host = host
        self.port = port
        self.online_users = []
        self.private_chats = {}  # 存储私聊窗口

        # 初始化网络线程
        self.network_thread = NetworkThread()
        self.network_thread.set_connection_info(host, port, username)

        self.init_ui()
        self.setup_connections()
        self.connect_to_server()

    def init_ui(self):
        """初始化用户界面"""
        # 窗口设置
        self.setWindowTitle(f"即时通讯 - {self.username}")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet(APP_STYLE)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左侧分割器（用户列表和聊天记录）
        left_splitter = QSplitter(Qt.Orientation.Vertical)

        # 用户列表区域
        user_widget = QWidget()
        user_layout = QVBoxLayout(user_widget)
        user_layout.setContentsMargins(0, 0, 0, 0)

        user_label = QLabel("在线用户")
        user_label.setStyleSheet("font-weight: bold; padding: 5px;")
        user_layout.addWidget(user_label)

        self.user_list = QListWidget()
        self.user_list.setStyleSheet(LIST_STYLE)
        self.user_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        user_layout.addWidget(self.user_list)

        left_splitter.addWidget(user_widget)

        # 聊天记录区域
        chat_log_widget = QWidget()
        chat_log_layout = QVBoxLayout(chat_log_widget)
        chat_log_layout.setContentsMargins(0, 0, 0, 0)

        chat_label = QLabel("聊天记录")
        chat_label.setStyleSheet("font-weight: bold; padding: 5px;")
        chat_log_layout.addWidget(chat_label)

        self.chat_log = QListWidget()
        self.chat_log.setStyleSheet(LIST_STYLE)
        chat_log_layout.addWidget(self.chat_log)

        left_splitter.addWidget(chat_log_widget)
        left_splitter.setSizes([200, 100])

        # 右侧区域（聊天界面）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)

        # 聊天显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Microsoft YaHei", 10))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        right_layout.addWidget(self.chat_display, 3)

        # 消息输入区域
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 5, 0, 0)

        # 输入框
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入消息... (按Ctrl+Enter发送)")
        self.message_input.setStyleSheet(INPUT_STYLE)
        self.message_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.message_input)

        # 按钮区域
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 5, 0, 0)

        # 发送按钮
        self.send_button = QPushButton("发送 (Ctrl+Enter)")
        self.send_button.setStyleSheet(BUTTON_STYLE)
        self.send_button.clicked.connect(self.send_chat_message)

        # 表情按钮
        self.emoji_button = QPushButton("😊 表情")
        self.emoji_button.setStyleSheet(BUTTON_STYLE)
        self.emoji_button.clicked.connect(self.show_emoji_picker)

        # 文件按钮
        self.file_button = QPushButton("📁 文件")
        self.file_button.setStyleSheet(BUTTON_STYLE)

        # 清空按钮
        self.clear_button = QPushButton("🗑️ 清空")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
            QPushButton:pressed {
                background-color: #e74c3c;
            }
        """)
        self.clear_button.clicked.connect(self.clear_chat)

        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.emoji_button)
        button_layout.addWidget(self.file_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        input_layout.addWidget(button_widget)
        right_layout.addWidget(input_widget)

        # 添加分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([300, 600])

        main_layout.addWidget(main_splitter)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("正在连接服务器...")
        self.status_bar.addWidget(self.status_label)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建系统托盘
        self.create_system_tray()

        # 添加快捷键
        self.setup_shortcuts()

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        new_chat_action = QAction("新建聊天", self)
        new_chat_action.triggered.connect(self.new_chat)
        file_menu.addAction(new_chat_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图")

        show_users_action = QAction("显示用户列表", self)
        show_users_action.setCheckable(True)
        show_users_action.setChecked(True)
        show_users_action.triggered.connect(self.toggle_user_list)
        view_menu.addAction(show_users_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_system_tray(self):
        """创建系统托盘"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(
                QStyle.StandardPixmap.SP_ComputerIcon
            ))

            tray_menu = QMenu()

            show_action = QAction("显示", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)

            hide_action = QAction("隐藏", self)
            hide_action.triggered.connect(self.hide)
            tray_menu.addAction(hide_action)

            tray_menu.addSeparator()

            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            self.tray_icon.activated.connect(self.tray_icon_activated)

    def setup_shortcuts(self):
        """设置快捷键"""
        from PyQt6.QtGui import QShortcut, QKeySequence
        # 发送消息快捷键
        self.send_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.send_shortcut.activated.connect(self.send_chat_message)

    def setup_connections(self):
        """连接信号和槽"""
        # 网络线程信号
        self.network_thread.message_received.connect(self.handle_message)
        self.network_thread.connection_status.connect(self.update_connection_status)

        # 用户列表右键菜单
        self.user_list.customContextMenuRequested.connect(self.show_user_context_menu)

        # 双击用户开始私聊
        self.user_list.itemDoubleClicked.connect(self.start_private_chat)

    def connect_to_server(self):
        """连接到服务器"""
        if self.network_thread.connect_server():
            self.network_thread.start()
        else:
            QMessageBox.critical(self, "连接失败",
                                 f"无法连接到服务器 {self.host}:{self.port}")
            self.close()

    def handle_message(self, message):
        """处理接收到的消息"""
        msg_type = message.get('type')

        if msg_type == 'system':
            self.append_system_message(message['content'])

        elif msg_type == 'notification':
            self.append_notification(message['content'])

            # 更新用户列表
            if "加入了" in message['content']:
                username = message['content'].split()[0]
                if username not in self.online_users and username != self.username:
                    self.online_users.append(username)
                    self.update_user_list()
            elif "离开了" in message['content']:
                username = message['content'].split()[0]
                if username in self.online_users:
                    self.online_users.remove(username)
                    self.update_user_list()

        elif msg_type == 'message':
            sender = message['sender']
            content = message['content']
            timestamp = message['timestamp']
            self.append_message(sender, content, timestamp, is_private=False)

        elif msg_type == 'private':
            sender = message['sender']
            content = message['content']
            timestamp = message['timestamp']
            self.append_message(sender, content, timestamp, is_private=True)

        elif msg_type == 'users':
            users = message.get('users', [])
            self.online_users = [u for u in users if u != self.username]
            self.update_user_list()

    def append_message(self, sender, content, timestamp, is_private=False):
        """添加消息到聊天显示区域"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 创建消息格式
        if is_private:
            prefix = f"[{timestamp}] [私聊] {sender}: "
            color = QColor("#8e44ad")  # 紫色
        else:
            prefix = f"[{timestamp}] {sender}: "
            color = QColor("#3498db")  # 蓝色

        # 插入发送者信息
        sender_format = QTextCharFormat()
        sender_format.setForeground(color)
        sender_format.setFontWeight(QFont.Weight.Bold)
        cursor.insertText(prefix, sender_format)

        # 插入消息内容
        content_format = QTextCharFormat()
        cursor.insertText(f"{content}\n", content_format)

        # 滚动到底部
        self.chat_display.ensureCursorVisible()

    def append_system_message(self, content):
        """添加系统消息"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        format = QTextCharFormat()
        format.setForeground(QColor("#e74c3c"))  # 红色
        format.setFontItalic(True)

        cursor.insertText(f"[系统] {content}\n", format)
        self.chat_display.ensureCursorVisible()

    def append_notification(self, content):
        """添加通知消息"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        format = QTextCharFormat()
        format.setForeground(QColor("#f39c12"))  # 橙色
        format.setFontItalic(True)

        cursor.insertText(f"[通知] {content}\n", format)
        self.chat_display.ensureCursorVisible()

    def send_chat_message(self):
        """发送聊天消息"""
        message = self.message_input.text().strip()
        if not message:
            return

        if message.startswith('/'):
            self.handle_command(message)
        else:
            if self.network_thread.send_message('message', message):
                # 显示自己发送的消息
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.append_message("我", message, timestamp)
                self.message_input.clear()

    def handle_command(self, command):
        """处理命令"""
        if command.startswith('/pm ') or command.startswith('/msg '):
            parts = command.split(' ', 2)
            if len(parts) >= 3:
                target_user = parts[1]
                content = parts[2]

                if target_user == self.username:
                    QMessageBox.warning(self, "警告", "不能给自己发送私聊消息")
                    return

                if self.network_thread.send_message('private', content, target_user):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.append_message(f"我 → {target_user}", content, timestamp, is_private=True)
                    self.message_input.clear()
        elif command == '/users' or command == '/list':
            self.status_label.setText(f"在线用户: {len(self.online_users)}人")
        elif command == '/help':
            self.show_help()
        elif command == '/clear':
            self.clear_chat()

    def update_user_list(self):
        """更新用户列表"""
        self.user_list.clear()
        for user in sorted(self.online_users):
            item = QListWidgetItem(f"👤 {user}")
            self.user_list.addItem(item)

        # 更新状态栏
        self.status_label.setText(f"在线: {len(self.online_users)}人 | 服务器: {self.host}:{self.port}")

    def show_user_context_menu(self, position):
        """显示用户右键菜单"""
        item = self.user_list.itemAt(position)
        if not item:
            return

        username = item.text().replace("👤 ", "").strip()

        menu = QMenu()

        # 私聊
        pm_action = QAction(f"私聊 {username}", self)
        pm_action.triggered.connect(lambda: self.start_private_chat(item))
        menu.addAction(pm_action)

        # 查看信息
        info_action = QAction(f"查看 {username} 信息", self)
        menu.addAction(info_action)

        menu.exec(self.user_list.mapToGlobal(position))

    def start_private_chat(self, item):
        """开始私聊"""
        username = item.text().replace("👤 ", "").strip()

        if username == self.username:
            return

        # 创建或显示私聊窗口
        if username not in self.private_chats:
            from private_chat_window import PrivateChatWindow
            private_window = PrivateChatWindow(self.username, username, self.network_thread)
            private_window.show()
            self.private_chats[username] = private_window
        else:
            self.private_chats[username].show()
            self.private_chats[username].raise_()

    def show_emoji_picker(self):
        """显示表情选择器"""
        # 简化的表情选择器
        emojis = ["😀", "😂", "😊", "😍", "👍", "❤️", "🎉", "🔥", "✨", "🌟"]

        menu = QMenu(self)

        # 创建两列布局
        layout = QHBoxLayout()
        left_column = QVBoxLayout()
        right_column = QVBoxLayout()

        for i, emoji in enumerate(emojis):
            action = QAction(emoji, self)
            action.triggered.connect(lambda checked, e=emoji: self.insert_emoji(e))

            if i < len(emojis) // 2:
                left_column.addWidget(self.create_emoji_button(emoji))
            else:
                right_column.addWidget(self.create_emoji_button(emoji))

        layout.addLayout(left_column)
        layout.addLayout(right_column)

        widget = QWidget()
        widget.setLayout(layout)
        action = QWidgetAction(menu)
        action.setDefaultWidget(widget)
        menu.addAction(action)

        menu.exec(self.emoji_button.mapToGlobal(QPoint(0, self.emoji_button.height())))

    def create_emoji_button(self, emoji):
        """创建表情按钮"""
        btn = QPushButton(emoji)
        btn.setFixedSize(40, 40)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        btn.clicked.connect(lambda: self.insert_emoji(emoji))
        return btn

    def insert_emoji(self, emoji):
        """插入表情到输入框"""
        self.message_input.insert(emoji)
        self.message_input.setFocus()

    def clear_chat(self):
        """清空聊天记录"""
        reply = QMessageBox.question(self, "确认",
                                     "确定要清空聊天记录吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_display.clear()

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h3>即时通讯客户端 v1.0</h3>
        <p>基于 PyQt6 开发的即时通讯软件</p>
        <p>支持功能：</p>
        <ul>
            <li>公共聊天室</li>
            <li>私聊功能</li>
            <li>在线用户列表</li>
            <li>表情发送</li>
            <li>系统托盘</li>
        </ul>
        <p>服务器地址: {host}:{port}</p>
        <p>当前用户: {username}</p>
        <hr>
        <p>© 2023 即时通讯客户端</p>
        """.format(host=self.host, port=self.port, username=self.username)

        QMessageBox.about(self, "关于", about_text)

    def show_help(self):
        """显示帮助"""
        help_text = """
        <h3>使用帮助</h3>
        <p><b>基本操作:</b></p>
        <ul>
            <li>直接在输入框输入消息并发送</li>
            <li>双击在线用户开始私聊</li>
            <li>右键点击用户查看更多选项</li>
        </ul>
        <p><b>快捷键:</b></p>
        <ul>
            <li>Ctrl+Enter: 发送消息</li>
            <li>Ctrl+C: 复制</li>
            <li>Ctrl+V: 粘贴</li>
        </ul>
        <p><b>命令:</b></p>
        <ul>
            <li>/pm 用户名 消息 - 私聊</li>
            <li>/users 或 /list - 查看在线用户</li>
            <li>/clear - 清空聊天记录</li>
            <li>/help - 显示此帮助</li>
        </ul>
        """

        QMessageBox.information(self, "帮助", help_text)

    def update_connection_status(self, connected, message):
        """更新连接状态"""
        if connected:
            self.status_bar.showMessage(f"已连接到服务器 - {message}", 5000)
        else:
            self.status_bar.showMessage(f"连接异常 - {message}", 5000)
            if "断开" in message:
                QMessageBox.warning(self, "连接断开", "与服务器的连接已断开")

    def toggle_user_list(self, visible):
        """切换用户列表显示"""
        self.user_list.setVisible(visible)

    def new_chat(self):
        """新建聊天"""
        self.message_input.setFocus()

    def tray_icon_activated(self, reason):
        """系统托盘图标激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()

    def quit_application(self):
        """退出应用程序"""
        self.network_thread.disconnect()
        QApplication.quit()

    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(self, "确认退出",
                                     "确定要退出聊天程序吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.network_thread.disconnect()
            event.accept()
        else:
            event.ignore()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("即时通讯客户端")
    app.setStyle("Fusion")  # 使用 Fusion 风格

    # 显示登录对话框
    login_dialog = LoginDialog()
    if login_dialog.exec():
        username, host, port = login_dialog.get_login_info()

        # 创建并显示主窗口
        chat_window = ChatWindow(username, host, port)
        chat_window.show()

        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()