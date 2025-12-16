#!/usr/bin/env python3
"""
Alpha Vantage新闻工具
获取个股专属新闻，支持全球市场（包括港股、A股、美股）
"""

import logging
import requests
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def get_alpha_vantage_news(ticker: str, limit: int = 15):
    """
    获取Alpha Vantage个股新闻
    
    Args:
        ticker: 股票代码（09618, AAPL等）
        limit: 最大新闻数量
    
    Returns:
        list: 新闻列表，每个新闻包含title, summary, source, url, time_published, sentiment
    """
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        logger.error("[Alpha Vantage] API Key未配置")
        return []
    
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'NEWS_SENTIMENT',
        'tickers': ticker,
        'apikey': api_key,
        'limit': limit,
        'sort': 'LATEST'  # 按时间排序
    }
    
    try:
        logger.info(f"[Alpha Vantage] 请求个股新闻: {ticker}, limit={limit}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 检查是否有错误
        if 'Error Message' in data:
            logger.error(f"[Alpha Vantage] API错误: {data['Error Message']}")
            return []
        
        if 'Note' in data:
            logger.warning(f"[Alpha Vantage] API限制: {data['Note']}")
            return []
        
        if 'feed' in data:
            news_items = data['feed']
            logger.info(f"[Alpha Vantage] ✅ 返回{len(news_items)}条新闻")
            
            # 格式化新闻
            formatted_news = []
            for item in news_items:
                # 提取ticker相关的情绪分数
                ticker_sentiment = None
                if 'ticker_sentiment' in item:
                    for ts in item['ticker_sentiment']:
                        if ts.get('ticker', '').upper() == ticker.upper():
                            ticker_sentiment = ts.get('ticker_sentiment_label', 'Neutral')
                            break
                
                formatted_news.append({
                    'title': item.get('title', '无标题'),
                    'summary': item.get('summary', ''),
                    'source': item.get('source', '未知来源'),
                    'url': item.get('url', ''),
                    'time_published': item.get('time_published', ''),
                    'sentiment': ticker_sentiment or item.get('overall_sentiment_label', 'Neutral'),
                    'relevance_score': item.get('relevance_score', 0)
                })
            
            return formatted_news
        else:
            logger.warning(f"[Alpha Vantage] 未返回新闻数据: {data}")
            return []
            
    except requests.exceptions.Timeout:
        logger.error("[Alpha Vantage] 请求超时")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"[Alpha Vantage] 请求失败: {e}")
        return []
    except Exception as e:
        logger.error(f"[Alpha Vantage] 处理失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def format_alpha_vantage_news(news_items, stock_code):
    """
    格式化Alpha Vantage新闻为markdown
    
    Args:
        news_items: 新闻列表
        stock_code: 股票代码
    
    Returns:
        str: 格式化的markdown文本
    """
    if not news_items:
        return ""
    
    report = f"# {stock_code} 个股新闻 (Alpha Vantage)\n\n"
    report += f"📅 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"📊 新闻数量: {len(news_items)} 条\n\n"
    
    for i, news in enumerate(news_items, 1):
        title = news.get('title', '无标题')
        summary = news.get('summary', '')
        source = news.get('source', '未知来源')
        time_published = news.get('time_published', '')
        sentiment = news.get('sentiment', 'Neutral')
        
        # 格式化时间
        if time_published:
            try:
                # Alpha Vantage时间格式: 20231215T120000
                dt = datetime.strptime(time_published, '%Y%m%dT%H%M%S')
                time_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                time_str = time_published
        else:
            time_str = '未知时间'
        
        # 情绪图标
        sentiment_icon = {
            'Bullish': '📈',
            'Bearish': '📉',
            'Neutral': '➖',
            'Somewhat-Bullish': '📊',
            'Somewhat-Bearish': '📉'
        }.get(sentiment, '➖')
        
        report += f"## {i}. {sentiment_icon} {title}\n\n"
        report += f"**来源**: {source} | **时间**: {time_str}\n"
        report += f"**情绪**: {sentiment}\n\n"
        
        if summary:
            # 限制摘要长度
            summary_text = summary[:500] + '...' if len(summary) > 500 else summary
            report += f"{summary_text}\n\n"
        
        report += "---\n\n"
    
    return report
