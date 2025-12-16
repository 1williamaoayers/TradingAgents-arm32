#!/bin/bash
# 自选股功能启动和验证脚本

echo "╔════════════════════════════════════════╗"
echo "║   自选股功能启动脚本                   ║"
echo "╚════════════════════════════════════════╝"
echo ""

# 1. 检查 MongoDB 服务
echo "📡 [1/3] 检查 MongoDB 服务..."
if ps aux | grep mongod | grep -v grep > /dev/null; then
    echo "   ✅ MongoDB 服务运行中"
else
    echo "   ❌ MongoDB 服务未运行"
    echo "   💡 请启动 MongoDB: sudo systemctl start mongod"
    exit 1
fi
echo ""

# 2. 验证数据库连接
echo "💾 [2/3] 验证数据库连接..."
python3 verify_mongodb_watchlist.py 2>&1 | grep -A 1 "自选股数量" | head -2
echo ""

# 3. 启动前端服务
echo "🚀 [3/3] 启动前端服务..."
echo ""
echo "   入口文件: web/主页.py"
echo "   端口: 8501"
echo ""

# 检查端口是否被占用
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ⚠️  端口 8501 已被占用"
    echo "   正在停止旧进程..."
    kill -9 $(lsof -t -i:8501) 2>/dev/null
    sleep 2
fi

echo "   正在启动 Streamlit..."
echo ""
echo "╔════════════════════════════════════════╗"
echo "║   启动命令                             ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "cd /trae/TradingAgents-arm32"
echo "streamlit run web/主页.py --server.port 8501"
echo ""
echo "📝 访问地址: http://localhost:8501"
echo "📝 或: http://67.215.241.58:8501"
echo ""
echo "⚠️  请在新终端运行上述命令，或按 Ctrl+C 后台运行"
echo ""
