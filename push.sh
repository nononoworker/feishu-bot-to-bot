#!/bin/bash
# 推送代码到GitHub
# 用法: bash push.sh YOUR_GITHUB_TOKEN

if [ -z "$1" ]; then
    echo "用法: bash push.sh YOUR_GITHUB_TOKEN"
    exit 1
fi

TOKEN=$1

cd ~/feishu-bot-to-bot
git branch -M main
git remote add origin "https://nononoworker:${TOKEN}@github.com/nononoworker/feishu-bot-to-bot.git" 2>/dev/null || git remote set-url origin "https://nononoworker:${TOKEN}@github.com/nononoworker/feishu-bot-to-bot.git"
git push -u origin main --force

echo "✅ 推送完成！"
echo "仓库地址: https://github.com/nononoworker/feishu-bot-to-bot"
