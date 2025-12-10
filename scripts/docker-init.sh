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

# Redis配置 [自动启用]
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379

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

# 确保文件权限正确
chmod 644 /app/.env

# 确保备份目录存在（权限不足时只警告不退出）
mkdir -p /app/backups/config 2>/dev/null || echo "⚠️  警告: 无法创建备份目录,备份功能可能受限"
chmod 755 /app/backups/config 2>/dev/null || true

echo "✅ 容器环境初始化完成"

# 执行原始命令
exec "$@"
