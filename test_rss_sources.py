#!/usr/bin/env python3
"""
RSS新闻源实际可用性测试
测试项目中配置的所有RSS新闻源
"""
import sys
sys.path.insert(0, '/app')

print("=" * 80)
print("📰 RSS新闻源实际可用性测试")
print("=" * 80)
print()

results = {}

# ============================================================================
# 1. 测试 feedparser 模块
# ============================================================================
print("1️⃣ 测试 feedparser 模块")
print("-" * 80)

try:
    import feedparser
    print(f"✅ feedparser 已安装 (版本: {feedparser.__version__})")
    print()
except ImportError:
    print("❌ feedparser 未安装")
    print("   需要安装: pip install feedparser")
    exit(1)

# ============================================================================
# 2. 测试 RSSHub - 财联社电报快讯
# ============================================================================
print("2️⃣ 测试 RSSHub - 财联社电报快讯")
print("-" * 80)

rsshub_urls = [
    ("主实例", "https://rsshub.app/cls/telegraph"),
    ("备用1", "https://rsshub.rssforever.com/cls/telegraph"),
    ("备用2", "https://rsshub.anyfeeder.com/cls/telegraph"),
]

for name, url in rsshub_urls:
    try:
        print(f"   测试: {name} - {url}")
        feed = feedparser.parse(url)
        
        if feed.bozo == 0 and len(feed.entries) > 0:
            results[f'rsshub_{name}'] = True
            print(f"   ✅ 成功获取新闻: {len(feed.entries)} 条")
            print(f"   最新新闻:")
            for i, entry in enumerate(feed.entries[:3], 1):
                title = entry.get('title', 'N/A')
                published = entry.get('published', 'N/A')
                print(f"      {i}. {title[:60]}...")
                print(f"         时间: {published}")
            break
        else:
            results[f'rsshub_{name}'] = False
            print(f"   ❌ 获取失败或无数据")
    except Exception as e:
        results[f'rsshub_{name}'] = False
        print(f"   ❌ 错误: {str(e)[:100]}")

print()

# ============================================================================
# 3. 测试 RSSHub - 其他财联社频道
# ============================================================================
print("3️⃣ 测试 RSSHub - 其他财联社频道")
print("-" * 80)

channels = [
    ("深度文章", "https://rsshub.app/cls/depth"),
    ("热门排行", "https://rsshub.app/cls/ranking/hot"),
]

for name, url in channels:
    try:
        print(f"   测试: {name} - {url}")
        feed = feedparser.parse(url)
        
        if feed.bozo == 0 and len(feed.entries) > 0:
            results[f'rsshub_{name}'] = True
            print(f"   ✅ 成功: {len(feed.entries)} 条")
            print(f"   示例: {feed.entries[0].get('title', 'N/A')[:50]}...")
        else:
            results[f'rsshub_{name}'] = False
            print(f"   ❌ 失败或无数据")
    except Exception as e:
        results[f'rsshub_{name}'] = False
        print(f"   ❌ 错误: {str(e)[:100]}")

print()

# ============================================================================
# 4. 测试 Google News RSS
# ============================================================================
print("4️⃣ 测试 Google News RSS")
print("-" * 80)

google_rss_urls = [
    ("美国版", "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"),
    ("香港版", "https://news.google.com/rss?hl=zh-HK&gl=HK&ceid=HK:zh-Hant"),
    ("中国版", "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
]

for name, url in google_rss_urls:
    try:
        print(f"   测试: Google News {name}")
        feed = feedparser.parse(url)
        
        if feed.bozo == 0 and len(feed.entries) > 0:
            results[f'google_{name}'] = True
            print(f"   ✅ 成功: {len(feed.entries)} 条")
            print(f"   最新: {feed.entries[0].get('title', 'N/A')[:50]}...")
        else:
            results[f'google_{name}'] = False
            print(f"   ❌ 失败或无数据")
    except Exception as e:
        results[f'google_{name}'] = False
        print(f"   ❌ 错误: {str(e)[:100]}")

print()

# ============================================================================
# 5. 测试 Yahoo Finance RSS
# ============================================================================
print("5️⃣ 测试 Yahoo Finance RSS")
print("-" * 80)

yahoo_rss_urls = [
    ("最新新闻", "https://finance.yahoo.com/news/rssindex"),
    ("股票新闻", "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US"),
]

for name, url in yahoo_rss_urls:
    try:
        print(f"   测试: Yahoo Finance {name}")
        feed = feedparser.parse(url)
        
        if feed.bozo == 0 and len(feed.entries) > 0:
            results[f'yahoo_{name}'] = True
            print(f"   ✅ 成功: {len(feed.entries)} 条")
            print(f"   示例: {feed.entries[0].get('title', 'N/A')[:50]}...")
        else:
            results[f'yahoo_{name}'] = False
            print(f"   ❌ 失败或无数据")
    except Exception as e:
        results[f'yahoo_{name}'] = False
        print(f"   ❌ 错误: {str(e)[:100]}")

print()

# ============================================================================
# 6. 测试 Reuters RSS
# ============================================================================
print("6️⃣ 测试 Reuters RSS")
print("-" * 80)

reuters_urls = [
    ("商业新闻", "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best"),
]

for name, url in reuters_urls:
    try:
        print(f"   测试: Reuters {name}")
        feed = feedparser.parse(url)
        
        if feed.bozo == 0 and len(feed.entries) > 0:
            results[f'reuters_{name}'] = True
            print(f"   ✅ 成功: {len(feed.entries)} 条")
            print(f"   示例: {feed.entries[0].get('title', 'N/A')[:50]}...")
        else:
            results[f'reuters_{name}'] = False
            print(f"   ❌ 失败或无数据")
    except Exception as e:
        results[f'reuters_{name}'] = False
        print(f"   ❌ 错误: {str(e)[:100]}")

print()

# ============================================================================
# 总结
# ============================================================================
print("=" * 80)
print("📊 RSS新闻源测试总结")
print("=" * 80)
print()

available_sources = [k for k, v in results.items() if v]
unavailable_sources = [k for k, v in results.items() if not v]

print(f"✅ 可用源: {len(available_sources)}")
for source in available_sources:
    print(f"   - {source}")

print()
print(f"❌ 不可用源: {len(unavailable_sources)}")
for source in unavailable_sources:
    print(f"   - {source}")

print()
print("💡 推荐配置:")
if any('rsshub' in k for k, v in results.items() if v):
    print("   ✅ 使用 RSSHub 获取财联社新闻（免费、稳定）")
if any('google' in k for k, v in results.items() if v):
    print("   ✅ 使用 Google News RSS（免费、全球新闻）")
if any('yahoo' in k for k, v in results.items() if v):
    print("   ✅ 使用 Yahoo Finance RSS（免费、金融新闻）")

print()
print("=" * 80)
