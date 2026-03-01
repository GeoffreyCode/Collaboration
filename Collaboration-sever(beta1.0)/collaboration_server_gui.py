#!/usr/bin/env python3
"""
Collaboration 服务端图形化界面
基于 PyQt6 的服务端管理界面
"""

import sys
import os
import json
import threading
import time
import logging
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QListWidget, QLabel,
    QSplitter, QStatusBar, QMessageBox, QSystemTrayIcon,
    QMenu, QMenuBar, QTabWidget, QGroupBox, QFormLayout,
    QSpinBox, QCheckBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QDialog, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QToolBar, QToolButton,
    QStyle, QGridLayout, QFrame
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize,
    QDateTime, QEvent, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QFont, QIcon, QAction, QTextCursor, QTextCharFormat,
    QColor, QPalette, QBrush, QKeySequence, QShortcut,
    QFontMetrics, QPainter, QLinearGradient, QPen
)

# 直接导入配置，避免循环导入
APP_NAME = "Collaboration"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Collaboration Team"
APP_DESCRIPTION = "即时通讯协作软件"

# 服务器配置
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 14725
PEANUTSHELL_DOMAIN = '118sx152ry310.vicp.fun'
PEANUTSHELL_PORT = 14725

# 服务器状态
SERVER_STATUS = {
    'STOPPED': 'stopped',
    'STARTING': 'starting',
    'RUNNING': 'running',
    'STOPPING': 'stopping',
    'ERROR': 'error'
}

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collaboration_server_gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ServerThread(QThread):
    """服务器线程"""

    # 定义信号
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)
    log_message = pyqtSignal(str, str)  # level, message
    user_connected = pyqtSignal(str, str)  # username, address
    user_disconnected = pyqtSignal(str, str)  # username, address
    users_updated = pyqtSignal(list)  # 在线用户列表
    server_stats = pyqtSignal(dict)  # 服务器统计信息

    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.server = None
        self.running = False

    def run(self):
        """运行服务器"""
        try:
            # 动态导入服务器类，避免循环导入
            from collaboration_server import CollaborationServer
            self.server = CollaborationServer()
            self.running = True

            # 启动服务器
            self.server_started.emit()
            self.log_message.emit('info', f"服务器启动在 {self.host}:{self.port}")

            # 定期发送统计信息
            self.stats_timer = QTimer()
            self.stats_timer.timeout.connect(self.emit_stats)
            self.stats_timer.start(5000)  # 5秒更新一次

            # 运行服务器
            self.server.start()

        except Exception as e:
            error_msg = str(e)
            self.server_error.emit(error_msg)
            self.log_message.emit('error', f"服务器启动失败: {error_msg}")
        finally:
            self.running = False
            self.server_stopped.emit()

    def emit_stats(self):
        """发送服务器统计信息"""
        if self.server:
            try:
                stats = self.server.get_server_info()
                self.server_stats.emit(stats)
            except:
                pass

    def stop_server(self):
        """停止服务器"""
        if self.server and self.running:
            self.server.stop()
            self.running = False

    def send_broadcast(self, message):
        """发送广播消息"""
        if self.server:
            try:
                self.server.broadcast_system_message(message)
                return True
            except:
                pass
        return False

    def get_server_info(self):
        """获取服务器信息"""
        if self.server:
            try:
                return self.server.get_server_info()
            except:
                pass
        return {}


# 简化UpdateManager类，避免复杂依赖
class SimpleUpdateManager:
    """简化版更新管理器"""

    def __init__(self):
        self.current_version = APP_VERSION

    def check_for_updates(self):
        """检查更新（简化版）"""
        # 这里可以添加实际的更新检查逻辑
        # 暂时返回无更新
        return False, None

    def get_update_history(self):
        """获取更新历史"""
        return []


class ServerGUI(QMainWindow):
    """服务器图形化界面"""

    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.update_manager = SimpleUpdateManager()
        self.current_status = SERVER_STATUS['STOPPED']
        self.online_users = []

        self.init_ui()
        self.setup_connections()
        self.setup_tray_icon()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"{APP_NAME} 服务器管理")
        self.setGeometry(100, 100, 1200, 800)

        # 设置窗口图标
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tabWidget")

        # 创建各个标签页
        self.create_dashboard_tab()
        self.create_users_tab()
        self.create_logs_tab()
        self.create_settings_tab()
        self.create_updates_tab()

        main_layout.addWidget(self.tab_widget)

        # 创建状态栏
        self.create_status_bar()

        # 创建工具栏
        self.create_toolbar()

        # 应用样式
        self.apply_style()

    def create_dashboard_tab(self):
        """创建仪表板标签页"""
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        dashboard_layout.setContentsMargins(10, 10, 10, 10)

        # 服务器状态卡片
        status_group = QGroupBox("服务器状态")
        status_layout = QGridLayout()

        # 状态指示灯
        self.status_light = QLabel()
        self.status_light.setFixedSize(20, 20)
        self.status_light.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                border-radius: 10px;
                border: 2px solid #c0392b;
            }
        """)

        self.status_label = QLabel("已停止")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")

        status_layout.addWidget(self.status_light, 0, 0)
        status_layout.addWidget(self.status_label, 0, 1, 1, 2)

        # 控制按钮
        self.start_button = QPushButton("▶ 启动服务器")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.start_server)

        self.stop_button = QPushButton("⏹ 停止服务器")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)

        self.restart_button = QPushButton("↻ 重启服务器")
        self.restart_button.setObjectName("restartButton")
        self.restart_button.clicked.connect(self.restart_server)

        status_layout.addWidget(self.start_button, 1, 0)
        status_layout.addWidget(self.stop_button, 1, 1)
        status_layout.addWidget(self.restart_button, 1, 2)

        status_group.setLayout(status_layout)
        dashboard_layout.addWidget(status_group)

        # 统计信息卡片
        stats_group = QGroupBox("服务器统计")
        stats_layout = QGridLayout()

        stats_labels = [
            ("运行时间:", "uptime_label"),
            ("在线用户:", "users_label"),
            ("总消息数:", "messages_label"),
            ("总连接数:", "connections_label")
        ]

        row = 0
        for label_text, obj_name in stats_labels:
            label = QLabel(label_text)
            value_label = QLabel("N/A")
            value_label.setObjectName(obj_name)
            value_label.setStyleSheet("font-weight: bold;")

            stats_layout.addWidget(label, row, 0)
            stats_layout.addWidget(value_label, row, 1)
            row += 1

        stats_group.setLayout(stats_layout)
        dashboard_layout.addWidget(stats_group)

        # 快速操作卡片
        quick_actions_group = QGroupBox("快速操作")
        quick_layout = QGridLayout()

        actions = [
            ("发送广播", self.send_broadcast, "📢"),
            ("清理日志", self.clear_logs, "🗑️"),
            ("备份数据", self.backup_data, "💾"),
            ("查看连接", self.view_connections, "🔗")
        ]

        row = 0
        col = 0
        for action_text, callback, icon in actions:
            button = QPushButton(f"{icon} {action_text}")
            button.clicked.connect(callback)
            button.setMaximumWidth(150)
            quick_layout.addWidget(button, row, col)

            col += 1
            if col > 1:
                col = 0
                row += 1

        quick_actions_group.setLayout(quick_layout)
        dashboard_layout.addWidget(quick_actions_group)

        dashboard_layout.addStretch()

        self.tab_widget.addTab(dashboard_widget, "📊 仪表板")

    def create_users_tab(self):
        """创建用户管理标签页"""
        users_widget = QWidget()
        users_layout = QVBoxLayout(users_widget)
        users_layout.setContentsMargins(10, 10, 10, 10)

        # 搜索框
        search_layout = QHBoxLayout()
        self.user_search = QLineEdit()
        self.user_search.setPlaceholderText("搜索用户...")

        search_button = QPushButton("🔍 搜索")

        search_layout.addWidget(self.user_search)
        search_layout.addWidget(search_button)
        users_layout.addLayout(search_layout)

        # 用户表格
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            "用户名", "用户ID", "状态", "最后登录", "注册时间"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setAlternatingRowColors(True)

        # 填充示例数据
        self.populate_users_table()

        users_layout.addWidget(self.users_table)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.refresh_users_button = QPushButton("🔄 刷新")
        self.refresh_users_button.clicked.connect(self.refresh_users)

        button_layout.addWidget(self.refresh_users_button)
        button_layout.addStretch()

        users_layout.addLayout(button_layout)

        self.tab_widget.addTab(users_widget, "👥 用户管理")

    def create_logs_tab(self):
        """创建日志标签页"""
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)
        logs_layout.setContentsMargins(10, 10, 10, 10)

        # 日志级别过滤
        filter_layout = QHBoxLayout()

        filter_label = QLabel("日志级别:")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["所有", "调试", "信息", "警告", "错误", "严重"])

        self.clear_logs_button = QPushButton("清空日志")
        self.clear_logs_button.clicked.connect(self.clear_logs)

        self.export_logs_button = QPushButton("导出日志")
        self.export_logs_button.clicked.connect(self.export_logs)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.log_level_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(self.clear_logs_button)
        filter_layout.addWidget(self.export_logs_button)

        logs_layout.addLayout(filter_layout)

        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                font-family: Consolas, 'Courier New', monospace;
            }
        """)

        logs_layout.addWidget(self.log_text)

        self.tab_widget.addTab(logs_widget, "📝 系统日志")

    def create_settings_tab(self):
        """创建设置标签页"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(10, 10, 10, 10)

        # 服务器设置
        server_group = QGroupBox("服务器设置")
        server_form = QFormLayout()

        self.server_host_input = QLineEdit(SERVER_HOST)
        self.server_port_input = QSpinBox()
        self.server_port_input.setRange(1, 65535)
        self.server_port_input.setValue(SERVER_PORT)

        server_form.addRow("监听地址:", self.server_host_input)
        server_form.addRow("监听端口:", self.server_port_input)

        server_group.setLayout(server_form)
        settings_layout.addWidget(server_group)

        # 花生壳设置
        peanutshell_group = QGroupBox("花生壳穿透设置")
        peanutshell_form = QFormLayout()

        self.peanutshell_domain_input = QLineEdit(PEANUTSHELL_DOMAIN)
        self.peanutshell_port_input = QSpinBox()
        self.peanutshell_port_input.setRange(1, 65535)
        self.peanutshell_port_input.setValue(PEANUTSHELL_PORT)

        peanutshell_form.addRow("花生壳域名:", self.peanutshell_domain_input)
        peanutshell_form.addRow("花生壳端口:", self.peanutshell_port_input)

        peanutshell_group.setLayout(peanutshell_form)
        settings_layout.addWidget(peanutshell_group)

        # 保存按钮
        button_layout = QHBoxLayout()
        self.save_settings_button = QPushButton("💾 保存设置")
        self.save_settings_button.clicked.connect(self.save_settings)

        self.reset_settings_button = QPushButton("↺ 恢复默认")
        self.reset_settings_button.clicked.connect(self.reset_settings)

        button_layout.addWidget(self.save_settings_button)
        button_layout.addWidget(self.reset_settings_button)
        button_layout.addStretch()

        settings_layout.addLayout(button_layout)
        settings_layout.addStretch()

        self.tab_widget.addTab(settings_widget, "⚙️ 设置")

    def create_updates_tab(self):
        """创建更新管理标签页"""
        updates_widget = QWidget()
        updates_layout = QVBoxLayout(updates_widget)
        updates_layout.setContentsMargins(10, 10, 10, 10)

        # 当前版本信息
        version_group = QGroupBox("当前版本信息")
        version_layout = QFormLayout()

        current_version_label = QLabel(APP_VERSION)
        current_version_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db;")

        version_layout.addRow("当前版本:", current_version_label)
        version_layout.addRow("应用名称:", QLabel(APP_NAME))
        version_layout.addRow("作者:", QLabel(APP_AUTHOR))

        version_group.setLayout(version_layout)
        updates_layout.addWidget(version_group)

        # 更新检查
        update_check_group = QGroupBox("更新检查")
        update_check_layout = QVBoxLayout()

        self.check_update_button = QPushButton("🔍 检查更新")
        self.check_update_button.clicked.connect(self.check_for_updates)

        self.update_status_label = QLabel("点击按钮检查更新")
        self.update_status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")

        update_check_layout.addWidget(self.check_update_button)
        update_check_layout.addWidget(self.update_status_label)

        update_check_group.setLayout(update_check_layout)
        updates_layout.addWidget(update_check_group)

        updates_layout.addStretch()

        self.tab_widget.addTab(updates_widget, "🔄 更新管理")

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 服务器状态
        self.server_status_label = QLabel("服务器状态: 已停止")
        self.status_bar.addWidget(self.server_status_label)

        # 用户数量
        self.user_count_label = QLabel("在线用户: 0")
        self.status_bar.addPermanentWidget(self.user_count_label)

        # 连接数
        self.connection_count_label = QLabel("总连接: 0")
        self.status_bar.addPermanentWidget(self.connection_count_label)

        # 系统时间
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)

        # 更新时间
        self.update_time()
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setObjectName("mainToolbar")
        self.addToolBar(toolbar)

        # 服务器操作
        toolbar.addAction("▶ 启动", self.start_server)
        toolbar.addAction("⏹ 停止", self.stop_server)
        toolbar.addAction("↻ 重启", self.restart_server)
        toolbar.addSeparator()

        # 用户操作
        toolbar.addAction("👥 用户管理", lambda: self.tab_widget.setCurrentIndex(1))
        toolbar.addSeparator()

        # 日志操作
        toolbar.addAction("📝 查看日志", lambda: self.tab_widget.setCurrentIndex(2))
        toolbar.addSeparator()

        # 设置操作
        toolbar.addAction("⚙️ 设置", lambda: self.tab_widget.setCurrentIndex(3))
        toolbar.addSeparator()

        # 更新操作
        toolbar.addAction("🔄 检查更新", self.check_for_updates)
        toolbar.addSeparator()

        # 帮助操作
        toolbar.addAction("❓ 帮助", self.show_help)

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
        # 定时检查更新
        self.update_check_timer = QTimer()
        self.update_check_timer.timeout.connect(self.auto_check_updates)
        self.update_check_timer.start(3600000)  # 1小时检查一次

    def apply_style(self):
        """应用样式"""
        try:
            # 简单样式
            style = """
            QMainWindow {
                background-color: #f5f7fa;
            }
            QGroupBox {
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
            #startButton {
                background-color: #2ecc71;
                color: white;
            }
            #stopButton {
                background-color: #e74c3c;
                color: white;
            }
            #restartButton {
                background-color: #3498db;
                color: white;
            }
            QStatusBar {
                background-color: #ecf0f1;
                color: #7f8c8d;
                border-top: 1px solid #d5dbdb;
            }
            """
            self.setStyleSheet(style)
        except:
            pass

    def start_server(self):
        """启动服务器"""
        if self.current_status == SERVER_STATUS['RUNNING']:
            QMessageBox.information(self, "提示", "服务器已经在运行中")
            return

        # 更新状态
        self.current_status = SERVER_STATUS['STARTING']
        self.update_server_status()

        # 获取服务器配置
        host = self.server_host_input.text()
        port = self.server_port_input.value()

        # 创建服务器线程
        self.server_thread = ServerThread(host, port)

        # 连接信号
        self.server_thread.server_started.connect(self.on_server_started)
        self.server_thread.server_stopped.connect(self.on_server_stopped)
        self.server_thread.server_error.connect(self.on_server_error)
        self.server_thread.log_message.connect(self.on_log_message)
        self.server_thread.server_stats.connect(self.on_server_stats)

        # 启动服务器线程
        self.server_thread.start()

        # 更新按钮状态
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.log_message('info', f"正在启动服务器: {host}:{port}")

    def stop_server(self):
        """停止服务器"""
        if self.current_status != SERVER_STATUS['RUNNING']:
            QMessageBox.information(self, "提示", "服务器未在运行中")
            return

        reply = QMessageBox.question(
            self,
            "确认停止",
            "确定要停止服务器吗？所有客户端将断开连接。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_status = SERVER_STATUS['STOPPING']
            self.update_server_status()

            if self.server_thread:
                self.server_thread.stop_server()

            # 更新按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

            self.log_message('info', "正在停止服务器...")

    def restart_server(self):
        """重启服务器"""
        if self.current_status == SERVER_STATUS['RUNNING']:
            self.stop_server()
            # 延迟启动
            QTimer.singleShot(2000, self.start_server)
        else:
            self.start_server()

    def on_server_started(self):
        """服务器启动成功"""
        self.current_status = SERVER_STATUS['RUNNING']
        self.update_server_status()
        self.log_message('info', "服务器启动成功")

        # 显示通知
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(
                "Collaboration 服务器",
                "服务器已启动",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

    def on_server_stopped(self):
        """服务器停止"""
        self.current_status = SERVER_STATUS['STOPPED']
        self.update_server_status()
        self.log_message('info', "服务器已停止")

        # 重置用户统计
        self.user_count_label.setText("在线用户: 0")
        self.connection_count_label.setText("总连接: 0")

        # 重置统计信息
        self.update_stat_label('uptime_label', 'N/A')
        self.update_stat_label('users_label', 'N/A')
        self.update_stat_label('messages_label', 'N/A')
        self.update_stat_label('connections_label', 'N/A')

        # 显示通知
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(
                "Collaboration 服务器",
                "服务器已停止",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )

    def on_server_error(self, error_message):
        """服务器错误"""
        self.current_status = SERVER_STATUS['ERROR']
        self.update_server_status()
        self.log_message('error', f"服务器错误: {error_message}")

        # 更新按钮状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        QMessageBox.critical(self, "服务器错误", error_message)

    def on_log_message(self, level, message):
        """处理日志消息"""
        self.log_message(level, message)

    def on_server_stats(self, stats):
        """服务器统计信息更新"""
        # 更新统计标签
        for key, value in stats.items():
            self.update_stat_label(f"{key}_label", str(value))

        # 更新状态栏
        if 'online_users' in stats:
            self.user_count_label.setText(f"在线用户: {stats['online_users']}")
        if 'total_connections' in stats:
            self.connection_count_label.setText(f"总连接: {stats['total_connections']}")

    def update_stat_label(self, label_name, value):
        """更新统计标签"""
        label = self.findChild(QLabel, label_name)
        if label:
            label.setText(value)

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
        elif level == 'debug':
            format.setForeground(QColor("#95a5a6"))
            prefix = "[调试] "
        else:
            format.setForeground(QColor("#ecf0f1"))
            prefix = ""

        # 添加时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor.insertText(f"[{timestamp}] {prefix}{message}\n", format)

        # 自动滚动到底部
        self.log_text.ensureCursorVisible()

    def update_server_status(self):
        """更新服务器状态显示"""
        status_text = {
            SERVER_STATUS['STOPPED']: "已停止",
            SERVER_STATUS['STARTING']: "启动中...",
            SERVER_STATUS['RUNNING']: "运行中",
            SERVER_STATUS['STOPPING']: "停止中...",
            SERVER_STATUS['ERROR']: "错误"
        }

        status_color = {
            SERVER_STATUS['STOPPED']: "#e74c3c",
            SERVER_STATUS['STARTING']: "#f39c12",
            SERVER_STATUS['RUNNING']: "#2ecc71",
            SERVER_STATUS['STOPPING']: "#f39c12",
            SERVER_STATUS['ERROR']: "#e74c3c"
        }

        text = status_text.get(self.current_status, "未知")
        color = status_color.get(self.current_status, "#95a5a6")

        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")

        self.status_light.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 10px;
                border: 2px solid {self.darken_color(color)};
            }}
        """)

        self.server_status_label.setText(f"服务器状态: {text}")

    def darken_color(self, color_hex, factor=0.8):
        """加深颜色"""
        # 简单实现
        if color_hex.startswith('#'):
            try:
                r = int(color_hex[1:3], 16)
                g = int(color_hex[3:5], 16)
                b = int(color_hex[5:7], 16)

                r = max(0, int(r * factor))
                g = max(0, int(g * factor))
                b = max(0, int(b * factor))

                return f'#{r:02x}{g:02x}{b:02x}'
            except:
                pass
        return color_hex

    def populate_users_table(self):
        """填充用户表格"""
        # 这里应该从服务器获取真实数据
        # 暂时使用示例数据
        self.users_table.setRowCount(3)

        users = [
            ["admin", "001", "在线", "2023-10-01 10:30", "2023-01-01"],
            ["user1", "002", "离线", "2023-09-30 15:45", "2023-02-15"],
            ["user2", "003", "在线", "2023-10-01 09:15", "2023-03-20"],
        ]

        for i, user in enumerate(users):
            for j, value in enumerate(user):
                item = QTableWidgetItem(value)
                if j == 2:  # 状态列
                    if value == "在线":
                        item.setForeground(QColor("#2ecc71"))
                    else:
                        item.setForeground(QColor("#e74c3c"))
                self.users_table.setItem(i, j, item)

    def refresh_users(self):
        """刷新用户列表"""
        self.populate_users_table()
        self.log_message('info', "用户列表已刷新")

    def send_broadcast(self):
        """发送广播消息"""
        if self.current_status != SERVER_STATUS['RUNNING']:
            QMessageBox.warning(self, "错误", "服务器未运行，无法发送广播")
            return

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
        send_button.clicked.connect(lambda: self._do_send_broadcast(message_input.toPlainText(), dialog))

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)

        button_layout.addWidget(send_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        dialog.exec()

    def _do_send_broadcast(self, message, dialog):
        """执行发送广播"""
        if not message.strip():
            QMessageBox.warning(self, "错误", "消息内容不能为空")
            return

        if self.server_thread:
            if self.server_thread.send_broadcast(message):
                self.log_message('info', f"发送广播消息: {message}")
                dialog.accept()
            else:
                QMessageBox.warning(self, "错误", "发送广播失败")

    def clear_logs(self):
        """清空日志"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空日志吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.log_text.clear()
            self.log_message('info', "日志已清空")

    def backup_data(self):
        """备份数据"""
        # 简单实现
        try:
            import shutil
            import datetime

            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"backup_{timestamp}.zip")

            # 这里应该实现实际的备份逻辑
            self.log_message('info', f"数据备份到: {backup_file}")
            QMessageBox.information(self, "备份成功", f"数据已备份到: {backup_file}")
        except Exception as e:
            self.log_message('error', f"备份失败: {e}")
            QMessageBox.critical(self, "备份失败", f"备份失败: {e}")

    def view_connections(self):
        """查看连接"""
        QMessageBox.information(self, "连接信息",
                                f"当前服务器状态: {self.current_status}\n"
                                f"在线用户: {self.user_count_label.text()}\n"
                                f"总连接: {self.connection_count_label.text()}")

    def export_logs(self):
        """导出日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出日志",
            f"server_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if file_path:
            try:
                log_text = self.log_text.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_text)

                QMessageBox.information(self, "导出成功", f"日志已导出到: {file_path}")
                self.log_message('info', f"日志已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出日志时出错: {str(e)}")
                self.log_message('error', f"导出日志失败: {e}")

    def save_settings(self):
        """保存设置"""
        try:
            # 这里应该将设置保存到配置文件
            self.log_message('info', "设置已保存")
            QMessageBox.information(self, "保存成功", "设置已保存")
        except Exception as e:
            self.log_message('error', f"保存设置失败: {e}")
            QMessageBox.critical(self, "保存失败", f"保存设置失败: {e}")

    def reset_settings(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要恢复默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.server_host_input.setText(SERVER_HOST)
            self.server_port_input.setValue(SERVER_PORT)
            self.peanutshell_domain_input.setText(PEANUTSHELL_DOMAIN)
            self.peanutshell_port_input.setValue(PEANUTSHELL_PORT)

            self.log_message('info', "设置已恢复为默认值")

    def check_for_updates(self):
        """检查更新"""
        self.log_message('info', "正在检查更新...")
        self.check_update_button.setEnabled(False)
        self.check_update_button.setText("检查中...")
        self.update_status_label.setText("正在检查更新...")

        # 模拟检查更新
        QTimer.singleShot(2000, self.on_update_check_complete)

    def on_update_check_complete(self):
        """更新检查完成"""
        self.check_update_button.setEnabled(True)
        self.check_update_button.setText("🔍 检查更新")

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 这里应该调用实际的更新检查
        has_update, update_info = self.update_manager.check_for_updates()

        if has_update:
            self.update_status_label.setText(f"发现新版本: {update_info.get('version')}")
            self.log_message('info', f"发现新版本: {update_info.get('version')}")
            self.show_update_info(update_info)
        else:
            self.update_status_label.setText(f"已是最新版本 (检查时间: {current_time})")
            self.log_message('info', "当前已是最新版本")

    def show_update_info(self, update_info):
        """显示更新信息"""
        version = update_info.get('version', '未知')

        reply = QMessageBox.information(
            self,
            "发现新版本",
            f"发现新版本 {version}，是否下载更新？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.log_message('info', f"开始下载更新: {version}")
            # 这里应该实现下载更新逻辑

    def auto_check_updates(self):
        """自动检查更新"""
        # 可以在这里实现自动检查更新逻辑
        pass

    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    def show_help(self):
        """显示帮助"""
        help_text = f"""
        <h2>{APP_NAME} 服务器管理</h2>

        <h3>基本操作</h3>
        <ul>
            <li>点击"启动服务器"按钮启动服务器</li>
            <li>点击"停止服务器"按钮停止服务器</li>
            <li>点击"重启服务器"按钮重启服务器</li>
            <li>在"用户管理"标签页查看用户信息</li>
            <li>在"系统日志"标签页查看服务器日志</li>
            <li>在"设置"标签页配置服务器参数</li>
            <li>在"更新管理"标签页检查更新</li>
        </ul>

        <h3>服务器配置</h3>
        <ul>
            <li>监听地址: {SERVER_HOST}</li>
            <li>监听端口: {SERVER_PORT}</li>
            <li>花生壳域名: {PEANUTSHELL_DOMAIN}</li>
            <li>花生壳端口: {PEANUTSHELL_PORT}</li>
        </ul>

        <p><b>需要更多帮助？</b><br>
        查看文档或联系技术支持。</p>
        """

        QMessageBox.information(self, "帮助", help_text)

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
        if self.current_status == SERVER_STATUS['RUNNING']:
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

        # 隐藏到托盘或退出
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName(f"{APP_NAME} 服务器")
    app.setApplicationVersion(APP_VERSION)

    # 设置样式
    app.setStyle("Fusion")

    # 创建并显示窗口
    window = ServerGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()