"""
Collaboration 配置文件
"""

# 应用程序配置
APP_NAME = "Collaboration"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Collaboration Team"
APP_DESCRIPTION = "即时通讯协作软件"

# 服务器配置
SERVER_HOST = '0.0.0.0'  # 本地监听地址
SERVER_PORT = 14725      # 本地端口

# 花生壳HTTP穿透配置 - 修复这里
PEANUTSHELL_DOMAIN = '118sx152ry310.vicp.fun'
PEANUTSHELL_HOST = '118sx152ry310.vicp.fun'  # 新增，与DOMAIN相同
PEANUTSHELL_PORT = 45114  # 公网端口

# 网络配置
BUFFER_SIZE = 8192       # 缓冲区大小
ENCODING = 'utf-8'       # 编码格式
MAX_CLIENTS = 100        # 最大客户端数
HEARTBEAT_INTERVAL = 30  # 心跳包间隔（秒）
CONNECTION_TIMEOUT = 60  # 连接超时（秒）

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

# 服务器状态
SERVER_STATUS = {
    'STOPPED': 'stopped',
    'STARTING': 'starting',
    'RUNNING': 'running',
    'STOPPING': 'stopping',
    'ERROR': 'error'
}

# 更新配置
UPDATE_CONFIG = {
    'check_interval': 3600,
    'current_version': '1.0.0',
    'auto_check': True,
}

# 文件传输配置
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = ['.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.gif']

# 主题颜色
THEME_COLORS = {
    'light': {
        'primary': '#3498db',
        'secondary': '#2ecc71',
        'danger': '#e74c3c',
        'warning': '#f39c12',
        'dark': '#2c3e50',
        'light': '#ecf0f1',
        'background': '#ffffff',
        'text': '#2c3e50'
    },
    'dark': {
        'primary': '#2980b9',
        'secondary': '#27ae60',
        'danger': '#c0392b',
        'warning': '#e67e22',
        'dark': '#1a252f',
        'light': '#34495e',
        'background': '#2c3e50',
        'text': '#ecf0f1'
    }
}