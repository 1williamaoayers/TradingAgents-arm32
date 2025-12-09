#!/bin/bash

# Google News 可用性测试与DNS修复脚本
# 使用方法: bash test_google_news_fix.sh

echo "=========================================="
echo "Google News 可用性测试 + DNS诊断"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 测试1: 检查网络连接
echo -e "${YELLOW}[测试1] 检查基本网络连接...${NC}"
if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 网络连接正常${NC}"
else
    echo -e "${RED}✗ 网络连接失败${NC}"
    exit 1
fi
echo ""

# 测试2: DNS诊断
echo -e "${YELLOW}[测试2] DNS诊断...${NC}"
echo -e "${BLUE}当前DNS配置:${NC}"
cat /etc/resolv.conf
echo ""

# 检查当前DNS能否解析Google
echo -e "${BLUE}测试当前DNS解析Google News...${NC}"
if nslookup news.google.com > /dev/null 2>&1; then
    echo -e "${GREEN}✓ DNS解析成功${NC}"
    DNS_OK=1
else
    echo -e "${RED}✗ 当前DNS无法解析Google域名${NC}"
    DNS_OK=0
fi
echo ""

# 如果DNS失败,提供修复方案
if [ $DNS_OK -eq 0 ]; then
    echo -e "${YELLOW}=========================================="
    echo "DNS问题诊断与修复方案"
    echo -e "==========================================${NC}"
    echo ""
    
    # 测试不同的DNS服务器
    echo -e "${BLUE}测试各种公共DNS服务器...${NC}"
    echo ""
    
    # Google DNS
    echo -e "${YELLOW}测试 Google DNS (8.8.8.8)...${NC}"
    if nslookup news.google.com 8.8.8.8 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Google DNS 可用${NC}"
        WORKING_DNS="8.8.8.8"
    else
        echo -e "${RED}✗ Google DNS 不可用${NC}"
    fi
    
    # Cloudflare DNS
    echo -e "${YELLOW}测试 Cloudflare DNS (1.1.1.1)...${NC}"
    if nslookup news.google.com 1.1.1.1 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Cloudflare DNS 可用${NC}"
        WORKING_DNS="1.1.1.1"
    else
        echo -e "${RED}✗ Cloudflare DNS 不可用${NC}"
    fi
    
    # OpenDNS
    echo -e "${YELLOW}测试 OpenDNS (208.67.222.222)...${NC}"
    if nslookup news.google.com 208.67.222.222 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OpenDNS 可用${NC}"
        WORKING_DNS="208.67.222.222"
    else
        echo -e "${RED}✗ OpenDNS 不可用${NC}"
    fi
    
    echo ""
    
    if [ -n "$WORKING_DNS" ]; then
        echo -e "${GREEN}找到可用的DNS服务器: $WORKING_DNS${NC}"
        echo ""
        echo -e "${YELLOW}修复方案(选择一个):${NC}"
        echo ""
        echo -e "${BLUE}方案1: 临时修复(重启后失效)${NC}"
        echo "sudo bash -c 'echo \"nameserver $WORKING_DNS\" > /etc/resolv.conf'"
        echo ""
        echo -e "${BLUE}方案2: 永久修复(推荐)${NC}"
        echo "# 对于使用systemd-resolved的系统(Ubuntu 18.04+):"
        echo "sudo mkdir -p /etc/systemd/resolved.conf.d/"
        echo "sudo bash -c 'cat > /etc/systemd/resolved.conf.d/dns.conf << EOF"
        echo "[Resolve]"
        echo "DNS=$WORKING_DNS"
        echo "FallbackDNS=8.8.4.4 1.0.0.1"
        echo "EOF'"
        echo "sudo systemctl restart systemd-resolved"
        echo ""
        echo "# 对于传统系统:"
        echo "sudo bash -c 'cat > /etc/resolv.conf << EOF"
        echo "nameserver $WORKING_DNS"
        echo "nameserver 8.8.4.4"
        echo "EOF'"
        echo "sudo chattr +i /etc/resolv.conf  # 防止被覆盖"
        echo ""
        
        # 询问是否自动修复
        echo -e "${YELLOW}是否立即应用临时修复? (y/n)${NC}"
        read -r -t 10 answer || answer="n"
        
        if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
            echo -e "${BLUE}正在应用临时DNS修复...${NC}"
            sudo bash -c "echo 'nameserver $WORKING_DNS' > /etc/resolv.conf"
            sudo bash -c "echo 'nameserver 8.8.4.4' >> /etc/resolv.conf"
            echo -e "${GREEN}✓ DNS已临时修复${NC}"
            echo ""
            
            # 重新测试
            echo -e "${YELLOW}重新测试DNS解析...${NC}"
            if nslookup news.google.com > /dev/null 2>&1; then
                echo -e "${GREEN}✓ DNS解析现在正常了!${NC}"
                DNS_OK=1
            else
                echo -e "${RED}✗ 修复失败,请手动执行上述命令${NC}"
            fi
        else
            echo -e "${YELLOW}请手动执行上述命令修复DNS${NC}"
            exit 1
        fi
    else
        echo -e "${RED}所有公共DNS都无法使用,可能存在网络封锁${NC}"
        echo -e "${YELLOW}建议:${NC}"
        echo "1. 检查VPS是否在中国大陆(如果是,需要特殊配置)"
        echo "2. 联系VPS提供商检查网络限制"
        echo "3. 考虑使用代理或VPN"
        exit 1
    fi
    echo ""
fi

# 如果DNS正常,继续其他测试
if [ $DNS_OK -eq 1 ]; then
    echo -e "${YELLOW}[测试3] 测试Google News HTTPS连接...${NC}"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 https://news.google.com)
    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 301 ] || [ "$HTTP_CODE" -eq 302 ]; then
        echo -e "${GREEN}✓ HTTPS连接成功 (HTTP状态码: $HTTP_CODE)${NC}"
    else
        echo -e "${RED}✗ HTTPS连接失败 (HTTP状态码: $HTTP_CODE)${NC}"
        echo -e "${YELLOW}可能原因:${NC}"
        echo "1. 防火墙阻止HTTPS连接"
        echo "2. 需要代理访问"
        echo "3. IP被Google限制"
        exit 1
    fi
    echo ""
    
    echo -e "${YELLOW}[测试4] 获取Google News首页内容...${NC}"
    CONTENT=$(curl -s --connect-timeout 10 -L https://news.google.com 2>&1)
    if echo "$CONTENT" | grep -qi "google"; then
        echo -e "${GREEN}✓ 成功获取Google News内容${NC}"
        echo -e "${BLUE}内容预览(前100字符):${NC}"
        echo "$CONTENT" | head -c 100
        echo "..."
    else
        echo -e "${RED}✗ 无法获取有效内容${NC}"
        echo -e "${YELLOW}返回内容:${NC}"
        echo "$CONTENT" | head -n 5
        exit 1
    fi
    echo ""
    
    echo -e "${YELLOW}[测试5] 测试Google News RSS Feed...${NC}"
    RSS_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "https://news.google.com/rss")
    if [ "$RSS_CODE" -eq 200 ]; then
        echo -e "${GREEN}✓ RSS Feed可访问 (HTTP状态码: $RSS_CODE)${NC}"
        
        # 获取实际RSS内容
        echo -e "${BLUE}RSS内容示例:${NC}"
        curl -s --connect-timeout 10 "https://news.google.com/rss" | head -n 10
    else
        echo -e "${YELLOW}⚠ RSS Feed访问失败 (HTTP状态码: $RSS_CODE)${NC}"
    fi
    echo ""
    
    echo -e "${YELLOW}[测试6] 测试响应时间...${NC}"
    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --connect-timeout 10 https://news.google.com)
    echo -e "${GREEN}响应时间: ${RESPONSE_TIME}秒${NC}"
    
    # 评估响应时间
    RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
    RESPONSE_MS_INT=${RESPONSE_MS%.*}
    
    if [ "$RESPONSE_MS_INT" -lt 500 ]; then
        echo -e "${GREEN}✓ 响应速度优秀${NC}"
    elif [ "$RESPONSE_MS_INT" -lt 1000 ]; then
        echo -e "${YELLOW}⚠ 响应速度一般${NC}"
    else
        echo -e "${RED}✗ 响应速度较慢${NC}"
    fi
    echo ""
    
    # 测试Python GNews库
    echo -e "${YELLOW}[测试7] Python GNews库测试...${NC}"
    if command -v python3 &> /dev/null; then
        cat > /tmp/test_gnews.py << 'PYEOF'
import sys
try:
    from gnews import GNews
    print("✓ GNews库已安装")
    
    google_news = GNews(language='en', country='US', max_results=3)
    news = google_news.get_top_news()
    
    if news and len(news) > 0:
        print(f"✓ 成功获取 {len(news)} 条新闻")
        print("\n最新新闻:")
        for i, item in enumerate(news, 1):
            print(f"{i}. {item.get('title', 'N/A')}")
    else:
        print("✗ 未能获取新闻")
        sys.exit(1)
except ImportError:
    print("ℹ GNews库未安装,安装命令: pip3 install gnews")
except Exception as e:
    print(f"✗ 错误: {str(e)}")
    sys.exit(1)
PYEOF
        
        python3 /tmp/test_gnews.py
        rm -f /tmp/test_gnews.py
    else
        echo -e "${YELLOW}⚠ Python3未安装${NC}"
    fi
    echo ""
    
    # 总结
    echo "=========================================="
    echo -e "${GREEN}✓ 所有测试完成!${NC}"
    echo "=========================================="
    echo ""
    echo -e "${GREEN}结论: 你的VPS可以正常访问Google News!${NC}"
    echo ""
    echo "下一步建议:"
    echo "1. 如果使用了临时DNS修复,建议应用永久修复方案"
    echo "2. 安装Python GNews库: pip3 install gnews"
    echo "3. 可以开始使用Google News API了"
    echo ""
fi
