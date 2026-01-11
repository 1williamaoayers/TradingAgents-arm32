#!/bin/bash
echo "================================"
echo "🚀 启动 TradingAgents 服务..."
echo "================================"

# 确保日志目录存在
mkdir -p /app/logs

# 启动新闻定时同步调度器（后台运行）
echo "📅 启动新闻定时同步调度器..."
python3 /app/app/scheduler/news_scheduler.py &
SCHEDULER_PID=$!
echo "   调度器 PID: $SCHEDULER_PID"

# 等待调度器启动
sleep 2

# 启动 Streamlit 前端（前台运行）
echo "🌐 启动 Streamlit 前端..."
exec streamlit run web/app.py --server.port 8501 --server.address 0.0.0.0

