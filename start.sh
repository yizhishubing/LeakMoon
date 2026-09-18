#!/usr/bin/env bash
# LeakMoon 一键启动脚本
# 用法: bash start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# 自动寻找空闲端口（8000-9000）
echo "[端口检测] 扫描 8000-9000..."
BACKEND_PORT=$(python "$SCRIPT_DIR/find_port.py" 2>/dev/null || echo "8000")
echo "后端端口: $BACKEND_PORT"
echo ""

echo "============================================"
echo "  校园网站敏感信息泄露巡检平台 - 启动中..."
echo "============================================"
echo ""

# 检查 MySQL
echo "[1/5] 检查 MySQL..."
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
echo ""
echo "[2/5] 检查 Redis..."
if redis-cli -p 6379 ping 2>/dev/null | grep -q PONG; then
    echo "  Redis: 运行中"
else
    echo "  Redis: 未运行，尝试启动..."
    redis-server --service-start 2>/dev/null || true
    echo "  Redis: 已启动"
fi

# 初始化数据库
echo ""
echo "[3/5] 初始化数据库..."
cd "$BACKEND_DIR"
source venv/Scripts/activate
python init_db.py

# 启动后端
echo ""
echo "[4/5] 启动后端服务 (端口: $BACKEND_PORT)..."
BACKEND_PORT=$BACKEND_PORT uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
echo "  PID: $BACKEND_PID"

# 等待后端就绪
echo "  等待后端就绪..."
for i in $(seq 1 10); do
    if curl -s "http://localhost:$BACKEND_PORT/api/health" >/dev/null 2>&1; then
        echo "  后端就绪!"
        break
    fi
    sleep 1
done

# 启动前端
echo ""
echo "[5/5] 启动前端服务..."
cd "$FRONTEND_DIR"
VITE_API_PORT=$BACKEND_PORT npm run dev &
FRONTEND_PID=$!
echo "  PID: $FRONTEND_PID"

echo ""
echo "============================================"
echo "  启动完成!"
echo "============================================"
echo "  前端:    http://localhost:5173"
echo "  后端:    http://localhost:$BACKEND_PORT/api/health"
echo "  文档:    http://localhost:$BACKEND_PORT/docs"
echo "============================================"
echo "  按 Ctrl+C 停止所有服务"
echo "============================================"

# 等待用户中断
wait
