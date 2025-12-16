#!/usr/bin/env python3
"""测试新闻源获取京东相关新闻"""
import os
import requests
import feedparser

print("=" * 80)
print("=== 测试新闻源获取京东相关新闻 ===")
print("=" * 80)

# 1. 测试FinnHub API
try:
    print("\n1. 测试FinnHub API...")
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("❌ FINNHUB_API_KEY未配置")
    else:
        url = f"https://finnhub.io/api/v1/company-news?symbol=JD&from=2024-12-01&to=2024-12-15&token={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            news = response.json()
            print(f"✅ FinnHub新闻获取成功: {len(news)}条")
            if news:
                print(f"   最新新闻: {news[0].get('headline', 'N/A')[:50]}...")
        else:
            print(f"❌ FinnHub API失败: HTTP {response.status_code}")
except Exception as e:
    print(f"❌ FinnHub测试失败: {e}")

# 2. 测试Alpha Vantage API
try:
    print("\n2. 测试Alpha Vantage API...")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY未配置")
    else:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=JD&apikey={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            news_count = len(data.get('feed', []))
            print(f"✅ Alpha Vantage新闻获取成功: {news_count}条")
            if news_count > 0:
                print(f"   最新新闻: {data['feed'][0].get('title', 'N/A')[:50]}...")
        else:
            print(f"❌ Alpha Vantage API失败: HTTP {response.status_code}")
except Exception as e:
    print(f"❌ Alpha Vantage测试失败: {e}")

# 3. 测试Google News RSS
try:
    print("\n3. 测试Google News HK RSS...")
    rss_url = os.getenv("RSS_GOOGLE_NEWS_HK")
    if not rss_url:
        print("❌ RSS_GOOGLE_NEWS_HK未配置")
    else:
        feed = feedparser.parse(rss_url)
        print(f"✅ Google News HK获取成功: {len(feed.entries)}条")
        if feed.entries:
            print(f"   最新新闻: {feed.entries[0].title[:50]}...")
except Exception as e:
    print(f"❌ Google News测试失败: {e}")

# 4. 测试Yahoo Finance RSS
try:
    print("\n4. 测试Yahoo Finance RSS...")
    rss_url = os.getenv("RSS_YAHOO_FINANCE")
    if not rss_url:
        print("❌ RSS_YAHOO_FINANCE未配置")
    else:
        feed = feedparser.parse(rss_url)
        print(f"✅ Yahoo Finance获取成功: {len(feed.entries)}条")
        if feed.entries:
            print(f"   最新新闻: {feed.entries[0].title[:50]}...")
except Exception as e:
    print(f"❌ Yahoo Finance测试失败: {e}")

# 5. 测试中文新闻源
try:
    print("\n5. 测试中文新闻源（金十数据）...")
    rss_url = os.getenv("RSS_JIN10_FLASH")
    if not rss_url:
        print("❌ RSS_JIN10_FLASH未配置")
    else:
        feed = feedparser.parse(rss_url)
        print(f"✅ 金十数据获取成功: {len(feed.entries)}条")
        if feed.entries:
            print(f"   最新快讯: {feed.entries[0].title[:50]}...")
except Exception as e:
    print(f"❌ 金十数据测试失败: {e}")

print("\n" + "=" * 80)
print("=== 新闻源测试完成 ===")
print("=" * 80)
