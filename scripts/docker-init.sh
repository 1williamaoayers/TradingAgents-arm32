#!/bin/bash
# Docker容器初始化脚本
# 确保配置文件存在且权限正确

set -e

echo "🔧 初始化容器环境..."

# 确保.env文件存在
if [ ! -f /app/.env ]; then
    echo "📝 创建默认配置文件..."
    cat > /app/.env << 'EOF'
# ============================================
# TradingAgents 配置文件
# 由Docker自动创建
# ============================================

# AI模型API密钥 [必填]
DEEPSEEK_API_KEY=
DASHSCOPE_API_KEY=
OPENAI_API_KEY=

# 数据源API密钥 [推荐]
FINNHUB_API_KEY=
ALPHA_VANTAGE_API_KEY=

# 数据库配置 [自动启用]
USE_MONGODB_STORAGE=true
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_DATABASE=tradingagents
MONGODB_USERNAME=admin
MONGODB_PASSWORD=tradingagents123

# Redis配置 [自动启用]
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379

# JWT安全配置 [必填]
JWT_SECRET=tradingagents-docker-secret-key-2026

# 系统配置
TZ=Asia/Shanghai
LOG_LEVEL=INFO
MEMORY_ENABLED=true
TA_CACHE_STRATEGY=integrated

# 数据目录
TRADINGAGENTS_DATA_DIR=/app/data
TRADINGAGENTS_RESULTS_DIR=/app/data/results
TRADINGAGENTS_CACHE_DIR=/app/cache
EOF
fi

# 🔥 确保必要配置存在（即使.env已存在也补充缺失项）
if ! grep -q "JWT_SECRET" /app/.env 2>/dev/null; then
    echo "📝 补充缺失的JWT_SECRET配置..."
    echo "JWT_SECRET=tradingagents-docker-secret-key-2026" >> /app/.env
fi

if ! grep -q "MONGODB_DATABASE" /app/.env 2>/dev/null; then
    echo "📝 补充缺失的MONGODB配置..."
    echo "MONGODB_DATABASE=tradingagents" >> /app/.env
fi

if ! grep -q "MONGODB_USERNAME" /app/.env 2>/dev/null; then
    echo "MONGODB_USERNAME=admin" >> /app/.env
    echo "MONGODB_PASSWORD=tradingagents123" >> /app/.env
fi

# 确保文件权限正确
chmod 644 /app/.env || echo "⚠️  警告: 无法修改 .env 权限，跳过..."

# 确保备份目录存在（权限不足时只警告不退出）
mkdir -p /app/backups/config 2>/dev/null || echo "⚠️  警告: 无法创建备份目录,备份功能可能受限"
chmod 755 /app/backups/config 2>/dev/null || true

echo "✅ 容器环境初始化完成"

# ============================================
# 🔥 启动 FastAPI 后端服务（后台运行）
# 包含定时任务调度器
# ============================================
echo "================================"
echo "🚀 启动 TradingAgents 服务..."
echo "================================"

# 启动后端API服务（后台运行，日志输出到控制台）
echo "🌐 启动 FastAPI 后端 (8000端口)..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ FastAPI 后端已启动 (PID: $BACKEND_PID)"
else
    echo "⚠️ FastAPI 后端启动失败，继续启动前端..."
fi

# 启动 Streamlit 前端
echo "🌐 启动 Streamlit 前端..."

# 执行原始命令（Streamlit）
exec "$@"
