"""
新闻源适配器抽象基类
定义统一接口，所有新闻源适配器必须实现此接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NewsSourceAdapter(ABC):
    """新闻源适配器抽象基类"""
    
    def __init__(self, source_name: str):
        """
        初始化适配器
        
        Args:
            source_name: 新闻源名称（如 "akshare", "alpha_vantage"）
        """
        self.source_name = source_name
        self.enabled = True
        self.error_count = 0
        self.success_count = 0
    
    @abstractmethod
    async def get_news(
        self,
        symbol: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取指定股票的新闻（必须实现）
        
        Args:
            symbol: 股票代码
            limit: 最大新闻数量
            
        Returns:
            新闻列表，每条新闻为字典格式
        """
        pass
    
    @abstractmethod
    def normalize_news(self, raw_news: Any) -> Dict[str, Any]:
        """
        将原始新闻格式化为统一格式（必须实现）
        
        Args:
            raw_news: 原始新闻数据
            
        Returns:
            标准化的新闻字典
        """
        pass
    
    def is_available(self) -> bool:
        """
        检查新闻源是否可用
        
        Returns:
            是否可用
        """
        return self.enabled and self.error_count < 10
    
    def record_success(self):
        """记录成功"""
        self.success_count += 1
        # 成功后重置错误计数
        if self.error_count > 0:
            self.error_count = max(0, self.error_count - 1)
    
    def record_error(self):
        """记录错误"""
        self.error_count += 1
        # 错误过多时自动禁用
        if self.error_count >= 10:
            logger.warning(f"[{self.source_name}] 错误次数过多，自动禁用")
            self.enabled = False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "source_name": self.source_name,
            "enabled": self.enabled,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "is_available": self.is_available()
        }


def create_standard_news_item(
    symbol: str,
    title: str,
    source: str,
    **kwargs
) -> Dict[str, Any]:
    """
    创建标准新闻格式
    
    Args:
        symbol: 股票代码
        title: 新闻标题
        source: 新闻源名称
        **kwargs: 其他可选字段
        
    Returns:
        标准化的新闻字典
    """
    return {
        "symbol": symbol,
        "title": title,
        "summary": kwargs.get("summary", ""),
        "content": kwargs.get("content", ""),
        "source": source,
        "source_type": kwargs.get("source_type", "api"),
        "url": kwargs.get("url", ""),
        "publish_time": kwargs.get("publish_time", datetime.utcnow()),
        "sentiment": kwargs.get("sentiment", "neutral"),
        "relevance_score": kwargs.get("relevance_score", 0.5),
        "tags": kwargs.get("tags", []),
        "created_at": datetime.utcnow()
    }
