#!/bin/bash
# 自选股功能快速验证脚本

echo "╔════════════════════════════════════════╗"
echo "║   自选股功能验证脚本                   ║"
echo "╚════════════════════════════════════════╝"
echo ""

# 1. 检查 MongoDB 服务
echo "📡 [1/4] 检查 MongoDB 服务..."
if ps aux | grep mongod | grep -v grep > /dev/null; then
    echo "   ✅ MongoDB 服务运行中"
else
    echo "   ❌ MongoDB 服务未运行"
    echo "   💡 请启动 MongoDB: sudo systemctl start mongod"
    exit 1
fi
echo ""

# 2. 验证数据库数据
echo "💾 [2/4] 验证数据库数据..."
python3 verify_mongodb_watchlist.py 2>&1 | grep -A 1 "自选股数量" | head -2
echo ""

# 3. 检查 JSON 文件状态
echo "📄 [3/4] 检查 JSON 文件状态..."
if [ -f "data/watchlist.json" ]; then
    FILE_TIME=$(stat -c %y data/watchlist.json 2>/dev/null | cut -d'.' -f1)
    FILE_SIZE=$(stat -c %s data/watchlist.json 2>/dev/null)
    echo "   文件修改时间: $FILE_TIME"
    echo "   文件大小: $FILE_SIZE 字节"
    echo "   📌 注意: 该文件应该不再被修改（旧时间戳）"
else
    echo "   ⚠️  文件不存在: data/watchlist.json"
fi
echo ""

# 4. 检查前端文件
echo "🎨 [4/4] 检查前端文件..."
if grep -q "fetch_watchlist_from_db" "web/pages/3_自选股管理.py"; then
    echo "   ✅ 前端已重构（使用 MongoDB）"
else
    echo "   ❌ 前端未重构（仍使用 JSON）"
    exit 1
fi
echo ""

echo "╔════════════════════════════════════════╗"
echo "║   ✨ 验证完成                          ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "📝 下一步操作："
echo "   1. 启动前端服务: streamlit run web/主页.py --server.port 8501"
echo "   2. 打开浏览器: http://localhost:8501"
echo "   3. 进入"自选股管理"页面"
echo "   4. 测试添加新股票（如 00700.HK）"
echo ""
