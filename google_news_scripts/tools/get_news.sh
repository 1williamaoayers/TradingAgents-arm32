#!/bin/bash

# 一键获取Google News - 小白专用脚本
# 使用方法: bash get_news.sh

echo "正在获取最新新闻..."
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装Python3,请先安装"
    exit 1
fi

# 检查gnews库是否安装
python3 -c "import gnews" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 正在安装GNews库..."
    pip3 install -q gnews
    echo "✓ 安装完成"
    echo ""
fi

# 获取新闻
python3 << 'EOF'
from gnews import GNews

print("=" * 60)
print("📰 Google News - 最新头条")
print("=" * 60)
print()

google_news = GNews(language='en', country='US', max_results=10)
news = google_news.get_top_news()

if news:
    for i, item in enumerate(news, 1):
        title = item.get('title', 'N/A')
        publisher = item.get('publisher', {}).get('title', 'Unknown')
        url = item.get('url', '')
        
        print(f"{i}. {title}")
        print(f"   来源: {publisher}")
        print(f"   链接: {url}")
        print()
    
    print("=" * 60)
    print(f"✓ 共获取 {len(news)} 条新闻")
    print("=" * 60)
else:
    print("❌ 未能获取新闻")
EOF
