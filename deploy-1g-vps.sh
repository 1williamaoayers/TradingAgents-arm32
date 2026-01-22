#!/bin/bash
# =====================================================
# TradingAgents-CN 1G VPS 部署脚本
# 自动配置 swap 并启动轻量版服务
# =====================================================

set -e

echo "🚀 TradingAgents-CN 1G VPS 部署脚本"
echo "=================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 root 用户运行此脚本"
    exit 1
fi

# ==========================================
# 1. 配置 Swap (1GB)
# ==========================================
echo ""
echo "📦 步骤1: 配置 Swap 空间..."

SWAP_FILE="/swapfile"
SWAP_SIZE="1G"

if [ -f "$SWAP_FILE" ]; then
    echo "   ⚠️  Swap文件已存在，跳过创建"
else
    echo "   创建 ${SWAP_SIZE} swap 文件..."
    fallocate -l $SWAP_SIZE $SWAP_FILE || dd if=/dev/zero of=$SWAP_FILE bs=1M count=1024
    chmod 600 $SWAP_FILE
    mkswap $SWAP_FILE
    swapon $SWAP_FILE
    
    # 添加到 fstab 实现开机自动挂载
    if ! grep -q "$SWAP_FILE" /etc/fstab; then
        echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab
    fi
    
    echo "   ✅ Swap 配置完成"
fi

# 优化 swap 使用策略
echo "   设置 swappiness=10 (减少不必要的swap使用)..."
sysctl vm.swappiness=10
echo "vm.swappiness=10" > /etc/sysctl.d/99-swappiness.conf

# 显示当前内存状态
echo ""
echo "📊 当前内存状态:"
free -h

# ==========================================
# 2. 停止旧容器
# ==========================================
echo ""
echo "🛑 步骤2: 停止旧容器..."
cd /anti/ak-trading/TradingAgents-arm32

docker-compose down 2>/dev/null || true

# ==========================================
# 3. 启动服务
# ==========================================
echo ""
echo "🚀 步骤3: 启动服务..."
docker-compose up -d

# ==========================================
# 4. 等待服务启动
# ==========================================
echo ""
echo "⏳ 步骤4: 等待服务启动 (约60秒)..."
sleep 30

echo "   检查服务状态..."
docker-compose ps

# ==========================================
# 5. 显示资源使用
# ==========================================
echo ""
echo "📊 步骤5: 资源使用情况:"
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo "============================================"
echo "✅ 部署完成!"
echo ""
echo "📌 访问地址:"
echo "   - 前端: http://你的IP:8501"
echo "   - API:  http://你的IP:8000"
echo ""
echo "📌 管理命令:"
echo "   - 查看日志: docker-compose logs -f"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart"
echo "   - 查看内存: docker stats"
echo "============================================"
