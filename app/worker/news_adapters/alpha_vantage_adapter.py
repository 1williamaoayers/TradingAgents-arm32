"""
Alpha Vantage新闻源适配器
使用Alpha Vantage API获取个股新闻
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import os

from app.worker.news_adapters.base import NewsSourceAdapter, create_standard_news_item

logger = logging.getLogger(__name__)


class AlphaVantageAdapter(NewsSourceAdapter):
    """Alpha Vantage新闻源适配器"""
    
    def __init__(self):
        super().__init__("alpha_vantage")
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.daily_quota = 25
        self.calls_today = 0
    
    async def get_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取指定股票的新闻
        
        Args:
            symbol: 股票代码
            limit: 最大新闻数量
            
        Returns:
            新闻列表
        """
        try:
            # 检查API配额
            if self.calls_today >= self.daily_quota:
                logger.warning(f"[Alpha Vantage] 已达到每日配额限制 ({self.daily_quota})")
                return []
            
            if not self.api_key:
                logger.warning(f"[Alpha Vantage] API Key未配置")
                return []
            
            # 导入Alpha Vantage工具
            from tradingagents.tools.alpha_vantage_news import get_alpha_vantage_news
            
            # 标准化股票代码（去除.HK等后缀）
            clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
            
            # 调用API获取新闻
            raw_news_list = get_alpha_vantage_news(
                ticker=clean_symbol,
                limit=min(limit, 10)  # Alpha Vantage限制每次10条
            )
            
            self.calls_today += 1
            
            if not raw_news_list:
                return []
            
            # 格式化为统一格式
            news_list = [
                self.normalize_news(raw_news, symbol)
                for raw_news in raw_news_list
            ]
            
            logger.debug(f"[Alpha Vantage] {symbol} 获取到 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"[Alpha Vantage] 获取新闻失败: {symbol} - {e}")
            raise
    
    def normalize_news(self, raw_news: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        格式化Alpha Vantage新闻为统一格式
        
        Args:
            raw_news: Alpha Vantage原始新闻
            symbol: 股票代码
            
        Returns:
            标准化的新闻字典
        """
        # 解析发布时间
        publish_time = datetime.utcnow()
        if "time_published" in raw_news:
            try:
                time_str = raw_news["time_published"]
                publish_time = datetime.strptime(time_str, "%Y%m%dT%H%M%S")
            except:
                pass
        
        # 解析情绪
        sentiment = "neutral"
        if "overall_sentiment_label" in raw_news:
            label = raw_news["overall_sentiment_label"].lower()
            if "positive" in label or "bullish" in label:
                sentiment = "positive"
            elif "negative" in label or "bearish" in label:
                sentiment = "negative"
        
        return create_standard_news_item(
            symbol=symbol,
            title=raw_news.get("title", ""),
            source="Alpha Vantage",
            summary=raw_news.get("summary", ""),
            content=raw_news.get("summary", ""),  # Alpha Vantage只有summary
            source_type="api",
            url=raw_news.get("url", ""),
            publish_time=publish_time,
            sentiment=sentiment,
            relevance_score=float(raw_news.get("relevance_score", 0.8)),
            tags=raw_news.get("topics", [])
        )
