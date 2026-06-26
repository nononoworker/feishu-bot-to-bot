# 🤖 飞书 Bot-to-Bot 通信完整解决方案

让飞书群里的多个机器人能够相互通信、收发消息和文件。

## 背景

飞书默认限制：机器人只能接收**@自己的消息**，且**无法收到其他机器人发的消息**。本解决方案通过三层机制彻底突破这些限制。

## 架构

```
┌──────────────┐      ┌──────────────────┐      ┌──────────────┐
│  用户发消息   │ ───→ │  Gateway 自动@   │ ───→ │  对方Bot接收  │
└──────────────┘      └──────────────────┘      └──────────────┘
                                                       │
                                                       ▼
┌──────────────┐      ┌──────────────────┐      ┌──────────────┐
│  轮询接收回复  │ ←─── │  Poll Daemon轮询  │ ←─── │  对方回复消息  │
└──────────────┘      └──────────────────┘      └──────────────┘
```

## 三层通信机制

1. **发送侧自动@** — Gateway `adapter.send()` 检测群聊，自动发送带 `@mention` 的富文本(post)消息
2. **接收侧开放** — `require_mention: false` + `allow_bots: all` 配置，接收群里所有消息
3. **轮询守护进程** — 主动拉取消息，绕过飞书 webhook 投递限制

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `scripts/send_at_message.py` | 发送@消息到飞书群里的其他机器人 |
| `scripts/send_file_with_notice.py` | 发送文件，自动先发@通知 |
| `scripts/feishu_poll_daemon.py` | 群消息轮询器 + 文件自动下载 |
| `scripts/msg_dedup.py` | 消息去重，持久化存储已处理的 message_id |
| `scripts/msg_to_bot.py` | 快捷发消息给对方 bot（带@）+ 发送日志 |

## 快速开始

```bash
# 1. 安装依赖
pip install requests

# 2. 配置环境变量
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"

# 3. 启动轮询守护进程
python3 scripts/feishu_poll_daemon.py &

# 4. 发送消息
python3 scripts/send_at_message.py "你好，Bot！"
```

## 权限要求

对方机器人需开通 `im:message.group_at_msg.include_bot:readonly` 权限，且 `FEISHU_ALLOW_BOTS` 配置为 `mentions` 或 `all`。

## 许可

MIT