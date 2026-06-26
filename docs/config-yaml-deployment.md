1|# Config.yaml channel_prompts Deployment
2|
3|## Problem
4|`hermes config set feishu.channel_prompts.X` writes to the wrong location (top-level `channel_prompts: {}` instead of under `feishu:` or `platforms.feishu.extra:`).
5|
6|## Solution: Python pathlib replace
7|
8|```python
9|import pathlib
10|p = pathlib.Path.home() / '.hermes/config.yaml'
11|t = p.read_text()
12|old = 'default_group_policy: open'
13|new = '''default_group_policy: open
14|    channel_prompts:
15|      oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx: |
16|        【绝对规则 - 违反即失败】
17|        在本群的所有输出必须通过脚本发送，禁止直接回复！
18|        执行方式：python3 ~/.hermes/scripts/msg_to_bot.py 消息内容
19|        例外：用户明确说不用@对方时才可直接回复。'''
20|if 'channel_prompts' in t:
21|    print('already exists')
22|else:
23|    p.write_text(t.replace(old, new, 1))
24|    print('done')
25|```
26|
27|## Key Points
28|- Always check actual config.yaml structure first: `grep -n 'feishu\|extra\|channel_prompts' ~/.hermes/config.yaml`
29|- Some installations use `platforms.feishu.extra:` (not top-level `feishu:`)
30|- `hermes config set` is unreliable for nested keys — use manual file editing
31|- After editing, restart gateway from external shell: `hermes gateway restart`
32|- Gateway cannot restart itself from inside (SIGTERM propagation)
33|
34|## Alternative: sed (less reliable for multi-line)
35|```bash
36|sed -i '/default_group_policy: open/a\    channel_prompts:\n      oc_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx: |\n        规则文本' ~/.hermes/config.yaml
37|```
38|Python is more reliable for multi-line YAML insertions.
39|