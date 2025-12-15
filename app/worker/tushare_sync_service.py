"""
Tushare同步服务（占位模块）
此模块仅用于解决导入错误，实际功能已禁用
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def run_tushare_basic_info_sync(*args, **kwargs):
    """基础信息同步（占位）"""
    logger.warning("⚠️ Tushare模块已禁用 - run_tushare_basic_info_sync")
    return {"status": "disabled", "message": "Tushare module is disabled"}

async def run_tushare_quotes_sync(*args, **kwargs):
    """行情同步（占位）"""
    logger.warning("⚠️ Tushare模块已禁用 - run_tushare_quotes_sync")
    return {"status": "disabled", "message": "Tushare module is disabled"}

async def run_tushare_historical_sync(*args, **kwargs):
    """历史数据同步（占位）"""
    logger.warning("⚠️ Tushare模块已禁用 - run_tushare_historical_sync")
    return {"status": "disabled", "message": "Tushare module is disabled"}

async def run_tushare_financial_sync(*args, **kwargs):
    """财务数据同步（占位）"""
    logger.warning("⚠️ Tushare模块已禁用 - run_tushare_financial_sync")
    return {"status": "disabled", "message": "Tushare module is disabled"}

async def run_tushare_status_check(*args, **kwargs):
    """状态检查（占位）"""
    logger.warning("⚠️ Tushare模块已禁用 - run_tushare_status_check")
    return {"status": "disabled", "message": "Tushare module is disabled"}

class TushareSyncService:
    """Tushare同步服务（占位类）"""
    
    def __init__(self):
        logger.warning("⚠️ TushareSyncService 已禁用")
        self.provider = None
    
    async def initialize(self):
        """初始化（占位）"""
        logger.warning("⚠️ TushareSyncService.initialize 已禁用")
        pass
    
    async def sync_basic_info(self, *args, **kwargs):
        """同步基础信息（占位）"""
        logger.warning("⚠️ TushareSyncService.sync_basic_info 已禁用")
        return {"status": "disabled"}

async def get_tushare_sync_service():
    """获取Tushare同步服务实例（占位）"""
    logger.warning("⚠️ get_tushare_sync_service 已禁用")
    return None
