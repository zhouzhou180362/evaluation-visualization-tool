#!/bin/bash

echo "🚀 自动化评测工具 - GitHub部署脚本"
echo "=================================="

# 检查Git状态
if [ ! -d ".git" ]; then
    echo "❌ 当前目录不是Git仓库"
    exit 1
fi

echo "📋 当前Git状态："
git status --short

echo ""
echo "📝 请按照以下步骤操作："
echo "1. 访问 https://github.com/new"
echo "2. 创建新仓库，名称建议：evaluation-visualization-tool"
echo "3. 选择 Public（公开）"
echo "4. 不要勾选 'Add a README file'"
echo "5. 点击 'Create repository'"
echo ""
echo "创建完成后，请提供您的GitHub用户名和仓库名："
echo ""

read -p "请输入您的GitHub用户名: " github_username
read -p "请输入仓库名称: " repo_name

if [ -z "$github_username" ] || [ -z "$repo_name" ]; then
    echo "❌ 用户名或仓库名不能为空"
    exit 1
fi

echo ""
echo "🔗 添加远程仓库..."
git remote add origin "https://github.com/$github_username/$repo_name.git"

echo "📤 推送代码到GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✅ 代码推送完成！"
echo "🌐 您的仓库地址：https://github.com/$github_username/$repo_name"
echo ""
echo "📋 接下来部署到Streamlit Cloud："
echo "1. 访问 https://share.streamlit.io/"
echo "2. 用GitHub账号登录"
echo "3. 点击 'New app'"
echo "4. 选择仓库：$repo_name"
echo "5. 设置 Main file path: app.py"
echo "6. 点击 'Deploy!'"
echo ""
echo "🎉 部署完成后，您将获得公网访问链接！"
