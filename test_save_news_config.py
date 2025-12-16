#!/usr/bin/env python3
"""
测试新闻收集配置保存
手动保存配置到数据库并验证
"""

from pymongo import MongoClient
from datetime import datetime


def test_save_config():
    """测试保存配置到数据库"""
    
    print("=" * 80)
    print("🧪 测试新闻收集配置保存")
    print("=" * 80)
    
    try:
        # 连接 MongoDB
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["tradingagents"]
        
        print("\n✅ MongoDB 连接成功")
        
        # 准备测试配置
        test_config = {
            "user_id": "default_user",
            "auto_collect": True,
            "collection_days": 30,
            "schedule_times": ["02:00", "14:00"],  # 🔥 多个时间点！
            "updated_at": datetime.now()
        }
        
        print(f"\n📝 准备保存配置:")
        print(f"  - 自动收集: {test_config['auto_collect']}")
        print(f"  - 收集天数: {test_config['collection_days']}")
        print(f"  - 时间点: {test_config['schedule_times']}")
        
        # 保存到数据库
        result = db.system_config.update_one(
            {"user_id": "default_user"},
            {"$set": test_config},
            upsert=True
        )
        
        print(f"\n✅ 保存成功！")
        print(f"  - 匹配: {result.matched_count}")
        print(f"  - 修改: {result.modified_count}")
        print(f"  - Upsert ID: {result.upserted_id}")
        
        # 验证保存结果
        print(f"\n🔍 验证保存结果...")
        saved_config = db.system_config.find_one({"user_id": "default_user"})
        
        if saved_config:
            print(f"\n✅ 配置已保存到数据库！")
            print(f"\n📋 保存的配置:")
            print(f"  - user_id: {saved_config.get('user_id')}")
            print(f"  - auto_collect: {saved_config.get('auto_collect')}")
            print(f"  - collection_days: {saved_config.get('collection_days')}")
            print(f"  - schedule_times: {saved_config.get('schedule_times')}")
            print(f"  - updated_at: {saved_config.get('updated_at')}")
            
            # 🔥 关键验证：schedule_times 是列表
            schedule_times = saved_config.get('schedule_times')
            if isinstance(schedule_times, list):
                print(f"\n✅ schedule_times 是列表类型！")
                print(f"  - 类型: {type(schedule_times)}")
                print(f"  - 长度: {len(schedule_times)}")
                print(f"  - 值: {schedule_times}")
            else:
                print(f"\n❌ schedule_times 不是列表！类型: {type(schedule_times)}")
        else:
            print(f"\n❌ 配置未找到！")
        
        client.close()
        
        print(f"\n" + "=" * 80)
        print(f"✅ 测试完成！")
        print(f"=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_save_config()
