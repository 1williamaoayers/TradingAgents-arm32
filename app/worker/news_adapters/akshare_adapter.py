"""
AKShare新闻源适配器
复用现有的AKShare提供器获取新闻
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.worker.news_adapters.base import NewsSourceAdapter, create_standard_news_item
from tradingagents.dataflows.providers.china.akshare import get_akshare_provider

logger = logging.getLogger(__name__)


class AKShareAdapter(NewsSourceAdapter):
    """AKShare新闻源适配器"""
    
    def __init__(self):
        super().__init__("akshare")
        self.provider = None
    
    async def initialize(self):
        """初始化AKShare提供器"""
        self.provider = get_akshare_provider()  # 不需要await
        logger.info("✅ AKShare适配器初始化完成")
    
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
            if not self.provider:
                await self.initialize()
            
            # 调用AKShare提供器获取新闻
            raw_news_list = await self.provider.get_stock_news(
                symbol=symbol,
                limit=limit
            )
            
            if not raw_news_list:
                return []
            
            # 格式化为统一格式
            news_list = [
                self.normalize_news(raw_news)
                for raw_news in raw_news_list
            ]
            
            logger.debug(f"[AKShare] {symbol} 获取到 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"[AKShare] 获取新闻失败: {symbol} - {e}")
            raise
    
    def normalize_news(self, raw_news: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化AKShare新闻为统一格式
        
        Args:
            raw_news: AKShare原始新闻
            
        Returns:
            标准化的新闻字典
        """
        return create_standard_news_item(
            symbol=raw_news.get("symbol", ""),
            title=raw_news.get("title", ""),
            source="AKShare",
            summary=raw_news.get("summary", ""),
            content=raw_news.get("content", ""),
            source_type="api",
            url=raw_news.get("url", ""),
            publish_time=raw_news.get("publish_time", datetime.utcnow()),
            sentiment=raw_news.get("sentiment", "neutral"),
            relevance_score=0.7,  # AKShare新闻相关性中等
            tags=raw_news.get("tags", [])
        )
