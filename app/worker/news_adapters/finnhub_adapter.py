"""
FinnHub新闻源适配器
使用FinnHub API获取美股新闻
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os
import aiohttp

from app.worker.news_adapters.base import NewsSourceAdapter, create_standard_news_item

logger = logging.getLogger(__name__)


class FinnHubAdapter(NewsSourceAdapter):
    """FinnHub新闻源适配器"""
    
    def __init__(self):
        super().__init__("finnhub")
        self.api_key = os.getenv("FINNHUB_API_KEY", "")
        self.base_url = "https://finnhub.io/api/v1"
    
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
            if not self.api_key:
                logger.warning(f"[FinnHub] API Key未配置")
                return []
            
            # 标准化股票代码（去除.HK等后缀）
            clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
            
            # 调用FinnHub API
            url = f"{self.base_url}/company-news"
            params = {
                "symbol": clean_symbol,
                "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d"),
                "token": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        raw_news_list = await response.json()
                    else:
                        logger.warning(f"[FinnHub] API返回错误: {response.status}")
                        return []
            
            if not raw_news_list:
                return []
            
            # 格式化为统一格式
            news_list = [
                self.normalize_news(raw_news, symbol)
                for raw_news in raw_news_list[:limit]
            ]
            
            logger.debug(f"[FinnHub] {symbol} 获取到 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"[FinnHub] 获取新闻失败: {symbol} - {e}")
            raise
    
    def normalize_news(self, raw_news: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        格式化FinnHub新闻为统一格式
        
        Args:
            raw_news: FinnHub原始新闻
            symbol: 股票代码
            
        Returns:
            标准化的新闻字典
        """
        # 解析发布时间
        publish_time = datetime.utcnow()
        if "datetime" in raw_news:
            try:
                publish_time = datetime.fromtimestamp(raw_news["datetime"])
            except:
                pass
        
        return create_standard_news_item(
            symbol=symbol,
            title=raw_news.get("headline", ""),
            source="FinnHub",
            summary=raw_news.get("summary", ""),
            content=raw_news.get("summary", ""),
            source_type="api",
            url=raw_news.get("url", ""),
            publish_time=publish_time,
            sentiment="neutral",
            relevance_score=0.8,  # FinnHub个股新闻相关性高
            tags=[]
        )
