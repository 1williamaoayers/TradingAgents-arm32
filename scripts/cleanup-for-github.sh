#!/bin/bash
# GitHub上传前清理脚本
# 删除不必要的测试文件、缓存、临时文件等

set -e

echo "🧹 清理项目,准备上传GitHub..."
echo ""

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 计数器
DELETED_FILES=0
DELETED_DIRS=0

# 1. 删除Python缓存
echo -e "${YELLOW}📦 清理Python缓存...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
echo -e "${GREEN}✅ Python缓存已清理${NC}"

# 2. 删除根目录的测试文件
echo -e "${YELLOW}🧪 清理根目录测试文件...${NC}"
rm -f test_*.py 2>/dev/null || true
rm -f configure_newsapi.py 2>/dev/null || true
rm -f investigate_akshare_news.py 2>/dev/null || true
rm -f news_report_*.md 2>/dev/null || true
echo -e "${GREEN}✅ 根目录测试文件已清理${NC}"

# 3. 删除临时文件和备份
echo -e "${YELLOW}📄 清理临时文件...${NC}"
find . -type f -name "*.tmp" -delete 2>/dev/null || true
find . -type f -name "*.temp" -delete 2>/dev/null || true
find . -type f -name "*.bak" -delete 2>/dev/null || true
find . -type f -name "*.old" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true
echo -e "${GREEN}✅ 临时文件已清理${NC}"

# 4. 删除日志文件
echo -e "${YELLOW}📝 清理日志文件...${NC}"
find . -type f -name "*.log" -delete 2>/dev/null || true
rm -rf logs/* 2>/dev/null || true
echo -e "${GREEN}✅ 日志文件已清理${NC}"

# 5. 删除数据缓存
echo -e "${YELLOW}💾 清理数据缓存...${NC}"
rm -rf data/* 2>/dev/null || true
rm -rf cache/* 2>/dev/null || true
rm -rf backups/* 2>/dev/null || true
echo -e "${GREEN}✅ 数据缓存已清理${NC}"

# 6. 删除.env文件(保留.env.docker和.env.example)
echo -e "${YELLOW}🔐 清理环境变量文件...${NC}"
if [ -f .env ]; then
    rm -f .env
    echo -e "${GREEN}✅ .env文件已删除(保留.env.docker和.env.example)${NC}"
fi

# 7. 删除IDE配置
echo -e "${YELLOW}💻 清理IDE配置...${NC}"
rm -rf .vscode/settings.json 2>/dev/null || true
rm -rf .idea 2>/dev/null || true
echo -e "${GREEN}✅ IDE配置已清理${NC}"

# 8. 删除构建产物
echo -e "${YELLOW}🏗️ 清理构建产物...${NC}"
rm -rf build/ 2>/dev/null || true
rm -rf dist/ 2>/dev/null || true
rm -rf *.egg-info/ 2>/dev/null || true
echo -e "${GREEN}✅ 构建产物已清理${NC}"

# 9. 删除不必要的大文件
echo -e "${YELLOW}📦 清理大文件...${NC}"
rm -f uv.lock 2>/dev/null || true
echo -e "${GREEN}✅ 大文件已清理${NC}"

# 10. 保留必要的空目录结构
echo -e "${YELLOW}📁 创建必要的空目录...${NC}"
mkdir -p data logs cache backups
touch data/.gitkeep logs/.gitkeep cache/.gitkeep backups/.gitkeep
echo -e "${GREEN}✅ 目录结构已保留${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ 清理完成!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "已清理:"
echo "  ✅ Python缓存(__pycache__, *.pyc)"
echo "  ✅ 测试文件(test_*.py)"
echo "  ✅ 临时文件(*.tmp, *.bak)"
echo "  ✅ 日志文件(*.log)"
echo "  ✅ 数据缓存(data/, cache/)"
echo "  ✅ 环境变量(.env)"
echo "  ✅ IDE配置(.vscode, .idea)"
echo "  ✅ 构建产物(build/, dist/)"
echo ""
echo "保留:"
echo "  ✅ .env.docker (Docker配置模板)"
echo "  ✅ .env.example (配置示例)"
echo "  ✅ 源代码文件"
echo "  ✅ 文档文件"
echo "  ✅ 配置文件"
echo ""
echo "下一步:"
echo "  1. 检查 git status"
echo "  2. git add ."
echo "  3. git commit -m 'Initial commit'"
echo "  4. git push"
echo ""
