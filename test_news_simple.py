#!/usr/bin/env python3
"""
简化的新闻抓取测试 - 直接使用 MongoDB 连接
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient

async def test_news_simple():
    """简化测试：直接连接 MongoDB 并抓取新闻"""
    
    print("🚀 开始测试新闻抓取: 00700.HK")
    print("=" * 60)
    
    try:
        # 1. 连接 MongoDB
        print("\n📡 连接 MongoDB...")
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # 测试连接
        await client.server_info()
        print("✅ MongoDB 连接成功")
        
        db = client["tradingagents"]
        
        # 2. 获取自选股列表
        print("\n📌 获取自选股列表...")
        latest_doc = await db.user_favorites.find_one(
            {"favorites": {"$exists": True, "$ne": []}},
            {"favorites.stock_code": 1, "_id": 0},
            sort=[("updated_at", -1)]
        )
        
        if latest_doc:
            favorites = latest_doc.get("favorites", [])
            stock_codes = [f.get("stock_code") for f in favorites]
            print(f"✅ 找到 {len(stock_codes)} 只自选股:")
            for code in stock_codes:
                print(f"  - {code}")
        else:
            print("⚠️ 未找到自选股")
            return
        
        # 3. 检查 00700.HK 是否在列表中
        if "00700.HK" in stock_codes:
            print("\n✅ 00700.HK 在自选股列表中")
        else:
            print("\n⚠️ 00700.HK 不在自选股列表中")
        
        # 4. 使用 AKShare 抓取新闻
        print("\n🔍 开始抓取 00700.HK 新闻...")
        
        try:
            import akshare as ak
            
            # 获取个股新闻
            news_df = ak.stock_news_em(symbol="00700")
            
            if news_df is not None and not news_df.empty:
                print(f"✅ 成功获取 {len(news_df)} 条新闻")
                
                # 显示前3条新闻标题
                print("\n📰 新闻标题示例:")
                for idx, row in news_df.head(3).iterrows():
                    title = row.get('新闻标题', row.get('title', '无标题'))
                    pub_time = row.get('发布时间', row.get('pub_time', ''))
                    print(f"  {idx+1}. {title}")
                    if pub_time:
                        print(f"     发布时间: {pub_time}")
                
                # 保存到数据库
                print("\n💾 保存新闻到数据库...")
                news_collection = db["stock_news"]
                
                saved_count = 0
                for idx, row in news_df.head(5).iterrows():
                    news_doc = {
                        "stock_code": "00700.HK",
                        "title": row.get('新闻标题', row.get('title', '')),
                        "content": row.get('新闻内容', row.get('content', '')),
                        "source": row.get('文章来源', row.get('source', 'AKShare')),
                        "pub_time": row.get('发布时间', row.get('pub_time', '')),
                        "url": row.get('新闻链接', row.get('url', '')),
                        "data_source": "akshare",
                        "created_at": asyncio.get_event_loop().time()
                    }
                    
                    await news_collection.update_one(
                        {"stock_code": "00700.HK", "title": news_doc["title"]},
                        {"$set": news_doc},
                        upsert=True
                    )
                    saved_count += 1
                
                print(f"✅ 成功保存 {saved_count} 条新闻到数据库")
                
            else:
                print("⚠️ 未获取到新闻数据")
        
        except Exception as e:
            print(f"❌ AKShare 抓取失败: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成！")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_news_simple())
