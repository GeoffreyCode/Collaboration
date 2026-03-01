[README.md](https://github.com/user-attachments/files/25659145/README.md)
# Collaboration - 即时通讯软件

一个带更新推送和服务端图形化界面的即时通讯软件。

## 功能特性

- 即时消息发送与接收
- 用户登录/登出
- 私聊功能
- 在线用户列表
- 服务端图形化管理界面
- 自动更新功能

## 项目结构

```
Collaboration/
├── collaboration_server.py       # 服务端主程序（命令行）
├── collaboration_server_gui.py   # 服务端图形化界面
├── collaboration_client.py       # 客户端主程序
├── config.py                     # 配置文件
├── update_manager.py             # 更新管理器
├── login_window.py               # 登录窗口
├── main_window.py                # 主聊天窗口
├── private_chat_window.py        # 私聊窗口
├── user_manager.py               # 用户管理
├── message_handler.py            # 消息处理器
├── styles.py                     # 样式表
├── resources/                    # 资源文件
│   ├── icons/                    # 图标
│   └── images/                   # 图片
├── updates/                      # 更新文件目录
│   ├── versions.json            # 版本信息
│   └── v1.0.1/                  # 版本目录
├── requirements.txt              # 依赖包
└── README.md                     # 项目说明
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行服务端

```bash
# 图形化界面
python collaboration_server_gui.py

# 命令行界面
python collaboration_server.py
```

## 运行客户端

```bash
python collaboration_client.py
```

## 更新功能

本软件支持自动更新，更新管理器会定期检查新版本并提供下载安装功能。

## 配置

通过 `config.py` 文件可以修改服务器配置、网络参数、安全设置等。

## 开发

本项目使用 Python 和 PyQt6 开发，遵循模块化设计原则，便于功能扩展和维护。

## 许可证

[在此处添加许可证信息]
