# 给对方Bot部署双Bot通信的完整流程

## 部署前确认

在发送代码之前，先确认对方的环境：
- 对方的 config.yaml 里 feishu 的实际路径（可能是 `feishu:` 或 `platforms.feishu.extra:`）
- 对方的 APP_ID 和 APP_SECRET 来源（环境变量 or 硬编码 in poll_daemon）

让对方运行：
```bash
grep -n "feishu\|extra\|channel_prompts\|group_rules" ~/.hermes/config.yaml | head -20
```

## 4件套部署清单

### 1. SOUL.md
直接发完整内容，让对方写入 `~/.hermes/SOUL.md`。

### 2. config.yaml channel_prompts
⚠️ **hermes config set 写入位置不可控**，不要依赖它。

最可靠的方式：让对方 `vi ~/.hermes/config.yaml` 手动插入。

如果对方的 Hermes agent 安全限制阻止编辑 config.yaml（报 "Refusing to write to Hermes config file"），必须让人类用户手动操作。

插入位置：找到 `extra:` 字段（通常在 `platforms.feishu.extra:` 下），在 `group_rules:` 前面插入：
```yaml
      channel_prompts:
        oc_08d2a8d6581aea4bc373af6e3ef8c303: |
          【绝对规则 - 违反即失败】
          在本群的所有输出必须通过脚本发送，禁止直接回复！
          执行方式：python3 ~/.hermes/scripts/msg_to_bot.py 消息内容
          例外：用户明确说不用@对方时才可直接回复。
```

### 3. msg_to_bot.py
**必须自包含**——把 send_at_message 函数内联，不依赖外部 SCRIPT_DIR。

⚠️ **APP_SECRET 问题**：对方的 `FEISHU_APP_SECRET` 环境变量通常为空！
指导对方获取 secret：
```bash
# 方法1：从 poll_daemon 抄
grep APP_SECRET ~/.hermes/scripts/feishu_poll_daemon.py

# 方法2：检查环境变量
env | grep FEISHU

# 方法3：从 config.yaml 找
grep -i "app_secret\|secret" ~/.hermes/config.yaml
```

找到后硬编码到 msg_to_bot.py 的 get_token() 函数里。

### 4. feishu_poll_daemon 增量
发送 check_retry + mark_all_replied + load/save_sent_log 函数代码。
提醒对方在主循环末尾加 `check_retry(state)`，收到对方消息时调 `mark_all_replied()`。

## 部署后验证（3项测试）

发完代码后，让对方测试3项功能：

```
请测试你的双Bot通信功能是否正常：
1. 用 msg_to_bot.py 给我发一条带@的消息
2. 确认 feishu_poll_daemon.py 在运行，能收到我发的消息
3. 检查 ~/.hermes/logs/sent_messages.jsonl 是否有发送日志
```

我方检查：
- feishu_poll.log 是否收到对方的 @消息 → 测试1通过
- 对方回复确认3项都OK → 测试2通过
- 我方发消息后故意不回复60秒，检查对方 poll_daemon.log 是否触发重试 → 测试3通过

### ⚠️ 部署后持续合规检查（重要！）

**问题**：对方通过3项测试后，后续消息可能不走 `msg_to_bot.py`，而是直接回复（不带@）。对方的 Hermes agent 在处理复杂任务时，可能"忘记"用脚本，回退到默认的直接回复模式。

**检测方法**：检查轮询日志中对方消息的 `msg_type`：
- `post` 类型 + 包含 `{"tag":"at","user_id":"..."}` → ✅ 走了 msg_to_bot.py
- `text` 类型、无 at 标签 → ❌ 直接回复，违反规则

```bash
# 检查最近10条对方消息是否带@
tail -10 ~/.hermes/feishu_poll_queue.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    if d.get('sender_id') == 'cli_YOUR_APP_ID':  # 对方bot的app_id
        has_at = '@' in d.get('text', '') or 'at' in d.get('content', '')
        status = '✅' if has_at else '❌ 直接回复!'
        print(f\"{status} {d['msg_type']}: {d.get('text', '')[:80]}\")
"
```

**处理**：发现对方直接回复时，立即通知对方纠正：
```
你的回复没有@我！请用 msg_to_bot.py 发送，不要直接回复。
```

### 对方服务器安全限制

对方的 Hermes agent 可能拦截 `pkill`、`kill`、`rm -rf` 等敏感命令，报 "Command Approval Required"。这是对方的安全策略，无法绕过。

**解决**：指导对方人类用户手动执行被拦截的命令，不要反复尝试自动化。例如：
```
需要您手动执行：sudo kill -9 <PID>
```

## 指导对方排查问题的工作流

**原则：一个一个问题处理，不要一次性丢出所有问题。**

当对方有多个问题需要排查时：
1. 先解决第一个问题，等对方确认完成后
2. 再进入下一个问题
3. 不要一次列出所有问题让对方自行处理

**原因**：对方的 agent 可能超时掉线、安全拦截命令、或误解指示。一次只给一个任务，可以及时发现和纠正偏差。

**对方 agent 误分析时**：如果对方把简单问题复杂化（如分析出无关的 /opposite 功能），明确告诉对方"不用管X，只需要做Y"，拉回正轨。

## 常见卡点及解决

| 卡点 | 原因 | 解决 |
|------|------|------|
| msg_to_bot.py 发送失败 | APP_SECRET 为空 | 从 poll_daemon 或 config.yaml 获取后硬编码 |
| hermes config set 写错位置 | config.yaml 结构不同 | 让对方 vi 手动编辑 |
| Hermes 安全限制拦截 | agent 不能改 config.yaml | 让人类用户手动操作 |
| 对方发消息不@我 | msg_to_bot.py 没有 at 标签 | 确认 send_at_message 函数里有 {tag: at, user_id: ...} |
| 对方通过测试后回退直接回复 | agent 复杂任务时忘用脚本 | 用合规检查脚本检测，发现后立即提醒 |
| 对方 agent 超时掉线 | 长时间处理后断连 | 重发消息，简化指令，一个一个问题来 |
| 对方 agent 误分析架构 | 把简单问题复杂化 | 明确告诉对方"不用管X，只需要做Y" |
| 对方收不到文件附件 | bot 间文件不可靠 | 改用纯文本代码块 |
