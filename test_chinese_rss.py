#!/usr/bin/env python3
"""
测试中文财经RSS源（CDX RSSHub实例）
"""
import sys
sys.path.insert(0, '/app')

print("=" * 80)
print("📰 中文财经RSS源实际可用性测试")
print("测试CDX RSSHub实例: rss.cdx.hidns.co")
print("=" * 80)
print()

try:
    import feedparser
    print(f"✅ feedparser 已安装 (版本: {feedparser.__version__})")
    print()
except ImportError:
    print("❌ feedparser 未安装")
    exit(1)

results = {}

# ============================================================================
# 🚀 第一梯队：必读快讯
# ============================================================================
print("🚀 第一梯队：必读快讯（追求速度）")
print("=" * 80)

tier1_sources = [
    ("金十数据 - 快讯", "https://rss.cdx.hidns.co/jin10/flash"),
    ("财联社 - 电报", "https://rss.cdx.hidns.co/cls/telegraph"),
    ("格隆汇 - 7x24小时快讯", "https://rss.cdx.hidns.co/gelonghui/live"),
]

for name, url in tier1_sources:
    try:
        print(f"\n📌 测试: {name}")
        print(f"   URL: {url}")
        feed = feedparser.parse(url)
        
        if feed.bozo == 0 and len(feed.entries) > 0:
            results[name] = True
            print(f"   ✅ 成功获取: {len(feed.entries)} 条")
            print(f"   最新快讯:")
            for i, entry in enumerate(feed.entries[:3], 1):
                title = entry.get('title', 'N/A')
                published = entry.get('published', entry.get('updated', 'N/A'))
                print(f"      {i}. {title[:70]}...")
                print(f"         时间: {published}")
        else:
            results[name] = False
            print(f"   ❌ 获取失败或无数据")
            if feed.bozo:
                print(f"   错误: {feed.bozo_exception}")
    except Exception as e:
        results[name] = False
        print(f"   ❌ 错误: {str(e)[:100]}")

print()

# ============================================================================
# 🌍 第二梯队：宏观与全球
# ============================================================================
print("🌍 第二梯队：宏观与全球（看大方向）")
print("=" * 80)

tier2_sources = [
    ("华尔街见闻 - 全球实时", "https://rss.cdx.hidns.co/wallstreetcn/live/global"),
    ("英为财情 - 股市新闻", "https://rss.cdx.hidns.co/investing/news/stock-market-news"),
]

for name, url in tier2_sources:
    try:
        print(f"\n📌 测试: {name}")
        print(f"   URL: {url}")
        feed = feedparser.parse(url)
        
        if feed.bozo == 0 and len(feed.entries) > 0:
            results[name] = True
            print(f"   ✅ 成功获取: {len(feed.entries)} 条")
            print(f"   最新新闻:")
            for i, entry in enumerate(feed.entries[:2], 1):
                title = entry.get('title', 'N/A')
                print(f"      {i}. {title[:70]}...")
        else:
            results[name] = False
            print(f"   ❌ 获取失败或无数据")
    except Exception as e:
        results[name] = False
        print(f"   ❌ 错误: {str(e)[:100]}")

print()

# ============================================================================
# 🧠 第三梯队：情绪与深度
# ============================================================================
print("🧠 第三梯队：情绪与深度（看逻辑）")
print("=" * 80)

tier3_sources = [
    ("雪球 - 今日热帖", "https://rss.cdx.hidns.co/xueqiu/today"),
    ("财新网 - 金融频道", "https://rss.cdx.hidns.co/caixin/category/finance"),
]

for name, url in tier3_sources:
    try:
        print(f"\n📌 测试: {name}")
        print(f"   URL: {url}")
        feed = feedparser.parse(url)
        
        if feed.bozo == 0 and len(feed.entries) > 0:
            results[name] = True
            print(f"   ✅ 成功获取: {len(feed.entries)} 条")
            print(f"   最新内容:")
            for i, entry in enumerate(feed.entries[:2], 1):
                title = entry.get('title', 'N/A')
                print(f"      {i}. {title[:70]}...")
        else:
            results[name] = False
            print(f"   ❌ 获取失败或无数据")
    except Exception as e:
        results[name] = False
        print(f"   ❌ 错误: {str(e)[:100]}")

print()

# ============================================================================
# 总结
# ============================================================================
print("=" * 80)
print("📊 中文财经RSS源测试总结")
print("=" * 80)
print()

tier1_available = [k for k in tier1_sources if results.get(k[0], False)]
tier2_available = [k for k in tier2_sources if results.get(k[0], False)]
tier3_available = [k for k in tier3_sources if results.get(k[0], False)]

print("🚀 第一梯队（必读快讯）:")
if tier1_available:
    for name, url in tier1_available:
        print(f"   ✅ {name}")
else:
    print("   ❌ 全部不可用")

print()
print("🌍 第二梯队（宏观全球）:")
if tier2_available:
    for name, url in tier2_available:
        print(f"   ✅ {name}")
else:
    print("   ❌ 全部不可用")

print()
print("🧠 第三梯队（情绪深度）:")
if tier3_available:
    for name, url in tier3_available:
        print(f"   ✅ {name}")
else:
    print("   ❌ 全部不可用")

print()
total_sources = len(tier1_sources) + len(tier2_sources) + len(tier3_sources)
available_count = len([v for v in results.values() if v])
print(f"总体可用率: {available_count}/{total_sources} ({available_count/total_sources*100:.1f}%)")

print()
print("💡 推荐配置:")
if available_count > 0:
    print("   ✅ CDX RSSHub实例可用，建议使用")
    print("   配置: RSS_HUB_BASE=https://rss.cdx.hidns.co")
else:
    print("   ⚠️ CDX RSSHub实例当前不可用")
    print("   建议: 使用Google News或Yahoo Finance作为替代")

print()
print("=" * 80)
