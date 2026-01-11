"""
RSS新闻源适配器
从RSS源获取中文财经新闻并智能过滤相关内容
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
        
        # 股票代码到公司名的映射（用于过滤）
        self.stock_names = {
            "09618": ["京东", "JD", "jd.com"],
            "00700": ["腾讯", "Tencent", "微信", "WeChat"],
            "09988": ["阿里", "阿里巴巴", "Alibaba", "淘宝", "天猫"],
            "01810": ["小米", "Xiaomi", "米家"],
            "02128": ["联塑", "中国联塑"],
            "02525": ["禾赛", "Hesai", "激光雷达"],
            "01024": ["快手", "Kuaishou"],
            "09999": ["网易", "NetEase"],
            "03690": ["美团", "Meituan"],
            "09888": ["百度", "Baidu"],
        }
        
        # 通用港股市场关键词（宽松匹配）
        self.market_keywords = [
            "港股", "恒生", "恒指", "港交所", "南向资金", "北向资金",
            "科技股", "消费股", "金融股", "地产股", "新能源",
            "中概股", "回港", "二次上市", "IPO", "回购",
            "互联网", "电商", "智能驾驶", "AI", "人工智能",
        ]
    
    async def get_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取RSS新闻并智能过滤
        
        Args:
            symbol: 股票代码
            limit: 最大新闻数量
            
        Returns:
            与股票相关的新闻列表
        """
        try:
            all_news = []
            matched_news = []
            
            # 获取该股票的关键词
            clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
            stock_keywords = self.stock_names.get(clean_symbol, [])
            
            # 获取所有RSS源的新闻
            for feed_url in self.rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:50]:  # 每个源最多50条
                        title = entry.get("title", "")
                        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                        content = title + " " + summary
                        
                        # 智能过滤：检查是否与股票相关
                        is_related, match_type = self._check_relevance(
                            content, clean_symbol, stock_keywords
                        )
                        
                        if is_related:
                            news_item = self.normalize_news(entry, symbol)
                            news_item["match_type"] = match_type  # 记录匹配类型
                            matched_news.append(news_item)
                            
                            if len(matched_news) >= limit:
                                break
                    
                    if len(matched_news) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"[RSS] 解析RSS源失败 {feed_url}: {e}")
                    continue
            
            # 限制总数
            matched_news = matched_news[:limit]
            
            if matched_news:
                logger.info(f"[RSS] {symbol}: 获取到 {len(matched_news)} 条相关新闻")
            else:
                logger.info(f"[RSS] {symbol}: 未找到相关新闻")
            
            return matched_news
            
        except Exception as e:
            logger.error(f"[RSS] 获取新闻失败: {e}")
            return []
    
    def _check_relevance(self, content: str, symbol: str, stock_keywords: List[str]) -> tuple:
        """
        检查新闻是否与股票相关（宽松匹配）
        
        Args:
            content: 新闻内容（标题+摘要）
            symbol: 股票代码（不含.HK）
            stock_keywords: 该股票的关键词列表
            
        Returns:
            (是否相关, 匹配类型)
        """
        content_lower = content.lower()
        
        # 1. 精确匹配股票代码
        if symbol in content or f"{symbol}.HK" in content:
            return True, "stock_code"
        
        # 2. 匹配公司名称/关键词
        for keyword in stock_keywords:
            if keyword.lower() in content_lower:
                return True, "company_name"
        
        # 3. 宽松匹配：港股市场通用关键词
        for keyword in self.market_keywords:
            if keyword in content:
                return True, "market_keyword"
        
        return False, None
    
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
            relevance_score=0.7,  # 过滤后的新闻相关性较高
            tags=[]
        )

