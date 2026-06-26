# 发送代码/配置给对方Bot

## 核心原则
**用纯文本代码块，不用文件附件。** 文件附件在bot之间不可靠，对方可能收不到。

## 发送流程

### 1. 准备内容
把每个文件的内容写到 /tmp/ 下的临时文件：

```python
write_file(path="/tmp/msg1_soul.md", content="SOUL.md的内容...")
write_file(path="/tmp/msg2_script.py", content="脚本内容...")
```

### 2. 用 execute_code 批量发送
```python
import subprocess, time

files = [
    ("/tmp/msg1.md", "【1/4】SOUL.md："),
    ("/tmp/msg2.py", "【2/4】msg_to_bot.py："),
]

for fpath, header in files:
    with open(fpath) as f:
        content = f.read()
    msg = f"{header}\n\n```\n{content}\n```"
    result = subprocess.run(
        ["python3", "~/.hermes/scripts/msg_to_bot.py", msg],
        capture_output=True, text=True
    )
    print(f"Sent {fpath}: {result.stdout.strip()}")
    time.sleep(2)  # 避免限流
```

### 3. 发完后发一条汇总
```bash
python3 ~/.hermes/scripts/msg_to_bot.py "X条代码全部发完。部署位置：..."
```

## 注意事项
- 每条消息之间 sleep(2) 避免飞书限流
- 代码块用 ``` 包裹，飞书会渲染为代码格式
- 如果单条消息太长（>4000字符），拆成多条发送
- 文件附件不可靠——bot之间文件可能无法同步
- **msg_to_bot.py 代码必须自包含**：对方可能没有 feishu-bot-to-bot-communication skill，发送的脚本必须把 send_at_message 函数内联，不能依赖外部 SCRIPT_DIR
- **提醒对方改凭据**：发送的代码里 APP_ID/APP_SECRET 要提醒对方改成自己的

## 给对方部署完整4件套的模板

当需要给另一个bot部署双bot通信时，发以下4条消息：

1. **SOUL.md** — 完整内容，包含绝对规则、对方bot信息、工作流程
2. **config.yaml** — channel_prompts + group_rules 片段，提醒对方确认 feishu 的实际路径（可能是 `platforms.feishu.extra`）
3. **msg_to_bot.py** — 自包含脚本（send_at_message 内联），提醒改 APP_ID/APP_SECRET
4. **feishu_poll_daemon.py 增量** — check_retry + mark_all_replied + load/save_sent_log

每条用 `[N/4]` 标号，最后发一条部署步骤汇总。
