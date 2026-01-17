
import os
import sys
import pandas as pd
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from tradingagents.dataflows.providers.china.akshare import AKShareProvider

def test():
    provider = AKShareProvider()
    print("Testing _get_stock_news_direct for 01810...")
    # 模拟 Docker 环境以触发 _get_stock_news_direct
    os.environ['DOCKER_CONTAINER'] = 'true'
    
    # 强制调用私有方法进行测试
    res = provider._get_stock_news_direct('01810', limit=5)
    
    if res is not None:
        print(f"\n--- Success! Found {len(res)} news ---")
        print(res.head())
    else:
        print("\n--- Failed: result is None ---")

if __name__ == "__main__":
    test()
