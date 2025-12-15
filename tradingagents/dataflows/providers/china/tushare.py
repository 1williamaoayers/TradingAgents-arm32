"""
Tushare数据提供者（占位模块）
此模块仅用于解决导入错误，实际功能已禁用
"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class TushareProvider:
    """Tushare提供者（占位类）"""
    
    def __init__(self):
        logger.warning("⚠️ TushareProvider 已禁用")
        self._available = False
    
    async def connect(self):
        """连接（占位）"""
        logger.warning("⚠️ TushareProvider.connect 已禁用")
        pass
    
    def is_available(self) -> bool:
        """检查是否可用（占位）"""
        return False
    
    async def get_stock_news(self, symbol: str, limit: int = 50, hours_back: int = 24) -> List[Dict[str, Any]]:
        """获取股票新闻（占位）"""
        logger.warning(f"⚠️ TushareProvider.get_stock_news 已禁用 - {symbol}")
        return []
    
    async def get_historical_data(self, symbol: str, start_date: str = None, end_date: str = None, period: str = "daily") -> Optional[Any]:
        """获取历史数据（占位）"""
        logger.warning(f"⚠️ TushareProvider.get_historical_data 已禁用 - {symbol}")
        return None

def get_tushare_provider() -> Optional[TushareProvider]:
    """获取Tushare提供者实例（占位）"""
    logger.warning("⚠️ get_tushare_provider 已禁用 - 返回 None")
    return None
