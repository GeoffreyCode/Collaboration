"""
样式表模块
定义了应用程序的全局样式
"""

# 默认样式表
DEFAULT_STYLE = """
/* 全局样式 */
QMainWindow {
    background-color: #f0f0f0;
}

QWidget {
    font-family: "Microsoft YaHei", "SimHei", "Segoe UI", sans-serif;
    font-size: 10pt;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
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

QLineEdit {
    padding: 6px;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    background-color: white;
}

QTextEdit {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    background-color: white;
    padding: 5px;
}

QLabel {
    color: #2c3e50;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #bdc3c7;
    border-radius: 5px;
    margin-top: 1ex;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}

QTableWidget {
    gridline-color: #bdc3c7;
    alternate-background-color: #ecf0f1;
    selection-background-color: #3498db;
    selection-color: white;
}

QTabWidget::pane {
    border: 1px solid #bdc3c7;
    border-radius: 5px;
}

QTabBar::tab {
    background-color: #ecf0f1;
    color: #2c3e50;
    padding: 8px 16px;
    border: 1px solid #bdc3c7;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 2px solid white;
}

QTabBar::tab:hover {
    background-color: #d5dbdb;
}

QMenuBar {
    background-color: #2c3e50;
    color: white;
    spacing: 3px;
}

QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
}

QMenuBar::item:selected {
    background: #34495e;
}

QMenuBar::item:pressed {
    background: #3d566e;
}

QStatusBar {
    background-color: #34495e;
    color: white;
}

QProgressBar {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    text-align: center;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #2ecc71;
    width: 1px;
}

QCheckBox {
    spacing: 5px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #bdc3c7;
    background-color: white;
}

QCheckBox::indicator:checked {
    border: 1px solid #3498db;
    background-color: #3498db;
}

QComboBox {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 4px;
    background-color: white;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #bdc3c7;
}

QComboBox::down-arrow {
    image: url(down_arrow.png);  /* 这里需要实际的箭头图片 */
}

/* 特定组件样式 */
#startButton {
    background-color: #2ecc71;
    font-size: 11pt;
    font-weight: bold;
}

#startButton:hover {
    background-color: #27ae60;
}

#startButton:pressed {
    background-color: #219653;
}

#stopButton {
    background-color: #e74c3c;
    font-size: 11pt;
    font-weight: bold;
}

#stopButton:hover {
    background-color: #c0392b;
}

#stopButton:pressed {
    background-color: #a93226;
}

#restartButton {
    background-color: #f39c12;
    font-size: 11pt;
    font-weight: bold;
}

#restartButton:hover {
    background-color: #d35400;
}

#restartButton:pressed {
    background-color: #ba4a00;
}

/* 工具栏样式 */
QToolBar {
    background-color: #ecf0f1;
    border: 1px solid #bdc3c7;
    padding: 2px;
}

QToolBar QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 5px;
    margin: 1px;
}

QToolBar QToolButton:hover {
    background-color: #d5dbdb;
    border: 1px solid #bdc3c7;
}

/* 滚动条样式 */
QScrollBar:vertical {
    background-color: #ecf0f1;
    width: 15px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #bdc3c7;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95a5a6;
}

QScrollBar:horizontal {
    background-color: #ecf0f1;
    height: 15px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #bdc3c7;
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #95a5a6;
}
"""

# 深色主题样式表
DARK_STYLE = """
/* 深色主题 */
QMainWindow {
    background-color: #2c3e50;
}

QWidget {
    background-color: #34495e;
    color: #ecf0f1;
    font-family: "Microsoft YaHei", "SimHei", "Segoe UI", sans-serif;
    font-size: 10pt;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #21618c;
}

QPushButton:disabled {
    background-color: #7f8c8d;
    color: #bdc3c7;
}

QLineEdit {
    padding: 6px;
    border: 1px solid #7f8c8d;
    border-radius: 4px;
    background-color: #2c3e50;
    color: #ecf0f1;
}

QTextEdit {
    border: 1px solid #7f8c8d;
    border-radius: 4px;
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 5px;
}

QLabel {
    color: #ecf0f1;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #7f8c8d;
    border-radius: 5px;
    margin-top: 1ex;
    padding-top: 10px;
    color: #ecf0f1;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    color: #ecf0f1;
}

QTableWidget {
    gridline-color: #7f8c8d;
    background-color: #2c3e50;
    alternate-background-color: #3d566e;
    color: #ecf0f1;
    selection-background-color: #3498db;
    selection-color: #2c3e50;
}

QTabWidget::pane {
    border: 1px solid #7f8c8d;
    border-radius: 5px;
}

QTabBar::tab {
    background-color: #3d566e;
    color: #ecf0f1;
    padding: 8px 16px;
    border: 1px solid #7f8c8d;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #2c3e50;
    border-bottom: 2px solid #3498db;
}

QTabBar::tab:hover {
    background-color: #4a637d;
}

QMenuBar {
    background-color: #2c3e50;
    color: #ecf0f1;
    spacing: 3px;
}

QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
}

QMenuBar::item:selected {
    background: #34495e;
}

QMenuBar::item:pressed {
    background: #3d566e;
}

QStatusBar {
    background-color: #2c3e50;
    color: #ecf0f1;
}

QProgressBar {
    border: 1px solid #7f8c8d;
    border-radius: 4px;
    text-align: center;
    font-weight: bold;
    background-color: #2c3e50;
}

QProgressBar::chunk {
    background-color: #2ecc71;
    width: 1px;
}

QCheckBox {
    spacing: 5px;
    color: #ecf0f1;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    border: 1px solid #7f8c8d;
    background-color: #2c3e50;
}

QCheckBox::indicator:checked {
    border: 1px solid #3498db;
    background-color: #3498db;
}

QComboBox {
    border: 1px solid #7f8c8d;
    border-radius: 4px;
    padding: 4px;
    background-color: #2c3e50;
    color: #ecf0f1;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #7f8c8d;
}

#startButton {
    background-color: #2ecc71;
    font-size: 11pt;
    font-weight: bold;
}

#startButton:hover {
    background-color: #27ae60;
}

#stopButton {
    background-color: #e74c3c;
    font-size: 11pt;
    font-weight: bold;
}

#stopButton:hover {
    background-color: #c0392b;
}

#restartButton {
    background-color: #f39c12;
    font-size: 11pt;
    font-weight: bold;
}

#restartButton:hover {
    background-color: #d35400;
}

/* 工具栏样式 */
QToolBar {
    background-color: #3d566e;
    border: 1px solid #7f8c8d;
    padding: 2px;
}

QToolBar QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 5px;
    margin: 1px;
    color: #ecf0f1;
}

QToolBar QToolButton:hover {
    background-color: #4a637d;
    border: 1px solid #7f8c8d;
}

/* 滚动条样式 */
QScrollBar:vertical {
    background-color: #3d566e;
    width: 15px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #7f8c8d;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95a5a6;
}

QScrollBar:horizontal {
    background-color: #3d566e;
    height: 15px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #7f8c8d;
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #95a5a6;
}
"""