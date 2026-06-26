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
export FEISHU_APP_SECRET="your...n
# 4. 启动轮询守护进程
python3 scripts/feishu_poll_daemon.py &

# 5. 发送消息
python3 scripts/msg_to_bot.py "你好，Bot！"
```

## 📋 完整部署步骤

### 前提条件

- ✅ 两个 Hermes Agent 实例（分别部署在不同服务器或同一服务器的不同端口）
- ✅ 两个飞书自建应用（每个 Hermes 实例对应一个）
- ✅ 一个飞书群聊（用于机器人间通信）

### 步骤 1：创建飞书自建应用

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 创建两个自建应用（例如：`Hermes-Bot-A` 和 `Hermes-Bot-B`）
3. 获取每个应用的 `APP_ID` 和 `APP_SECRET`
4. 为每个应用开通以下权限：
   - `im:message.group_at_msg.include_bot:readonly`（接收群消息）
   - `im:message:send_as_bot`（发送消息）

### 步骤 2：创建飞书群聊并添加机器人

1. 在飞书中创建一个新群聊（例如：`Bot-Communication`）
2. 将两个机器人（`Hermes-Bot-A` 和 `Hermes-Bot-B`）都添加到群聊中
3. 记录群聊的 `CHAT_ID`（可在飞书管理后台查看）

### 步骤 3：配置 Hermes 实例

**对于 Hermes-Bot-A：**
```bash
# 配置环境变量
export FEISHU_APP_ID="cli_xxxxxxxxxxxxxxxx"  # Bot-A 的 APP_ID
export FEISHU_APP_SECRET="your_bot_a_secret"
export FEISHU_CHAT_ID="oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 群聊 ID

# 配置 config.yaml
cat >> ~/.hermes/config.yaml << EOF
feishu:
  require_mention: false
  allow_bots: all
  group_rules:
    $FEISHU_CHAT_ID:
      policy: open
EOF

# 启动 Hermes
hermes gateway run
```

**对于 Hermes-Bot-B：**
```bash
# 配置环境变量
export FEISHU_APP_ID="cli_yyyyyyyyyyyyyyyy"  # Bot-B 的 APP_ID
export FEISHU_APP_SECRET="your_bot_b_secret"
export FEISHU_CHAT_ID="oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 同一个群聊 ID

# 配置 config.yaml（与 Bot-A 相同）
cat >> ~/.hermes/config.yaml << EOF
feishu:
  require_mention: false
  allow_bots: all
  group_rules:
    $FEISHU_CHAT_ID:
      policy: open
EOF

# 启动 Hermes
hermes gateway run
```

### 步骤 4：测试 Bot-to-Bot 通信

在群聊中发送消息：
```
@Hermes-Bot-A 请帮我查询天气
```

Bot-A 会收到消息并处理，然后通过 `msg_to_bot.py` 发送带 @ 的回复，Bot-B 也能收到。

## 权限要求

对方机器人需开通 `im:message.group_at_msg.include_bot:readonly` 权限，且 `FEISHU_ALLOW_BOTS` 配置为 `mentions` 或 `all`。

## 许可

MIT

## 相关项目

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) - 开源 AI 代理框架
- [Hermes 飞书集成文档](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu) - 官方飞书平台配置指南