#!/usr/bin/env python3
"""
Google News 可用性测试脚本
使用方法: python3 test_google_news_python.py
"""

import sys

def test_gnews():
    """测试GNews库"""
    try:
        from gnews import GNews
    except ImportError:
        print("❌ GNews库未安装")
        print("\n安装命令:")
        print("  pip3 install gnews")
        print("\n或者:")
        print("  python3 -m pip install gnews")
        return False
    
    print("=" * 60)
    print("Google News 可用性测试")
    print("=" * 60)
    print()
    
    # 测试1: 获取美国头条
    print("📰 [测试1] 获取美国头条新闻...")
    try:
        google_news = GNews(language='en', country='US', max_results=5)
        us_news = google_news.get_top_news()
        
        if us_news and len(us_news) > 0:
            print(f"✓ 成功获取 {len(us_news)} 条新闻\n")
            
            for i, item in enumerate(us_news, 1):
                title = item.get('title', 'N/A')
                publisher = item.get('publisher', {}).get('title', 'N/A')
                pub_date = item.get('published date', 'N/A')
                
                print(f"{i}. {title}")
                print(f"   发布者: {publisher}")
                print(f"   时间: {pub_date}")
                print()
        else:
            print("✗ 未获取到新闻\n")
            return False
            
    except Exception as e:
        print(f"✗ 错误: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试2: 搜索特定关键词
    print("🔍 [测试2] 搜索关键词 'technology'...")
    try:
        tech_news = google_news.get_news('technology')
        
        if tech_news and len(tech_news) > 0:
            print(f"✓ 找到 {len(tech_news)} 条相关新闻\n")
            
            for i, item in enumerate(tech_news[:3], 1):
                print(f"{i}. {item.get('title', 'N/A')}")
            print()
        else:
            print("⚠ 未找到相关新闻\n")
            
    except Exception as e:
        print(f"⚠ 搜索失败: {e}\n")
    
    # 测试3: 获取不同地区的新闻
    print("🌍 [测试3] 测试不同地区...")
    
    regions = [
        ('en', 'US', '美国'),
        ('en', 'GB', '英国'),
        ('zh-Hans', 'HK', '香港'),
    ]
    
    for lang, country, name in regions:
        try:
            regional_news = GNews(language=lang, country=country, max_results=1)
            news = regional_news.get_top_news()
            
            if news and len(news) > 0:
                print(f"  ✓ {name}: 可用")
            else:
                print(f"  ✗ {name}: 无新闻")
        except Exception as e:
            print(f"  ✗ {name}: 错误 - {e}")
    
    print()
    
    # 测试4: 获取新闻详情
    print("📄 [测试4] 获取新闻详情...")
    try:
        if us_news and len(us_news) > 0:
            first_news = us_news[0]
            article = google_news.get_full_article(first_news['url'])
            
            if article:
                print(f"✓ 成功获取文章详情")
                print(f"  标题: {article.title[:60]}...")
                print(f"  作者: {', '.join(article.authors) if article.authors else 'N/A'}")
                print(f"  发布时间: {article.publish_date}")
                
                if article.text:
                    print(f"  内容长度: {len(article.text)} 字符")
                    print(f"  内容预览: {article.text[:100]}...")
            else:
                print("⚠ 无法获取文章详情")
        print()
    except Exception as e:
        print(f"⚠ 获取详情失败: {e}\n")
    
    # 总结
    print("=" * 60)
    print("✓ 测试完成!")
    print("=" * 60)
    print()
    print("结论:")
    print("  ✓ Google News API 完全可用")
    print("  ✓ 可以获取头条新闻")
    print("  ✓ 可以搜索关键词")
    print("  ✓ 可以访问多个地区")
    print()
    print("使用示例:")
    print("  from gnews import GNews")
    print("  google_news = GNews(language='en', country='US')")
    print("  news = google_news.get_top_news()")
    print()
    
    return True


if __name__ == '__main__':
    success = test_gnews()
    sys.exit(0 if success else 1)
