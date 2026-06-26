# Hermes飞书适配器自动@mention分析 (2026-06-25)

## 问题
LLM有时忘记用 `msg_to_bot.py`，直接回复导致对方收不到消息。

## 适配器发送路径

```
LLM回复 → GatewayStreamConsumer 
  → adapter.send(chat_id, content, reply_to, metadata)
    → format_message(content)  # markdown格式化
    → truncate_message(formatted, MAX_MESSAGE_LENGTH)
    → _build_outbound_payload(chunk)  # markdown→text/post
    → _feishu_send_with_retry(chat_id, msg_type, payload, reply_to, metadata)
    → 飞书API
```

## 关键代码位置

### `_build_outbound_payload()` (adapter.py:4376)
```python
def _build_outbound_payload(self, content: str) -> tuple[str, str]:
    # markdown表格 → 强制text（post不渲染表格）
    if _MARKDOWN_TABLE_RE.search(content):
        text_payload = {"text": content}
        return "text", json.dumps(text_payload, ensure_ascii=False)
    # markdown提示 → post格式
    if _MARKDOWN_HINT_RE.search(content):
        return "post", _build_markdown_post_payload(content)
    # 默认 → text格式
    text_payload = {"text": content}
    return "text", json.dumps(text_payload, ensure_ascii=False)
```

**问题**：这个方法从不添加@mention，text格式的@标签被当普通文字。

### `send()` 方法 (adapter.py:1774)
```python
async def send(self, chat_id: str, content: str, reply_to=None, metadata=None):
    formatted = self.format_message(content)
    chunks = self.truncate_message(formatted, self.MAX_MESSAGE_LENGTH)
    for chunk in chunks:
        msg_type, payload = self._build_outbound_payload(chunk)
        response = await self._feishu_send_with_retry(
            chat_id=chat_id, msg_type=msg_type, payload=payload,
            reply_to=reply_to, metadata=metadata
        )
```

**注意**：`metadata` 参数被传递但未用于@mention。

## 解决方案：修改 `_build_outbound_payload()`

### 方案A：最小改动（推荐）
在 `_build_outbound_payload()` 开头添加群聊检测：

```python
def _build_outbound_payload(self, content: str, chat_id: str = None) -> tuple[str, str]:
    # 自动@mention：群聊+配置了bot mentions
    if chat_id and hasattr(self, '_group_bot_mentions'):
        mentions = self._group_bot_mentions.get(chat_id, [])
        if mentions:
            return "post", _build_post_with_mentions(content, mentions)
    
    # 原有逻辑...
    if _MARKDOWN_TABLE_RE.search(content):
        return "text", json.dumps({"text": content}, ensure_ascii=False)
    # ...
```

### 辅助函数 `_build_post_with_mentions()`
```python
def _build_post_with_mentions(content: str, mention_ids: list) -> str:
    """构建带@mention的post格式消息"""
    post_content = {
        "zh_cn": {
            "title": "",
            "content": [
                [{"tag": "text", "text": content}]
            ]
        }
    }
    # 在消息开头添加@mention
    at_elements = [{"tag": "at", "user_id": oid} for oid in mention_ids]
    post_content["zh_cn"]["content"][0] = at_elements + post_content["zh_cn"]["content"][0]
    return json.dumps(post_content, ensure_ascii=False)
```

### 配置读取
在 `_load_settings()` 中添加：
```python
group_bot_mentions = extra.get("group_bot_mentions", {})
# 存储到 settings
```

config.yaml 中添加：
```yaml
feishu:
  extra:
    group_bot_mentions:
      oc_08d2a8d6581aea4bc373af6e3ef8c303:
        - ou_8bdac7cdb8ff50d51b0dfbeffaf4c65d  # 对方bot open_id
```

## 为什么不用Hook系统

Hermes有 `HookRegistry` (gateway/hooks.py)，支持事件：
- `gateway:startup`, `session:start`, `session:end`
- `agent:start`, `agent:step`, `agent:end`
- `command:*` (wildcard)

**致命缺陷**：`agent:end` 在消息**已发送到飞书后**才触发：
```python
# gateway/run.py:9553
await self.hooks.emit("agent:end", {
    **hook_ctx,
    "response": (response or "")[:500],  # 此时消息已发送
})
```

Hook无法拦截或修改 outgoing 消息。

## 为什么不用 stream_consumer.py

`stream_consumer.py` 负责消费LLM输出并调用 `adapter.send()`。
- 消息编辑（edit-in-place）和最终发送走不同路径
- 批量消息合并逻辑复杂
- 改动面太大，容易引入bug

## 为什么不修改 gateway/run.py

`run.py` 是gateway主循环，调用 `_run_agent()` 后处理响应。
- 响应已经过stream_consumer处理
- 在此处拦截需要重写消息发送逻辑
- 改动面太大

## 最小改动点

`adapter.py` 的 `_build_outbound_payload()` 是所有出站消息的必经之路：
- 所有消息类型（text, post, file, image）都经过这里
- 改动最小（~20行）
- 最安全（不影响其他平台）
- 可通过config.yaml配置

## 私聊 vs 群聊的chat_id区分

修改`send()`方法时，可以通过chat_id前缀判断消息类型：
- **群聊**：chat_id以 `oc_` 开头（如 `oc_08d2a8d6581aea4bc373af6e3ef8c303`）
- **私聊**：chat_id是 `ou_xxx`（open_id）或 `feishu_user_id:xxx`

```python
# 在send()方法开头添加判断
async def send(self, chat_id, content, reply_to=None, metadata=None):
    # 私聊 → 原样发送，完全不变
    if not chat_id.startswith("oc_"):
        return await _original_send(...)
    
    # 群聊 → 自动加@mention
    if needs_auto_mention(chat_id, content):
        content = add_bot_mentions(content, chat_id)
    return await _original_send(...)
```

**私聊完全不受影响**——`oc_` 判断确保改动只作用于群聊。

## 接收侧验证（2026-06-25实测）

当前配置 `require_mention: false` + `allow_bots: all` **已能收到对方bot的无@消息**。
实测：轮询日志中"验证码还关闭着，要恢复吗？"就是无@的bot消息，被正确接收。

## 发送侧验证（2026-06-25实测）

发送的消息中**5条里只有1条带@**（1/20%）。
问题确认：LLM有时直接回复，不用 `msg_to_bot.py`。

## 修改后需要验证
1. 群聊消息自动带@mention
2. 私聊消息不受影响
3. 文本/post格式正确
4. 表格内容不被破坏
5. 文件/图片消息不受影响
