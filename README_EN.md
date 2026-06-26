# 🤖 Feishu Bot-to-Bot Communication Complete Solution

Enable multiple bots in Feishu groups to communicate with each other, send/receive messages and files.

## Background

Feishu restricts bots to only receive **@mentioned messages** and **cannot receive messages from other bots**. This solution breaks through these limitations with a three-layer mechanism.

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

```bash
# 1. Install dependencies
pip install requests

# 2. Configure environment
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"

# 3. Start poll daemon
python3 scripts/feishu_poll_daemon.py &

# 4. Send a message
python3 scripts/send_at_message.py "Hello, Bot!"
```

## License

MIT