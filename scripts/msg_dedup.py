#!/usr/bin/env python3
"""消息去重工具 - 持久化存储已处理的message_id

解决 feishu_poll_daemon.py 重启后重复处理历史消息的问题。
去重状态存在文件里，重启不丢失。

用法（在 feishu_poll_daemon.py 中）：
    from msg_dedup import is_processed, mark_processed, cleanup_old

    # 处理消息前
    if is_processed(message_id):
        continue  # 跳过已处理的消息

    # 处理完后
    mark_processed(message_id)

    # 定期清理（建议每天一次）
    cleanup_old(days=7)
"""
import json, os, time

DEDUP_FILE = os.path.expanduser('~/.hermes/logs/processed_msg_ids.json')

def load_processed():
    if os.path.exists(DEDUP_FILE):
        try:
            with open(DEDUP_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_processed(data):
    os.makedirs(os.path.dirname(DEDUP_FILE), exist_ok=True)
    with open(DEDUP_FILE, 'w') as f:
        json.dump(data, f)

def is_processed(msg_id):
    """检查消息是否已处理过"""
    data = load_processed()
    return msg_id in data

def mark_processed(msg_id):
    """标记消息为已处理"""
    data = load_processed()
    data[msg_id] = time.time()
    # 只保留最近1000条，防止文件无限增长
    if len(data) > 1000:
        sorted_items = sorted(data.items(), key=lambda x: x[1])
        data = dict(sorted_items[-1000:])
    save_processed(data)

def cleanup_old(days=7):
    """清理超过N天的记录"""
    data = load_processed()
    cutoff = time.time() - days * 86400
    data = {k: v for k, v in data.items() if v > cutoff}
    save_processed(data)
