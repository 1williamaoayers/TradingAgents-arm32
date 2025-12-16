"""
RSS新闻源适配器
从RSS源获取中文财经新闻并过滤相关内容
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import feedparser

from app.worker.news_adapters.base import NewsSourceAdapter, create_standard_news_item

logger = logging.getLogger(__name__)


class RSSAdapter(NewsSourceAdapter):
    """RSS新闻源适配器"""
    
    def __init__(self):
        super().__init__("rss")
        # RSS源列表（使用报告中验证过的源）
        self.rss_feeds = [
            # CDX RSSHub 中文财经快讯
            "https://rss.cdx.hidns.co/jin10/flash",  # 金十数据
            "https://rss.cdx.hidns.co/cls/telegraph",  # 财联社
            "https://rss.cdx.hidns.co/gelonghui/live",  # 格隆汇
            "https://rss.cdx.hidns.co/wallstreetcn/live/global",  # 华尔街见闻
            # Google News
            "https://news.google.com/rss?hl=zh-HK&gl=HK&ceid=HK:zh-Hant",  # 香港版
            "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",  # 美国版
            # Yahoo Finance
            "https://finance.yahoo.com/news/rssindex",  # 最新新闻
        ]
    
    async def get_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取RSS新闻
        
        注意：RSS返回的是通用财经新闻，不针对特定股票
        所有新闻都会被存储，由LLM判断相关性
        
        Args:
            symbol: 股票代码（仅用于标记，不用于过滤）
            limit: 最大新闻数量
            
        Returns:
            新闻列表
        """
        try:
            all_news = []
            
            # 获取所有RSS源的新闻
            for feed_url in self.rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    
                    # 每个源最多取100条，总共不超过limit
                    for entry in feed.entries[:100]:
                        # 直接添加所有新闻，不过滤
                        news_item = self.normalize_news(entry, symbol)
                        all_news.append(news_item)
                        
                        if len(all_news) >= limit:
                            break
                    
                    if len(all_news) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"[RSS] 解析RSS源失败 {feed_url}: {e}")
                    continue
            
            # 限制总数
            all_news = all_news[:limit]
            
            if all_news:
                logger.info(f"[RSS] 获取到 {len(all_news)} 条通用财经新闻")
            
            return all_news
            
        except Exception as e:
            logger.error(f"[RSS] 获取新闻失败: {e}")
            return []
    
    def normalize_news(self, raw_news: Any, symbol: str) -> Dict[str, Any]:
        """
        格式化RSS新闻为统一格式
        
        Args:
            raw_news: RSS原始新闻
            symbol: 股票代码
            
        Returns:
            标准化的新闻字典
        """
        # 解析发布时间
        publish_time = datetime.utcnow()
        if hasattr(raw_news, "published_parsed"):
            try:
                from time import mktime
                publish_time = datetime.fromtimestamp(mktime(raw_news.published_parsed))
            except:
                pass
        
        # 获取内容
        summary = ""
        if hasattr(raw_news, "summary"):
            summary = raw_news.summary
        elif hasattr(raw_news, "description"):
            summary = raw_news.description
        
        return create_standard_news_item(
            symbol=symbol,
            title=raw_news.get("title", ""),
            source="RSS",
            summary=summary,
            content=summary,
            source_type="rss",
            url=raw_news.get("link", ""),
            publish_time=publish_time,
            sentiment="neutral",
            relevance_score=0.6,  # RSS新闻相关性较低（需要过滤）
            tags=[]
        )
    
    def _get_company_name(self, symbol: str) -> str:
        """
        根据股票代码获取公司名称
        
        Args:
            symbol: 股票代码
            
        Returns:
            公司名称
        """
        # 简单映射表
        name_map = {
            "09618": "京东",
            "00700": "腾讯",
            "09988": "阿里",
            "01810": "小米",
            "02525": "禾赛",
        }
        
        clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
        return name_map.get(clean_symbol, "")
