# 🤖 Hermes 飞书 Bot-to-Bot 通信模块

> 这是 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的飞书平台扩展模块，让 Hermes 能够在飞书群聊中与其他机器人相互通信。

## 🎯 适用场景

- **Hermes 多实例协作**：多个 Hermes Agent 在同一飞书群中协同工作
- **Bot-to-Bot 对话**：突破飞书限制，实现机器人之间的直接通信
- **文件共享**：机器人之间可以发送和接收文件

## 背景

飞书默认限制：机器人只能接收**@自己的消息**，且**无法收到其他机器人发的消息**。本模块通过三层机制彻底突破这些限制，专门为 Hermes Agent 设计。

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

### 方式一：作为 Hermes 插件使用（推荐）

本模块已集成到 Hermes Agent 中。只需配置飞书平台即可自动启用：

```bash
# 1. 安装 Hermes Agent
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. 配置飞书平台
hermes gateway setup

# 3. 启动 Hermes（自动启用 Bot-to-Bot 通信）
hermes gateway run
```

### 方式二：独立使用

```bash
# 1. 克隆仓库
git clone https://github.com/nononoworker/feishu-bot-to-bot.git
cd feishu-bot-to-bot

# 2. 安装依赖
pip install requests

# 3. 配置环境变量
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"

# 4. 启动轮询守护进程
python3 scripts/feishu_poll_daemon.py &

# 5. 发送消息
python3 scripts/msg_to_bot.py "你好，Bot！"
```

## 权限要求

对方机器人需开通 `im:message.group_at_msg.include_bot:readonly` 权限，且 `FEISHU_ALLOW_BOTS` 配置为 `mentions` 或 `all`。

## 许可

MIT

## 相关项目

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) - 开源 AI 代理框架
- [Hermes 飞书集成文档](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu) - 官方飞书平台配置指南