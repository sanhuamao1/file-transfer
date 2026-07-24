#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "==> 检查 Python"
command -v python3 >/dev/null 2>&1 || { echo "需要 Python 3，请先安装"; exit 1; }

echo "==> 创建虚拟环境"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate

echo "==> 安装依赖"
pip install -r requirements.txt -q

echo "==> 创建必要目录"
mkdir -p data

echo "==> 检查 .env"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  已从 .env.example 生成 .env，请编辑修改 ACCESS_CODE"
fi

echo ""
echo "==> 启动开发服务器 (http://localhost:5000)"
echo "    按 Ctrl+C 停止"
echo ""
ACCESS_CODE="${ACCESS_CODE:-$(grep ^ACCESS_CODE .env | cut -d= -f2)}" \
  python app.py
