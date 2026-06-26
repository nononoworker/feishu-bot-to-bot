1|# 给对方Bot部署双Bot通信的完整流程
2|
3|## 部署前确认
4|
5|在发送代码之前，先确认对方的环境：
6|- 对方的 config.yaml 里 feishu 的实际路径（可能是 `feishu:` 或 `platforms.feishu.extra:`）
7|- 对方的 APP_ID 和 APP_SECRET 来源（环境变量 or 硬编码 in poll_daemon）
8|
9|让对方运行：
10|```bash
11|grep -n "feishu\|extra\|channel_prompts\|group_rules" ~/.hermes/config.yaml | head -20
12|```
13|
14|## 4件套部署清单
15|
16|### 1. SOUL.md
17|直接发完整内容，让对方写入 `~/.hermes/SOUL.md`。
18|
19|### 2. config.yaml channel_prompts
20|⚠️ **hermes config set 写入位置不可控**，不要依赖它。
21|
22|最可靠的方式：让对方 `vi ~/.hermes/config.yaml` 手动插入。
23|
24|如果对方的 Hermes agent 安全限制阻止编辑 config.yaml（报 "Refusing to write to Hermes config file"），必须让人类用户手动操作。
25|
26|插入位置：找到 `extra:` 字段（通常在 `platforms.feishu.extra:` 下），在 `group_rules:` 前面插入：
27|```yaml
28|      channel_prompts:
29|        oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx: |
30|          【绝对规则 - 违反即失败】
31|          在本群的所有输出必须通过脚本发送，禁止直接回复！
32|          执行方式：python3 ~/.hermes/scripts/msg_to_bot.py 消息内容
33|          例外：用户明确说不用@对方时才可直接回复。
34|```
35|
36|### 3. msg_to_bot.py
37|**必须自包含**——把 send_at_message 函数内联，不依赖外部 SCRIPT_DIR。
38|
39|⚠️ **APP_SECRET 问题**：对方的 `FEISHU_APP_SECRET` 环境变量通常为空！
40|指导对方获取 secret：
41|```bash
42|# 方法1：从 poll_daemon 抄
43|grep APP_SECRET ~/.hermes/scripts/feishu_poll_daemon.py
44|
45|# 方法2：检查环境变量
46|env | grep FEISHU
47|
48|# 方法3：从 config.yaml 找
49|grep -i "app_secret\|secret" ~/.hermes/config.yaml
50|```
51|
52|找到后硬编码到 msg_to_bot.py 的 get_token() 函数里。
53|
54|### 4. feishu_poll_daemon 增量
55|发送 check_retry + mark_all_replied + load/save_sent_log 函数代码。
56|提醒对方在主循环末尾加 `check_retry(state)`，收到对方消息时调 `mark_all_replied()`。
57|
58|## 部署后验证（3项测试）
59|
60|发完代码后，让对方测试3项功能：
61|
62|```
63|请测试你的双Bot通信功能是否正常：
64|1. 用 msg_to_bot.py 给我发一条带@的消息
65|2. 确认 feishu_poll_daemon.py 在运行，能收到我发的消息
66|3. 检查 ~/.hermes/logs/sent_messages.jsonl 是否有发送日志
67|```
68|
69|我方检查：
70|- feishu_poll.log 是否收到对方的 @消息 → 测试1通过
71|- 对方回复确认3项都OK → 测试2通过
72|- 我方发消息后故意不回复60秒，检查对方 poll_daemon.log 是否触发重试 → 测试3通过
73|
74|### ⚠️ 部署后持续合规检查（重要！）
75|
76|**问题**：对方通过3项测试后，后续消息可能不走 `msg_to_bot.py`，而是直接回复（不带@）。对方的 Hermes agent 在处理复杂任务时，可能"忘记"用脚本，回退到默认的直接回复模式。
77|
78|**检测方法**：检查轮询日志中对方消息的 `msg_type`：
79|- `post` 类型 + 包含 `{"tag":"at","user_id":"..."}` → ✅ 走了 msg_to_bot.py
80|- `text` 类型、无 at 标签 → ❌ 直接回复，违反规则
81|
82|```bash
83|# 检查最近10条对方消息是否带@
84|tail -10 ~/.hermes/feishu_poll_queue.jsonl | python3 -c "
85|import sys, json
86|for line in sys.stdin:
87|    d = json.loads(line)
88|    if d.get('sender_id') == 'cli_YOUR_APP_ID':  # 对方bot的app_id
89|        has_at = '@' in d.get('text', '') or 'at' in d.get('content', '')
90|        status = '✅' if has_at else '❌ 直接回复!'
91|        print(f\"{status} {d['msg_type']}: {d.get('text', '')[:80]}\")
92|"
93|```
94|
95|**处理**：发现对方直接回复时，立即通知对方纠正：
96|```
97|你的回复没有@我！请用 msg_to_bot.py 发送，不要直接回复。
98|```
99|
100|### 对方服务器安全限制
101|
102|对方的 Hermes agent 可能拦截 `pkill`、`kill`、`rm -rf` 等敏感命令，报 "Command Approval Required"。这是对方的安全策略，无法绕过。
103|
104|**解决**：指导对方人类用户手动执行被拦截的命令，不要反复尝试自动化。例如：
105|```
106|需要您手动执行：sudo kill -9 <PID>
107|```
108|
109|## 指导对方排查问题的工作流
110|
111|**原则：一个一个问题处理，不要一次性丢出所有问题。**
112|
113|当对方有多个问题需要排查时：
114|1. 先解决第一个问题，等对方确认完成后
115|2. 再进入下一个问题
116|3. 不要一次列出所有问题让对方自行处理
117|
118|**原因**：对方的 agent 可能超时掉线、安全拦截命令、或误解指示。一次只给一个任务，可以及时发现和纠正偏差。
119|
120|**对方 agent 误分析时**：如果对方把简单问题复杂化（如分析出无关的 /opposite 功能），明确告诉对方"不用管X，只需要做Y"，拉回正轨。
121|
122|## 常见卡点及解决
123|
124|| 卡点 | 原因 | 解决 |
125||------|------|------|
126|| msg_to_bot.py 发送失败 | APP_SECRET 为空 | 从 poll_daemon 或 config.yaml 获取后硬编码 |
127|| hermes config set 写错位置 | config.yaml 结构不同 | 让对方 vi 手动编辑 |
128|| Hermes 安全限制拦截 | agent 不能改 config.yaml | 让人类用户手动操作 |
129|| 对方发消息不@我 | msg_to_bot.py 没有 at 标签 | 确认 send_at_message 函数里有 {tag: at, user_id: ...} |
130|| 对方通过测试后回退直接回复 | agent 复杂任务时忘用脚本 | 用合规检查脚本检测，发现后立即提醒 |
131|| 对方 agent 超时掉线 | 长时间处理后断连 | 重发消息，简化指令，一个一个问题来 |
132|| 对方 agent 误分析架构 | 把简单问题复杂化 | 明确告诉对方"不用管X，只需要做Y" |
133|| 对方收不到文件附件 | bot 间文件不可靠 | 改用纯文本代码块 |
134|