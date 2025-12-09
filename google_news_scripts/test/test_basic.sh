#!/bin/bash

# Google News 可用性测试脚本
# 使用方法: bash test_google_news.sh

echo "=========================================="
echo "Google News 可用性测试"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试1: 检查网络连接
echo -e "${YELLOW}[测试1] 检查基本网络连接...${NC}"
if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 网络连接正常${NC}"
else
    echo -e "${RED}✗ 网络连接失败${NC}"
    exit 1
fi
echo ""

# 测试2: 检查DNS解析
echo -e "${YELLOW}[测试2] 检查Google News DNS解析...${NC}"
if nslookup news.google.com > /dev/null 2>&1; then
    echo -e "${GREEN}✓ DNS解析成功${NC}"
    nslookup news.google.com | grep "Address:" | tail -n 1
else
    echo -e "${RED}✗ DNS解析失败${NC}"
    exit 1
fi
echo ""

# 测试3: 测试HTTPS连接
echo -e "${YELLOW}[测试3] 测试Google News HTTPS连接...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 https://news.google.com)
if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 301 ] || [ "$HTTP_CODE" -eq 302 ]; then
    echo -e "${GREEN}✓ HTTPS连接成功 (HTTP状态码: $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ HTTPS连接失败 (HTTP状态码: $HTTP_CODE)${NC}"
    exit 1
fi
echo ""

# 测试4: 获取实际内容
echo -e "${YELLOW}[测试4] 获取Google News首页内容...${NC}"
CONTENT=$(curl -s --connect-timeout 10 -L https://news.google.com | head -n 20)
if echo "$CONTENT" | grep -qi "google"; then
    echo -e "${GREEN}✓ 成功获取Google News内容${NC}"
    echo "前20行内容预览:"
    echo "$CONTENT"
else
    echo -e "${RED}✗ 无法获取有效内容${NC}"
    exit 1
fi
echo ""

# 测试5: 测试RSS Feed
echo -e "${YELLOW}[测试5] 测试Google News RSS Feed...${NC}"
RSS_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "https://news.google.com/rss")
if [ "$RSS_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ RSS Feed可访问 (HTTP状态码: $RSS_CODE)${NC}"
else
    echo -e "${RED}✗ RSS Feed访问失败 (HTTP状态码: $RSS_CODE)${NC}"
fi
echo ""

# 测试6: 测试特定地区的Google News (以美国为例)
echo -e "${YELLOW}[测试6] 测试美国地区Google News...${NC}"
US_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "https://news.google.com/home?hl=en-US&gl=US&ceid=US:en")
if [ "$US_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ 美国地区Google News可访问 (HTTP状态码: $US_CODE)${NC}"
else
    echo -e "${RED}✗ 美国地区Google News访问失败 (HTTP状态码: $US_CODE)${NC}"
fi
echo ""

# 测试7: 测试响应时间
echo -e "${YELLOW}[测试7] 测试响应时间...${NC}"
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --connect-timeout 10 https://news.google.com)
echo -e "${GREEN}响应时间: ${RESPONSE_TIME}秒${NC}"
echo ""

# 测试8: Python环境测试 (如果安装了Python)
echo -e "${YELLOW}[测试8] Python环境测试...${NC}"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python3已安装${NC}"
    
    # 创建临时Python测试脚本
    cat > /tmp/test_gnews.py << 'PYEOF'
import sys
try:
    from gnews import GNews
    print("✓ GNews库已安装")
    
    # 测试获取新闻
    google_news = GNews(language='en', country='US', max_results=5)
    news = google_news.get_top_news()
    
    if news and len(news) > 0:
        print(f"✓ 成功获取 {len(news)} 条新闻")
        print("\n最新新闻标题:")
        for i, item in enumerate(news[:3], 1):
            print(f"  {i}. {item.get('title', 'N/A')}")
    else:
        print("✗ 未能获取新闻内容")
        sys.exit(1)
        
except ImportError:
    print("✗ GNews库未安装")
    print("安装命令: pip3 install gnews")
    sys.exit(1)
except Exception as e:
    print(f"✗ 测试失败: {str(e)}")
    sys.exit(1)
PYEOF
    
    python3 /tmp/test_gnews.py
    PYTHON_TEST=$?
    
    if [ $PYTHON_TEST -eq 0 ]; then
        echo -e "${GREEN}✓ Python GNews测试通过${NC}"
    else
        echo -e "${YELLOW}⚠ Python GNews测试失败 (可能需要安装gnews库)${NC}"
    fi
    
    # 清理临时文件
    rm -f /tmp/test_gnews.py
else
    echo -e "${YELLOW}⚠ Python3未安装,跳过Python测试${NC}"
fi
echo ""

# 总结
echo "=========================================="
echo -e "${GREEN}测试完成!${NC}"
echo "=========================================="
echo ""
echo "如果所有测试都通过,说明你的VPS可以正常访问Google News"
echo "如果有测试失败,请检查:"
echo "  1. 网络连接是否正常"
echo "  2. 是否有防火墙限制"
echo "  3. DNS设置是否正确"
echo ""
