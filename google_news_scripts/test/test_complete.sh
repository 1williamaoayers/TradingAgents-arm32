#!/bin/bash

# Google News 可用性最终验证脚本
# 使用方法: bash test_google_news_final.sh

echo "=========================================="
echo "Google News 可用性验证"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 测试1: 基础连接
echo -e "${YELLOW}[测试1] 基础网络连接${NC}"
if ping -c 2 8.8.8.8 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 网络正常${NC}"
else
    echo -e "${RED}✗ 网络异常${NC}"
    exit 1
fi
echo ""

# 测试2: DNS解析
echo -e "${YELLOW}[测试2] DNS解析${NC}"
if nslookup news.google.com > /dev/null 2>&1; then
    echo -e "${GREEN}✓ DNS解析成功${NC}"
    IP=$(nslookup news.google.com | grep "Address:" | tail -n 1 | awk '{print $2}')
    echo -e "${BLUE}   IP: $IP${NC}"
else
    echo -e "${RED}✗ DNS解析失败${NC}"
    exit 1
fi
echo ""

# 测试3: HTTPS连接(跟随重定向)
echo -e "${YELLOW}[测试3] HTTPS连接测试${NC}"
HTTP_CODE=$(curl -sL -o /dev/null -w "%{http_code}" --connect-timeout 10 https://news.google.com)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ HTTPS连接成功 (状态码: $HTTP_CODE)${NC}"
else
    echo -e "${YELLOW}⚠ 状态码: $HTTP_CODE (可能需要重定向)${NC}"
fi
echo ""

# 测试4: 获取网页内容
echo -e "${YELLOW}[测试4] 获取Google News网页内容${NC}"
CONTENT=$(curl -sL --connect-timeout 10 https://news.google.com 2>&1)
if echo "$CONTENT" | grep -qi "google"; then
    echo -e "${GREEN}✓ 成功获取内容${NC}"
    
    # 提取标题
    TITLE=$(echo "$CONTENT" | grep -o "<title>.*</title>" | sed 's/<[^>]*>//g' | head -n 1)
    if [ -n "$TITLE" ]; then
        echo -e "${BLUE}   页面标题: $TITLE${NC}"
    fi
else
    echo -e "${RED}✗ 无法获取有效内容${NC}"
fi
echo ""

# 测试5: RSS Feed
echo -e "${YELLOW}[测试5] Google News RSS Feed${NC}"
RSS_CODE=$(curl -sL -o /dev/null -w "%{http_code}" --connect-timeout 10 "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")
if [ "$RSS_CODE" = "200" ]; then
    echo -e "${GREEN}✓ RSS Feed可用 (状态码: $RSS_CODE)${NC}"
    
    # 获取RSS内容并显示新闻标题
    echo -e "${BLUE}   最新新闻标题:${NC}"
    RSS_CONTENT=$(curl -sL "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en" 2>&1)
    echo "$RSS_CONTENT" | grep -o "<title>.*</title>" | sed 's/<[^>]*>//g' | sed 's/&amp;/\&/g' | head -n 6 | tail -n 5 | while read line; do
        echo -e "${BLUE}   • $line${NC}"
    done
else
    echo -e "${RED}✗ RSS Feed不可用 (状态码: $RSS_CODE)${NC}"
fi
echo ""

# 测试6: 不同地区的RSS
echo -e "${YELLOW}[测试6] 测试不同地区的Google News${NC}"

# 美国
US_CODE=$(curl -sL -o /dev/null -w "%{http_code}" "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en")
echo -e "   美国: $([ "$US_CODE" = "200" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}") (状态码: $US_CODE)"

# 英国
UK_CODE=$(curl -sL -o /dev/null -w "%{http_code}" "https://news.google.com/rss?hl=en-GB&gl=GB&ceid=GB:en")
echo -e "   英国: $([ "$UK_CODE" = "200" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}") (状态码: $UK_CODE)"

# 香港
HK_CODE=$(curl -sL -o /dev/null -w "%{http_code}" "https://news.google.com/rss?hl=zh-HK&gl=HK&ceid=HK:zh-Hant")
echo -e "   香港: $([ "$HK_CODE" = "200" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}") (状态码: $HK_CODE)"

echo ""

# 测试7: 响应时间
echo -e "${YELLOW}[测试7] 响应时间测试${NC}"
RESPONSE_TIME=$(curl -sL -o /dev/null -w "%{time_total}" https://news.google.com)
echo -e "${GREEN}   响应时间: ${RESPONSE_TIME}秒${NC}"

# 评估速度
RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc 2>/dev/null || echo "0")
RESPONSE_MS_INT=${RESPONSE_MS%.*}

if [ "$RESPONSE_MS_INT" -lt 500 ]; then
    echo -e "${GREEN}   ✓ 速度优秀${NC}"
elif [ "$RESPONSE_MS_INT" -lt 1000 ]; then
    echo -e "${YELLOW}   ⚠ 速度一般${NC}"
else
    echo -e "${RED}   ✗ 速度较慢${NC}"
fi
echo ""

# 测试8: Python环境
echo -e "${YELLOW}[测试8] Python GNews库测试${NC}"
if command -v python3 &> /dev/null; then
    cat > /tmp/test_gnews_final.py << 'PYEOF'
import sys
try:
    from gnews import GNews
    
    google_news = GNews(language='en', country='US', max_results=3)
    news = google_news.get_top_news()
    
    if news and len(news) > 0:
        print(f"✓ GNews库工作正常,获取到 {len(news)} 条新闻")
        print("\n最新新闻:")
        for i, item in enumerate(news, 1):
            title = item.get('title', 'N/A')[:70]
            print(f"  {i}. {title}")
        sys.exit(0)
    else:
        print("✗ 未能获取新闻")
        sys.exit(1)
        
except ImportError:
    print("ℹ GNews库未安装")
    print("  安装命令: pip3 install gnews")
    sys.exit(2)
except Exception as e:
    print(f"✗ 错误: {str(e)}")
    sys.exit(1)
PYEOF
    
    PYTHON_OUTPUT=$(python3 /tmp/test_gnews_final.py 2>&1)
    PYTHON_EXIT=$?
    
    if [ $PYTHON_EXIT -eq 0 ]; then
        echo -e "${GREEN}$PYTHON_OUTPUT${NC}"
    elif [ $PYTHON_EXIT -eq 2 ]; then
        echo -e "${YELLOW}$PYTHON_OUTPUT${NC}"
    else
        echo -e "${RED}$PYTHON_OUTPUT${NC}"
    fi
    
    rm -f /tmp/test_gnews_final.py
else
    echo -e "${YELLOW}   ⚠ Python3未安装${NC}"
fi
echo ""

# 总结
echo "=========================================="
echo -e "${GREEN}测试完成!${NC}"
echo "=========================================="
echo ""

# 生成报告
TOTAL_TESTS=8
PASSED_TESTS=0

[ "$HTTP_CODE" = "200" ] && ((PASSED_TESTS++))
[ "$RSS_CODE" = "200" ] && ((PASSED_TESTS++))
echo "$CONTENT" | grep -qi "google" && ((PASSED_TESTS++))

if [ $PASSED_TESTS -ge 2 ]; then
    echo -e "${GREEN}✓ Google News 可用!${NC}"
    echo ""
    echo "推荐使用方式:"
    echo "  1. RSS Feed: https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    echo "  2. Python库: pip3 install gnews"
    echo "  3. cURL命令: curl -sL https://news.google.com"
    echo ""
    echo "注意事项:"
    echo "  • 使用curl时必须加 -L 参数(跟随重定向)"
    echo "  • RSS Feed是最稳定的获取方式"
    echo "  • 建议使用Python GNews库进行开发"
else
    echo -e "${RED}✗ Google News 访问受限${NC}"
    echo ""
    echo "可能的原因:"
    echo "  1. IP被Google限制"
    echo "  2. 需要使用代理"
    echo "  3. 地区限制"
fi
echo ""
