"""
登录对话框
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox,
    QGroupBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QIcon

from config import PEANUTSHELL_HOST, PEANUTSHELL_PORT, SERVER_PORT
from styles import BUTTON_STYLE, INPUT_STYLE, DIALOG_STYLE


class LoginDialog(QDialog):
    """登录对话框"""

    def __init__(self):
        super().__init__()
        self.settings = QSettings("IMChat", "QtClient")
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("登录即时通讯")
        self.setFixedSize(400, 350)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout()

        # 标题
        title_label = QLabel("即时通讯客户端")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 登录表单组
        form_group = QGroupBox("登录信息")
        form_layout = QFormLayout()

        # 用户名
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setStyleSheet(INPUT_STYLE)
        form_layout.addRow("用户名:", self.username_input)

        # 服务器地址
        server_layout = QHBoxLayout()
        self.server_combo = QComboBox()
        self.server_combo.setStyleSheet(INPUT_STYLE)
        self.server_combo.addItems([
            "花生壳服务器",
            "本地服务器",
            "自定义服务器"
        ])
        self.server_combo.currentTextChanged.connect(self.on_server_changed)

        self.custom_host_input = QLineEdit()
        self.custom_host_input.setPlaceholderText("服务器地址")
        self.custom_host_input.setStyleSheet(INPUT_STYLE)
        self.custom_host_input.setVisible(False)

        server_layout.addWidget(self.server_combo, 2)
        server_layout.addWidget(self.custom_host_input, 3)
        form_layout.addRow("服务器:", server_layout)

        # 端口
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("端口号")
        self.port_input.setStyleSheet(INPUT_STYLE)
        form_layout.addRow("端口:", self.port_input)

        # 记住密码选项
        self.remember_check = QCheckBox("记住用户名和服务器")
        form_layout.addRow("", self.remember_check)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.login_button = QPushButton("登录")
        self.login_button.setStyleSheet(BUTTON_STYLE)
        self.login_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 设置默认值
        self.server_combo.setCurrentIndex(0)
        self.on_server_changed("花生壳服务器")

    def on_server_changed(self, server_type):
        """服务器类型改变事件"""
        if server_type == "花生壳服务器":
            self.port_input.setText(str(PEANUTSHELL_PORT))
            self.custom_host_input.setVisible(False)
            self.port_input.setEnabled(False)
        elif server_type == "本地服务器":
            self.port_input.setText(str(SERVER_PORT))
            self.custom_host_input.setVisible(False)
            self.custom_host_input.setText("127.0.0.1")
            self.port_input.setEnabled(True)
        else:  # 自定义服务器
            self.port_input.setText(str(PEANUTSHELL_PORT))
            self.custom_host_input.setVisible(True)
            self.custom_host_input.setText("")
            self.port_input.setEnabled(True)

    def load_settings(self):
        """加载保存的设置"""
        username = self.settings.value("username", "")
        server_type = self.settings.value("server_type", "花生壳服务器")
        custom_host = self.settings.value("custom_host", "")
        port = self.settings.value("port", str(PEANUTSHELL_PORT))
        remember = self.settings.value("remember", False, type=bool)

        self.username_input.setText(username)
        if server_type in ["花生壳服务器", "本地服务器", "自定义服务器"]:
            self.server_combo.setCurrentText(server_type)
        if server_type == "自定义服务器":
            self.custom_host_input.setText(custom_host)
        self.port_input.setText(port)
        self.remember_check.setChecked(remember)

    def save_settings(self):
        """保存设置"""
        self.settings.setValue("username", self.username_input.text())
        self.settings.setValue("server_type", self.server_combo.currentText())
        self.settings.setValue("custom_host", self.custom_host_input.text())
        self.settings.setValue("port", self.port_input.text())
        self.settings.setValue("remember", self.remember_check.isChecked())

    def get_login_info(self):
        """获取登录信息"""
        server_type = self.server_combo.currentText()

        if server_type == "花生壳服务器":
            host = PEANUTSHELL_HOST
        elif server_type == "本地服务器":
            host = "127.0.0.1"
        else:  # 自定义服务器
            host = self.custom_host_input.text().strip()
            if not host:
                host = PEANUTSHELL_HOST

        port = int(self.port_input.text().strip())
        username = self.username_input.text().strip()

        # 保存设置
        if self.remember_check.isChecked():
            self.save_settings()

        return username, host, port

    def accept(self):
        """登录验证"""
        username = self.username_input.text().strip()
        host = ""

        server_type = self.server_combo.currentText()
        if server_type == "花生壳服务器":
            host = PEANUTSHELL_HOST
        elif server_type == "本地服务器":
            host = "127.0.0.1"
        else:
            host = self.custom_host_input.text().strip()

        port_text = self.port_input.text().strip()

        # 验证输入
        if not username:
            QMessageBox.warning(self, "输入错误", "用户名不能为空！")
            return

        if not host:
            QMessageBox.warning(self, "输入错误", "服务器地址不能为空！")
            return

        if not port_text.isdigit():
            QMessageBox.warning(self, "输入错误", "端口号必须是数字！")
            return

        port = int(port_text)
        if port < 1 or port > 65535:
            QMessageBox.warning(self, "输入错误", "端口号必须在1-65535之间！")
            return

        super().accept()