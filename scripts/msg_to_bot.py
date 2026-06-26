#!/usr/bin/env python3
"""
快捷发消息给对方bot（自动带@）+ 记录发送日志用于自动重试
用法：
  python3 msg_to_bot.py "消息内容"
  python3 msg_to_bot.py --file /path/to/file "说明文字"
"""

import sys
import os
import subprocess
import json
import time

SCRIPT_DIR = os.path.expanduser("~/.hermes/skills/software-development/feishu-bot-to-bot-communication/scripts")
SENT_LOG = os.path.expanduser("~/.hermes/logs/sent_messages.jsonl")


def log_sent(text, msg_type="text"):
    """记录发送的消息，用于自动重试"""
    os.makedirs(os.path.dirname(SENT_LOG), exist_ok=True)
    entry = {
        "text": text,
        "type": msg_type,
        "sent_at": int(time.time()),
        "replied": False
    }
    with open(SENT_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def send_text(text):
    """发送带@的文本消息"""
    subprocess.run([
        "python3", f"{SCRIPT_DIR}/send_at_message.py", text
    ])
    log_sent(text, "text")


def send_file(file_path, description=""):
    """发送文件（先@再发文件）"""
    subprocess.run([
        "python3", f"{SCRIPT_DIR}/send_file_with_notice.py", file_path, description
    ])
    log_sent(f"[文件] {description}", "file")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 msg_to_bot.py '消息内容'")
        print("  python3 msg_to_bot.py --file /path/to/file '说明文字'")
        sys.exit(1)
    
    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("缺少文件路径")
            sys.exit(1)
        file_path = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else f"请查收: {os.path.basename(file_path)}"
        send_file(file_path, description)
    else:
        text = " ".join(sys.argv[1:])
        send_text(text)


if __name__ == "__main__":
    main()
