#!/bin/bash

# 自动化评测工具部署脚本

set -e

echo "🚀 开始部署自动化评测可视化工具..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装，请先安装docker-compose"
    exit 1
fi

# 创建数据目录
mkdir -p data

# 构建并启动服务
echo "📦 构建Docker镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
    echo "✅ 部署成功！"
    echo "🌐 访问地址: http://localhost:8501"
    echo "📊 应用名称: 自动化评测可视化工具"
    echo ""
    echo "📝 使用说明:"
    echo "1. 在浏览器中打开 http://localhost:8501"
    echo "2. 选择处理类型"
    echo "3. 上传Excel文件"
    echo "4. 开始处理并查看结果"
    echo ""
    echo "🔧 管理命令:"
    echo "查看日志: docker-compose logs -f"
    echo "停止服务: docker-compose down"
    echo "重启服务: docker-compose restart"
else
    echo "❌ 服务启动失败，请检查日志:"
    docker-compose logs
    exit 1
fi
