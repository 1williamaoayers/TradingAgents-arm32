#!/usr/bin/env python3
"""
财联社新闻获取工具
支持多种方式获取财联社(CLS)的实时财经快讯
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser


class CailianpressNewsProvider:
    """财联社新闻提供者"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.cls.cn'
        }
    
    def get_news_via_rsshub(self, category: str = 'telegraph', max_items: int = 20) -> List[Dict]:
        """
        通过RSSHub获取财联社新闻
        
        Args:
            category: 新闻类别
                - 'telegraph': 电报快讯(推荐)
                - 'depth': 深度文章
                - 'ranking/hot': 热门文章排行榜
            max_items: 最大新闻数量
        
        Returns:
            新闻列表
        """
        try:
            # RSSHub公共实例
            rsshub_urls = [
                f"https://rsshub.app/cls/{category}",
                f"https://rsshub.rssforever.com/cls/{category}",  # 备用实例
            ]
            
            for rsshub_url in rsshub_urls:
                try:
                    print(f"尝试从RSSHub获取: {rsshub_url}")
                    feed = feedparser.parse(rsshub_url)
                    
                    if not feed or not feed.entries:
                        continue
                    
                    news_items = []
                    for entry in feed.entries[:max_items]:
                        news_items.append({
                            'title': entry.get('title', ''),
                            'content': entry.get('summary', ''),
                            'link': entry.get('link', ''),
                            'published': entry.get('published', ''),
                            'source': '财联社',
                            'category': category
                        })
                    
                    if news_items:
                        print(f"✓ 成功获取 {len(news_items)} 条新闻")
                        return news_items
                        
                except Exception as e:
                    print(f"✗ RSSHub实例失败: {e}")
                    continue
            
            print("✗ 所有RSSHub实例都失败")
            return []
            
        except Exception as e:
            print(f"✗ RSSHub获取失败: {e}")
            return []
    
    def get_news_via_api(self, max_items: int = 20) -> List[Dict]:
        """
        通过财联社API获取新闻(非官方接口)
        
        Args:
            max_items: 最大新闻数量
        
        Returns:
            新闻列表
        """
        try:
            # 财联社滚动新闻API
            api_url = "https://www.cls.cn/v1/roll/get_roll_list"
            params = {
                'app': 'CailianpressWeb',
                'os': 'web',
                'sv': '7.7.5',
                'sign': '',  # 可能需要签名
                'rn': max_items
            }
            
            print(f"尝试从财联社API获取新闻...")
            response = requests.get(api_url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 200 and 'data' in data:
                news_list = data['data'].get('roll_data', [])
                
                news_items = []
                for item in news_list[:max_items]:
                    news_items.append({
                        'title': item.get('title', ''),
                        'content': item.get('content', ''),
                        'link': f"https://www.cls.cn/detail/{item.get('id', '')}",
                        'published': item.get('ctime', ''),
                        'source': '财联社',
                        'category': 'api'
                    })
                
                print(f"✓ 成功获取 {len(news_items)} 条新闻")
                return news_items
            else:
                print(f"✗ API返回错误: {data}")
                return []
                
        except Exception as e:
            print(f"✗ API获取失败: {e}")
            return []
    
    def get_news_via_third_party(self, api_key: Optional[str] = None, max_items: int = 20) -> List[Dict]:
        """
        通过第三方API服务获取财联社新闻
        
        第三方服务商:
        - 觅知API: https://www.98dou.cn
        - 小尘API: https://www.xcvts.cn
        
        Args:
            api_key: 第三方API密钥(如果需要)
            max_items: 最大新闻数量
        
        Returns:
            新闻列表
        """
        if not api_key:
            print("⚠ 第三方API需要密钥,请提供api_key参数")
            return []
        
        try:
            # 示例: 觅知API接口
            api_url = "https://api.98dou.cn/api/cls/telegraph"
            params = {
                'key': api_key,
                'num': max_items
            }
            
            print(f"尝试从第三方API获取新闻...")
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 200:
                news_list = data.get('data', [])
                
                news_items = []
                for item in news_list:
                    news_items.append({
                        'title': item.get('title', ''),
                        'content': item.get('content', ''),
                        'link': item.get('url', ''),
                        'published': item.get('time', ''),
                        'source': '财联社',
                        'category': 'third_party'
                    })
                
                print(f"✓ 成功获取 {len(news_items)} 条新闻")
                return news_items
            else:
                print(f"✗ 第三方API返回错误: {data}")
                return []
                
        except Exception as e:
            print(f"✗ 第三方API获取失败: {e}")
            return []
    
    def get_news(self, method: str = 'rsshub', **kwargs) -> List[Dict]:
        """
        获取财联社新闻(统一接口)
        
        Args:
            method: 获取方法
                - 'rsshub': 通过RSSHub(推荐,免费)
                - 'api': 通过财联社API(可能不稳定)
                - 'third_party': 通过第三方API(需要密钥)
            **kwargs: 其他参数
        
        Returns:
            新闻列表
        """
        if method == 'rsshub':
            return self.get_news_via_rsshub(**kwargs)
        elif method == 'api':
            return self.get_news_via_api(**kwargs)
        elif method == 'third_party':
            return self.get_news_via_third_party(**kwargs)
        else:
            print(f"✗ 不支持的方法: {method}")
            return []


def main():
    """测试财联社新闻获取"""
    print("=" * 60)
    print("财联社新闻获取测试")
    print("=" * 60)
    print()
    
    provider = CailianpressNewsProvider()
    
    # 方法1: RSSHub(推荐)
    print("【方法1】通过RSSHub获取财联社电报快讯")
    print("-" * 60)
    news = provider.get_news(method='rsshub', category='telegraph', max_items=5)
    
    if news:
        for i, item in enumerate(news, 1):
            print(f"\n{i}. {item['title']}")
            print(f"   时间: {item['published']}")
            print(f"   链接: {item['link']}")
            if item['content']:
                print(f"   内容: {item['content'][:100]}...")
    else:
        print("未获取到新闻")
    
    print("\n" + "=" * 60)
    
    # 方法2: 财联社API
    print("\n【方法2】通过财联社API获取新闻")
    print("-" * 60)
    news_api = provider.get_news(method='api', max_items=5)
    
    if news_api:
        for i, item in enumerate(news_api, 1):
            print(f"\n{i}. {item['title']}")
            print(f"   时间: {item['published']}")
    else:
        print("未获取到新闻")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
