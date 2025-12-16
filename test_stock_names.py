#!/usr/bin/env python3
"""
测试改进后的股票名称显示功能
测试多只港股，验证真实名称获取
"""
import sys
sys.path.insert(0, '/app')

from pymongo import MongoClient
from datetime import datetime

# 测试股票列表（港股）
test_stocks = [
    ("09618.HK", "港股"),  # 京东集团
    ("00700.HK", "港股"),  # 腾讯控股
    ("09988.HK", "港股"),  # 阿里巴巴
    ("01810.HK", "港股"),  # 小米集团
    ("02525.HK", "港股"),  # 禾赛科技
    ("02128.HK", "港股"),  # 中国联通（验证是否正确）
]

def add_stock_with_real_name(symbol, market):
    """添加股票并获取真实名称（改进版）"""
    mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client["tradingagents"]
    user_id = "test_user"  # 使用测试用户
    
    # 从stock_basic_info获取真实名称
    stock_name = symbol
    try:
        basic_info = db.stock_basic_info.find_one({"symbol": symbol})
        if basic_info:
            stock_name = (
                basic_info.get('name') or 
                basic_info.get('stock_name') or 
                basic_info.get('cn_name') or 
                symbol
            )
            print(f"  ✅ {symbol} -> {stock_name}")
        else:
            print(f"  ⚠️ {symbol} -> 未找到名称，使用代码")
    except Exception as e:
        print(f"  ❌ {symbol} -> 查询失败: {e}")
    
    # 添加到数据库
    favorite_stock = {
        "stock_code": symbol,
        "stock_name": stock_name,
        "market": market,
        "added_at": datetime.utcnow(),
    }
    
    result = db.user_favorites.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {"user_id": user_id, "created_at": datetime.utcnow()},
            "$push": {"favorites": favorite_stock},
            "$set": {"updated_at": datetime.utcnow()}
        },
        upsert=True
    )
    
    client.close()
    return stock_name

def test_stock_names():
    """测试股票名称获取"""
    print("=" * 60)
    print("🧪 测试股票名称获取功能（港股）")
    print("=" * 60)
    
    # 清空测试用户的自选股
    mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
    client = MongoClient(mongo_uri)
    db = client["tradingagents"]
    db.user_favorites.delete_one({"user_id": "test_user"})
    
    print("\n📊 添加测试股票并获取名称:")
    results = []
    for symbol, market in test_stocks:
        stock_name = add_stock_with_real_name(symbol, market)
        results.append((symbol, stock_name))
    
    # 验证结果
    print("\n📋 最终结果:")
    user_doc = db.user_favorites.find_one({"user_id": "test_user"})
    if user_doc:
        for i, fav in enumerate(user_doc.get("favorites", []), 1):
            code = fav.get('stock_code')
            name = fav.get('stock_name')
            print(f"  {i}. {code:12} -> {name}")
    
    client.close()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_stock_names()
