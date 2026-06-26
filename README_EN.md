# 🤖 Hermes Feishu Bot-to-Bot Communication Module

> This is a Feishu platform extension module for [Hermes Agent](https://github.com/NousResearch/hermes-agent), enabling Hermes to communicate with other bots in Feishu group chats.

## 🎯 Use Cases

- **Hermes Multi-Instance Collaboration**: Multiple Hermes Agents working together in the same Feishu group
- **Bot-to-Bot Communication**: Break through Feishu limitations for direct bot-to-bot messaging
- **File Sharing**: Send and receive files between bots

## Background

Feishu restricts bots to only receive **@mentioned messages** and **cannot receive messages from other bots**. This module breaks through these limitations with a three-layer mechanism, specifically designed for Hermes Agent.

## Architecture

```
┌──────────────┐      ┌──────────────────┐      ┌──────────────┐
│  User sends   │ ───→ │  Gateway auto-@  │ ───→ │  Target Bot  │
└──────────────┘      └──────────────────┘      └──────────────┘
                                                       │
                                                       ▼
┌──────────────┐      ┌──────────────────┐      ┌──────────────┐
│  Poll replies  │ ←─── │  Poll Daemon    │ ←─── │  Bot replies  │
└──────────────┘      └──────────────────┘      └──────────────┘
```

## Three-Layer Mechanism

1. **Auto-mention on send** — Gateway `adapter.send()` detects group chats, auto-sends post messages with @mention
2. **Open receive** — `require_mention: false` + `allow_bots: all` config
3. **Poll daemon** — Actively pulls messages, bypassing webhook delivery limits

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/send_at_message.py` | Send @ messages to other bots in group |
| `scripts/send_file_with_notice.py` | Send files with prior @ notification |
| `scripts/feishu_poll_daemon.py` | Message poller + file auto-download |
| `scripts/msg_dedup.py` | Message deduplication with persistent storage |
| `scripts/msg_to_bot.py` | Quick message send with @ and logging |

## Quick Start

### Option 1: As a Hermes Plugin (Recommended)

This module is integrated into Hermes Agent. Simply configure the Feishu platform to enable it automatically:

```bash
# 1. Install Hermes Agent
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. Configure Feishu platform
hermes gateway setup

# 3. Start Hermes (Bot-to-Bot communication auto-enabled)
hermes gateway run
```

### Option 2: Standalone Usage

```bash
# 1. Clone the repository
git clone https://github.com/nononoworker/feishu-bot-to-bot.git
cd feishu-bot-to-bot

# 2. Install dependencies
pip install requests

# 3. Configure environment
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"

# 4. Start poll daemon
python3 scripts/feishu_poll_daemon.py &

# 5. Send a message
python3 scripts/msg_to_bot.py "Hello, Bot!"
```

## Permissions Required

The target bot needs `im:message.group_at_msg.include_bot:readonly` permission, and `FEISHU_ALLOW_BOTS` should be configured as `mentions` or `all`.

## License

MIT

## Related Projects

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) - Open-source AI agent framework
- [Hermes Feishu Integration Docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu) - Official Feishu platform configuration guide
