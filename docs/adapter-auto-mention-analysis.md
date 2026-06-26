1|# Hermes飞书适配器自动@mention分析 (2026-06-25)
2|
3|## 问题
4|LLM有时忘记用 `msg_to_bot.py`，直接回复导致对方收不到消息。
5|
6|## 适配器发送路径
7|
8|```
9|LLM回复 → GatewayStreamConsumer 
10|  → adapter.send(chat_id, content, reply_to, metadata)
11|    → format_message(content)  # markdown格式化
12|    → truncate_message(formatted, MAX_MESSAGE_LENGTH)
13|    → _build_outbound_payload(chunk)  # markdown→text/post
14|    → _feishu_send_with_retry(chat_id, msg_type, payload, reply_to, metadata)
15|    → 飞书API
16|```
17|
18|## 关键代码位置
19|
20|### `_build_outbound_payload()` (adapter.py:4376)
21|```python
22|def _build_outbound_payload(self, content: str) -> tuple[str, str]:
23|    # markdown表格 → 强制text（post不渲染表格）
24|    if _MARKDOWN_TABLE_RE.search(content):
25|        text_payload = {"text": content}
26|        return "text", json.dumps(text_payload, ensure_ascii=False)
27|    # markdown提示 → post格式
28|    if _MARKDOWN_HINT_RE.search(content):
29|        return "post", _build_markdown_post_payload(content)
30|    # 默认 → text格式
31|    text_payload = {"text": content}
32|    return "text", json.dumps(text_payload, ensure_ascii=False)
33|```
34|
35|**问题**：这个方法从不添加@mention，text格式的@标签被当普通文字。
36|
37|### `send()` 方法 (adapter.py:1774)
38|```python
39|async def send(self, chat_id: str, content: str, reply_to=None, metadata=None):
40|    formatted = self.format_message(content)
41|    chunks = self.truncate_message(formatted, self.MAX_MESSAGE_LENGTH)
42|    for chunk in chunks:
43|        msg_type, payload = self._build_outbound_payload(chunk)
44|        response = await self._feishu_send_with_retry(
45|            chat_id=chat_id, msg_type=msg_type, payload=payload,
46|            reply_to=reply_to, metadata=metadata
47|        )
48|```
49|
50|**注意**：`metadata` 参数被传递但未用于@mention。
51|
52|## 解决方案：修改 `_build_outbound_payload()`
53|
54|### 方案A：最小改动（推荐）
55|在 `_build_outbound_payload()` 开头添加群聊检测：
56|
57|```python
58|def _build_outbound_payload(self, content: str, chat_id: str = None) -> tuple[str, str]:
59|    # 自动@mention：群聊+配置了bot mentions
60|    if chat_id and hasattr(self, '_group_bot_mentions'):
61|        mentions = self._group_bot_mentions.get(chat_id, [])
62|        if mentions:
63|            return "post", _build_post_with_mentions(content, mentions)
64|    
65|    # 原有逻辑...
66|    if _MARKDOWN_TABLE_RE.search(content):
67|        return "text", json.dumps({"text": content}, ensure_ascii=False)
68|    # ...
69|```
70|
71|### 辅助函数 `_build_post_with_mentions()`
72|```python
73|def _build_post_with_mentions(content: str, mention_ids: list) -> str:
74|    """构建带@mention的post格式消息"""
75|    post_content = {
76|        "zh_cn": {
77|            "title": "",
78|            "content": [
79|                [{"tag": "text", "text": content}]
80|            ]
81|        }
82|    }
83|    # 在消息开头添加@mention
84|    at_elements = [{"tag": "at", "user_id": oid} for oid in mention_ids]
85|    post_content["zh_cn"]["content"][0] = at_elements + post_content["zh_cn"]["content"][0]
86|    return json.dumps(post_content, ensure_ascii=False)
87|```
88|
89|### 配置读取
90|在 `_load_settings()` 中添加：
91|```python
92|group_bot_mentions = extra.get("group_bot_mentions", {})
93|# 存储到 settings
94|```
95|
96|config.yaml 中添加：
97|```yaml
98|feishu:
99|  extra:
100|    group_bot_mentions:
101|      oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx:
102|        - ou_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 对方bot open_id
103|```
104|
105|## 为什么不用Hook系统
106|
107|Hermes有 `HookRegistry` (gateway/hooks.py)，支持事件：
108|- `gateway:startup`, `session:start`, `session:end`
109|- `agent:start`, `agent:step`, `agent:end`
110|- `command:*` (wildcard)
111|
112|**致命缺陷**：`agent:end` 在消息**已发送到飞书后**才触发：
113|```python
114|# gateway/run.py:9553
115|await self.hooks.emit("agent:end", {
116|    **hook_ctx,
117|    "response": (response or "")[:500],  # 此时消息已发送
118|})
119|```
120|
121|Hook无法拦截或修改 outgoing 消息。
122|
123|## 为什么不用 stream_consumer.py
124|
125|`stream_consumer.py` 负责消费LLM输出并调用 `adapter.send()`。
126|- 消息编辑（edit-in-place）和最终发送走不同路径
127|- 批量消息合并逻辑复杂
128|- 改动面太大，容易引入bug
129|
130|## 为什么不修改 gateway/run.py
131|
132|`run.py` 是gateway主循环，调用 `_run_agent()` 后处理响应。
133|- 响应已经过stream_consumer处理
134|- 在此处拦截需要重写消息发送逻辑
135|- 改动面太大
136|
137|## 最小改动点
138|
139|`adapter.py` 的 `_build_outbound_payload()` 是所有出站消息的必经之路：
140|- 所有消息类型（text, post, file, image）都经过这里
141|- 改动最小（~20行）
142|- 最安全（不影响其他平台）
143|- 可通过config.yaml配置
144|
145|## 私聊 vs 群聊的chat_id区分
146|
147|修改`send()`方法时，可以通过chat_id前缀判断消息类型：
148|- **群聊**：chat_id以 `oc_` 开头（如 `oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）
149|- **私聊**：chat_id是 `ou_xxx`（open_id）或 `feishu_user_id:xxx`
150|
151|```python
152|# 在send()方法开头添加判断
153|async def send(self, chat_id, content, reply_to=None, metadata=None):
154|    # 私聊 → 原样发送，完全不变
155|    if not chat_id.startswith("oc_"):
156|        return await _original_send(...)
157|    
158|    # 群聊 → 自动加@mention
159|    if needs_auto_mention(chat_id, content):
160|        content = add_bot_mentions(content, chat_id)
161|    return await _original_send(...)
162|```
163|
164|**私聊完全不受影响**——`oc_` 判断确保改动只作用于群聊。
165|
166|## 接收侧验证（2026-06-25实测）
167|
168|当前配置 `require_mention: false` + `allow_bots: all` **已能收到对方bot的无@消息**。
169|实测：轮询日志中"验证码还关闭着，要恢复吗？"就是无@的bot消息，被正确接收。
170|
171|## 发送侧验证（2026-06-25实测）
172|
173|发送的消息中**5条里只有1条带@**（1/20%）。
174|问题确认：LLM有时直接回复，不用 `msg_to_bot.py`。
175|
176|## 修改后需要验证
177|1. 群聊消息自动带@mention
178|2. 私聊消息不受影响
179|3. 文本/post格式正确
180|4. 表格内容不被破坏
181|5. 文件/图片消息不受影响
182|