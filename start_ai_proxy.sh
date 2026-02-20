#!/bin/bash
# AI代理服务启动脚本 - 自动重启机制

LOG_FILE="/tmp/ai_proxy.log"
PID_FILE="/tmp/ai_proxy.pid"

# 停止旧服务
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "停止旧服务 (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f "$PID_FILE"
fi

# 启动新服务
echo "启动AI代理服务..."
cd /root/.openclaw/workspace/academic-color-palette

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 启动AI代理服务..." >> "$LOG_FILE"
    python3 ai_proxy_v2.py >> "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] AI代理服务已启动 (PID: $PID)" >> "$LOG_FILE"
    
    # 等待进程结束
    wait $PID
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] AI代理服务已停止 (退出码: $EXIT_CODE)" >> "$LOG_FILE"
    
    # 如果是异常退出，等待5秒后重启
    if [ $EXIT_CODE -ne 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 5秒后重启..." >> "$LOG_FILE"
        sleep 5
    else
        # 正常退出，不再重启
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 正常退出，停止服务" >> "$LOG_FILE"
        break
    fi
done