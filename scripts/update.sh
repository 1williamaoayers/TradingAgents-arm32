#!/bin/bash

# ============================================
# TradingAgents 一键更新脚本
# ============================================

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[INFO]${NC} 开始更新 TradingAgents..."

# 拉取最新镜像
echo -e "${BLUE}[INFO]${NC} 拉取最新镜像..."
docker-compose pull

# 重启服务
echo -e "${BLUE}[INFO]${NC} 重启服务..."
docker-compose up -d

# 清理旧镜像
echo -e "${BLUE}[INFO]${NC} 清理旧镜像..."
docker image prune -f

echo -e "${GREEN}[SUCCESS]${NC} 更新完成!"
echo ""
echo "访问地址: http://localhost:8501"
