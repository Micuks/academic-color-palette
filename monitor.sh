#!/bin/bash
# 学术配色推荐器监控脚本

echo "========================================"
echo "🎨 学术配色推荐器 - 服务监控"
echo "========================================"
echo ""

# 检查服务状态
echo "📊 服务状态："
systemctl is-active palette-api
echo ""

# 检查健康端点
echo "🏥 健康检查："
curl -s http://localhost:8890/api/health | python3 -m json.tool
echo ""

# 检查端口占用
echo "🔌 端口占用："
netstat -tlnp | grep 8890
echo ""

# 检查进程
echo "⚙️ 进程信息："
ps aux | grep backend_server.py | grep -v grep | awk '{print "PID: "$2", CPU: "$3"%, MEM: "$4"%"}'
echo ""

echo "========================================"
echo "监控完成 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"