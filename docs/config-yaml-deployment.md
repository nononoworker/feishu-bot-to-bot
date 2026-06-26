# Config.yaml channel_prompts Deployment

## Problem
`hermes config set feishu.channel_prompts.X` writes to the wrong location (top-level `channel_prompts: {}` instead of under `feishu:` or `platforms.feishu.extra:`).

## Solution: Python pathlib replace

```python
import pathlib
p = pathlib.Path.home() / '.hermes/config.yaml'
t = p.read_text()
old = 'default_group_policy: open'
new = '''default_group_policy: open
    channel_prompts:
      oc_08d2a8d6581aea4bc373af6e3ef8c303: |
        【绝对规则 - 违反即失败】
        在本群的所有输出必须通过脚本发送，禁止直接回复！
        执行方式：python3 ~/.hermes/scripts/msg_to_bot.py 消息内容
        例外：用户明确说不用@对方时才可直接回复。'''
if 'channel_prompts' in t:
    print('already exists')
else:
    p.write_text(t.replace(old, new, 1))
    print('done')
```

## Key Points
- Always check actual config.yaml structure first: `grep -n 'feishu\|extra\|channel_prompts' ~/.hermes/config.yaml`
- Some installations use `platforms.feishu.extra:` (not top-level `feishu:`)
- `hermes config set` is unreliable for nested keys — use manual file editing
- After editing, restart gateway from external shell: `hermes gateway restart`
- Gateway cannot restart itself from inside (SIGTERM propagation)

## Alternative: sed (less reliable for multi-line)
```bash
sed -i '/default_group_policy: open/a\    channel_prompts:\n      oc_08d2a8d6581aea4bc373af6e3ef8c303: |\n        规则文本' ~/.hermes/config.yaml
```
Python is more reliable for multi-line YAML insertions.
