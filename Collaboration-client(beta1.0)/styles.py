"""
样式表定义
"""

# 应用程序主样式
APP_STYLE = """
QMainWindow {
    background-color: #f5f7fa;
}

QWidget {
    background-color: #f5f7fa;
}

QTextEdit, QLineEdit, QListWidget {
    border: 1px solid #d1d9e6;
    border-radius: 5px;
    padding: 5px;
    background-color: white;
}

QTextEdit:focus, QLineEdit:focus {
    border: 2px solid #3498db;
}

QPushButton {
    border: none;
    padding: 8px 15px;
    border-radius: 5px;
    font-weight: bold;
}

QLabel {
    color: #2c3e50;
}

QStatusBar {
    background-color: #ecf0f1;
    color: #7f8c8d;
}
"""

# 按钮样式
BUTTON_STYLE = """
QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    font-weight: bold;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #21618c;
}

QPushButton:disabled {
    background-color: #bdc3c7;
    color: #7f8c8d;
}
"""

# 输入框样式
INPUT_STYLE = """
QLineEdit {
    border: 2px solid #d1d9e6;
    border-radius: 5px;
    padding: 8px;
    background-color: white;
    font-size: 14px;
}

QLineEdit:focus {
    border: 2px solid #3498db;
}

QLineEdit:disabled {
    background-color: #ecf0f1;
    color: #7f8c8d;
}
"""

# 列表样式
LIST_STYLE = """
QListWidget {
    background-color: white;
    border: 1px solid #d1d9e6;
    border-radius: 5px;
    padding: 5px;
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
"""

# 对话框样式
DIALOG_STYLE = """
QDialog {
    background-color: #f5f7fa;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #d1d9e6;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}
"""

# 菜单样式
MENU_STYLE = """
QMenuBar {
    background-color: #2c3e50;
    color: white;
}

QMenuBar::item {
    background-color: transparent;
    padding: 5px 10px;
}

QMenuBar::item:selected {
    background-color: #34495e;
}

QMenu {
    background-color: white;
    border: 1px solid #d1d9e6;
}

QMenu::item {
    padding: 5px 20px 5px 20px;
}

QMenu::item:selected {
    background-color: #3498db;
    color: white;
}
"""