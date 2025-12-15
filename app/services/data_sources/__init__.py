"""
Data sources subpackage.
Expose adapters and manager for backward-compatible imports.
"""
from .base import DataSourceAdapter
# from .tushare_adapter import TushareAdapter  # 注释掉：模块缺失
from .akshare_adapter import AKShareAdapter
from .baostock_adapter import BaoStockAdapter
from .manager import DataSourceManager

__all__ = ['DataSourceAdapter', 'AKShareAdapter', 'BaoStockAdapter', 'DataSourceManager']
