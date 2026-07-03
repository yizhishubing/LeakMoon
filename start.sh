#!/usr/bin/env bash
# LeakMoon 一键启动脚本
# 用法: bash start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "============================================"
echo "  校园网站敏感信息泄露巡检平台 - 启动中..."
echo "============================================"
echo ""

# 检查 MySQL
echo "[检查] MySQL..."
export PATH="/c/Program Files/MySQL/MySQL Server 8.4/bin:$PATH"
if mysql -u root -proot123456 -e "SELECT 1" --silent 2>/dev/null; then
    echo "  MySQL: 运行中"
else
    echo "  MySQL: 未运行，正在启动..."
    mysqld --defaults-file="/c/ProgramData/MySQL/MySQL Server 8.4/my.ini" --user=root --console &
    sleep 3
    echo "  MySQL: 已启动"
fi

# 检查 Redis
echo "[检查] Redis..."
if redis-cli -p 6379 ping 2>/dev/null | grep -q PONG; then
    echo "  Redis: 运行中"
else
    echo "  Redis: 未运行，正在启动..."
    redis-server --service-start 2>/dev/null || true
    echo "  Redis: 已启动"
fi

# 启动后端
echo ""
echo "[启动] 后端服务..."
cd "$BACKEND_DIR"
source venv/Scripts/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "  PID: $BACKEND_PID"

# 等待后端就绪
echo "  等待后端就绪..."
for i in $(seq 1 10); do
    if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
        echo "  后端就绪!"
        break
    fi
    sleep 1
done

# 启动前端
echo ""
echo "[启动] 前端服务..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
echo "  PID: $FRONTEND_PID"

echo ""
echo "============================================"
echo "  启动完成!"
echo "============================================"
echo "  前端:   http://localhost:5173"
echo "  后端:   http://localhost:8000/api/health"
echo "  文档:   http://localhost:8000/docs"
echo "============================================"
echo "  按 Ctrl+C 停止所有服务"
echo "============================================"

# 等待用户中断
wait
