#!/usr/bin/env python3
"""
新闻收集配置检查脚本
检查 MongoDB 中的新闻自动收集配置
"""

from pymongo import MongoClient
from datetime import datetime
import json


def check_scheduler_config():
    """检查新闻收集调度配置"""
    
    print("=" * 80)
    print("📊 新闻收集配置检查")
    print("=" * 80)
    
    try:
        # 连接 MongoDB
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["tradingagents"]
        
        print("\n✅ MongoDB 连接成功")
        
        # 检查可能存储配置的集合
        collections_to_check = [
            "system_config",
            "scheduler_config",
            "user_preferences",
            "users",
            "settings"
        ]
        
        print("\n🔍 检查可能的配置集合...")
        print("-" * 80)
        
        found_config = False
        
        for coll_name in collections_to_check:
            if coll_name in db.list_collection_names():
                print(f"\n📁 集合: {coll_name}")
                
                # 查找所有文档
                docs = list(db[coll_name].find().limit(10))
                
                if docs:
                    print(f"  ✅ 找到 {len(docs)} 个文档")
                    
                    for i, doc in enumerate(docs, 1):
                        print(f"\n  文档 {i}:")
                        
                        # 移除 _id 以便更好地显示
                        doc_copy = doc.copy()
                        if '_id' in doc_copy:
                            doc_copy['_id'] = str(doc_copy['_id'])
                        
                        # 检查是否包含新闻收集相关的字段
                        news_related_keys = [
                            'auto_collect', 'collection_days', 'collection_time',
                            'schedule_time', 'news_collection', 'scheduler'
                        ]
                        
                        has_news_config = any(key in doc_copy for key in news_related_keys)
                        
                        if has_news_config:
                            print(f"  🎯 发现新闻收集配置！")
                            found_config = True
                        
                        # 打印文档内容
                        print(f"  {json.dumps(doc_copy, indent=4, ensure_ascii=False, default=str)}")
                else:
                    print(f"  ⚠️ 集合为空")
            else:
                print(f"\n📁 集合: {coll_name} - ❌ 不存在")
        
        # 检查 APScheduler 任务配置
        print("\n" + "=" * 80)
        print("🔍 检查 APScheduler 任务配置...")
        print("-" * 80)
        
        # 检查是否有 apscheduler_jobs 集合（APScheduler 默认存储）
        if "apscheduler_jobs" in db.list_collection_names():
            jobs = list(db.apscheduler_jobs.find())
            print(f"\n✅ 找到 {len(jobs)} 个 APScheduler 任务")
            
            for job in jobs:
                print(f"\n任务 ID: {job.get('_id')}")
                print(f"  下次运行: {job.get('next_run_time')}")
                if 'job_state' in job:
                    print(f"  任务状态: {job.get('job_state')[:100]}...")
        else:
            print("\n⚠️ 未找到 apscheduler_jobs 集合")
        
        # 总结
        print("\n" + "=" * 80)
        print("📋 检查总结")
        print("=" * 80)
        
        if found_config:
            print("✅ 找到新闻收集配置")
        else:
            print("❌ 未找到新闻收集配置！")
            print("⚠️ 这意味着前端的\"保存设置\"功能可能没有正常工作")
        
        print("\n💡 建议检查的字段:")
        print("  - auto_collect: 是否启用自动收集")
        print("  - collection_days: 收集天数（应该是 30）")
        print("  - collection_time 或 schedule_time: 收集时间")
        print("  - 时间字段类型: 字符串 \"02:00\" 还是列表 [\"02:00\"]")
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_scheduler_config()
