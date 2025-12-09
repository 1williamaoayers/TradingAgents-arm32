#!/usr/bin/env python3
"""
简单的Google News获取脚本
使用方法: python3 simple_news.py
"""

from gnews import GNews

def get_latest_news(max_results=10):
    """获取最新新闻"""
    google_news = GNews(language='en', country='US', max_results=max_results)
    return google_news.get_top_news()

def search_news(keyword, max_results=5):
    """搜索特定关键词的新闻"""
    google_news = GNews(language='en', country='US', max_results=max_results)
    return google_news.get_news(keyword)

def main():
    print("=" * 70)
    print("📰 Google News 简易获取工具")
    print("=" * 70)
    print()
    
    # 获取头条新闻
    print("【头条新闻】")
    print()
    
    news = get_latest_news(5)
    
    if news:
        for i, item in enumerate(news, 1):
            print(f"{i}. {item['title']}")
            print(f"   来源: {item.get('publisher', {}).get('title', 'Unknown')}")
            print(f"   时间: {item.get('published date', 'N/A')}")
            print(f"   链接: {item['url']}")
            print()
    else:
        print("❌ 未能获取新闻")
        return
    
    # 搜索特定主题
    print("-" * 70)
    print("【科技新闻】")
    print()
    
    tech_news = search_news('technology', 3)
    
    if tech_news:
        for i, item in enumerate(tech_news, 1):
            print(f"{i}. {item['title']}")
            print(f"   {item.get('publisher', {}).get('title', 'Unknown')}")
            print()
    
    print("=" * 70)
    print("✓ 完成")
    print("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("❌ 请先安装GNews库:")
        print("   pip3 install gnews")
    except Exception as e:
        print(f"❌ 错误: {e}")
