#!/bin/zsh

# 切换到脚本所在目录
cd "$(dirname "$0")" || exit 1

echo "[1/4] 检查/创建虚拟环境 .venv ..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv || { echo "创建虚拟环境失败，请确认已安装 Python3"; read -r; exit 1; }
fi

echo "[2/4] 激活虚拟环境 ..."
source .venv/bin/activate || { echo "激活虚拟环境失败"; read -r; exit 1; }

echo "[3/4] 安装依赖（首次运行会较慢） ..."
python3 -m pip3 install --upgrade pip3 >/dev/null 2>&1
pip3 install -r requirements.txt || { echo "依赖安装失败"; read -r; exit 1; }

echo "[4/4] 启动应用： http://localhost:8501 ..."
exec python3 -m streamlit run app.py --server.port 8501 --server.headless false


