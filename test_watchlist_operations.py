#!/usr/bin/env python3
"""
模拟前端操作验证Watchlist功能
1. 添加 02525 到自选股
2. 删除 00700 从自选股
3. 验证数据库变化
"""
import sys
sys.path.insert(0, '/app')

from pymongo import MongoClient
from datetime import datetime

def test_watchlist_operations():
    """测试自选股增删操作"""
    
    print("=" * 60)
    print("🧪 模拟前端操作测试")
    print("=" * 60)
    
    # 连接数据库
    mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client["tradingagents"]
    user_id = "default_user"
    
    # 1. 查看当前自选股
    print("\n📊 当前自选股列表:")
    user_doc = db.user_favorites.find_one({"user_id": user_id})
    if user_doc:
        for i, fav in enumerate(user_doc.get("favorites", []), 1):
            print(f"  {i}. {fav.get('stock_code')} - {fav.get('stock_name')}")
    
    # 2. 添加 02525（模拟前端add_stock_to_db函数）
    print("\n➕ 添加 02525.HK 到自选股...")
    
    # 检查是否已存在
    existing = db.user_favorites.find_one({
        "user_id": user_id,
        "favorites.stock_code": "02525.HK"
    })
    
    if existing:
        print("  ⚠️ 02525.HK 已在自选股中")
    else:
        favorite_stock = {
            "stock_code": "02525.HK",
            "stock_name": "02525.HK",  # 暂时使用代码作为名称
            "market": "港股",
            "added_at": datetime.utcnow(),
            "tags": [],
            "notes": "",
            "alert_price_high": None,
            "alert_price_low": None
        }
        
        result = db.user_favorites.update_one(
            {"user_id": user_id},
            {
                "$setOnInsert": {
                    "user_id": user_id,
                    "created_at": datetime.utcnow()
                },
                "$push": {"favorites": favorite_stock},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True
        )
        
        if result.acknowledged:
            print("  ✅ 添加成功！")
        else:
            print("  ❌ 添加失败！")
    
    # 3. 删除 00700（模拟前端remove_stock_from_db函数）
    print("\n🗑️ 删除 00700.HK 从自选股...")
    
    result = db.user_favorites.update_one(
        {"user_id": user_id},
        {
            "$pull": {"favorites": {"stock_code": "00700.HK"}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.modified_count > 0:
        print("  ✅ 删除成功！")
    else:
        print("  ⚠️ 未找到 00700.HK 或已删除")
    
    # 4. 验证最终结果
    print("\n📊 操作后的自选股列表:")
    user_doc = db.user_favorites.find_one({"user_id": user_id})
    if user_doc:
        favorites = user_doc.get("favorites", [])
        print(f"  总数: {len(favorites)}")
        for i, fav in enumerate(favorites, 1):
            print(f"  {i}. {fav.get('stock_code')} - {fav.get('stock_name')}")
    
    client.close()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_watchlist_operations()
