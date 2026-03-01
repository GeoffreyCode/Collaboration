"""
私聊窗口
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

from styles import BUTTON_STYLE, INPUT_STYLE


class PrivateChatWindow(QWidget):
    """私聊窗口"""

    def __init__(self, my_username, target_username, network_thread):
        super().__init__()
        self.my_username = my_username
        self.target_username = target_username
        self.network_thread = network_thread

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"与 {self.target_username} 的私聊")
        self.setGeometry(300, 300, 500, 400)

        layout = QVBoxLayout()

        # 标题栏
        title_label = QLabel(f"私聊 - {self.target_username}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 聊天显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.chat_display)

        # 输入区域
        input_layout = QHBoxLayout()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText(f"发送给 {self.target_username}...")
        self.message_input.setStyleSheet(INPUT_STYLE)
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input, 4)

        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet(BUTTON_STYLE)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button, 1)

        layout.addLayout(input_layout)

        self.setLayout(layout)

    def append_message(self, sender, content, is_me=False):
        """添加消息到聊天窗口"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if is_me:
            prefix = f"[我] {content}"
            color = QColor("#3498db")  # 蓝色
        else:
            prefix = f"[{sender}] {content}"
            color = QColor("#8e44ad")  # 紫色

        format = QTextCharFormat()
        format.setForeground(color)
        cursor.insertText(prefix + "\n", format)

        self.chat_display.ensureCursorVisible()

    def send_message(self):
        """发送私聊消息"""
        message = self.message_input.text().strip()
        if not message:
            return

        if self.network_thread.send_message('private', message, self.target_username):
            self.append_message(self.my_username, message, is_me=True)
            self.message_input.clear()

    def receive_message(self, sender, content):
        """接收私聊消息"""
        if sender == self.target_username:
            self.append_message(sender, content, is_me=False)

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.deleteLater()
        event.accept()