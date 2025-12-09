#!/usr/bin/env python3
"""
数据库连接测试脚本
测试MongoDB和Redis的连接和基本读写功能
"""

import os
import sys
from datetime import datetime

# 测试结果
results = {
    "mongodb": {"connected": False, "read": False, "write": False, "error": None},
    "redis": {"connected": False, "read": False, "write": False, "error": None}
}

print("=" * 60)
print("数据库连接测试")
print("=" * 60)
print()

# ==================== MongoDB测试 ====================
print("1. 测试MongoDB连接...")
print("-" * 60)

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    
    # 从环境变量读取配置
    mongo_host = os.getenv("MONGODB_HOST", "localhost")
    mongo_port = int(os.getenv("MONGODB_PORT", "27017"))
    mongo_user = os.getenv("MONGODB_USERNAME", "admin")
    mongo_pass = os.getenv("MONGODB_PASSWORD", "tradingagents123")
    mongo_db = os.getenv("MONGODB_DATABASE", "tradingagents")
    
    print(f"连接参数:")
    print(f"  Host: {mongo_host}")
    print(f"  Port: {mongo_port}")
    print(f"  User: {mongo_user}")
    print(f"  Database: {mongo_db}")
    print()
    
    # 连接MongoDB
    client = MongoClient(
        host=mongo_host,
        port=mongo_port,
        username=mongo_user,
        password=mongo_pass,
        serverSelectionTimeoutMS=5000
    )
    
    # 测试连接
    client.admin.command('ping')
    results["mongodb"]["connected"] = True
    print("✅ MongoDB连接成功!")
    print()
    
    # 测试写入
    print("测试写入数据...")
    db = client[mongo_db]
    test_collection = db["test_connection"]
    
    test_doc = {
        "test_type": "connection_test",
        "timestamp": datetime.now(),
        "message": "This is a test document"
    }
    
    insert_result = test_collection.insert_one(test_doc)
    results["mongodb"]["write"] = True
    print(f"✅ 写入成功! Document ID: {insert_result.inserted_id}")
    print()
    
    # 测试读取
    print("测试读取数据...")
    found_doc = test_collection.find_one({"_id": insert_result.inserted_id})
    if found_doc:
        results["mongodb"]["read"] = True
        print("✅ 读取成功!")
        print(f"  Document: {found_doc}")
    else:
        print("❌ 读取失败!")
    print()
    
    # 清理测试数据
    test_collection.delete_one({"_id": insert_result.inserted_id})
    print("🧹 测试数据已清理")
    
    client.close()
    
except ImportError:
    results["mongodb"]["error"] = "pymongo未安装"
    print("❌ 错误: pymongo未安装")
    print("   请运行: pip install pymongo")
except ConnectionFailure as e:
    results["mongodb"]["error"] = f"连接失败: {str(e)}"
    print(f"❌ MongoDB连接失败: {e}")
except ServerSelectionTimeoutError as e:
    results["mongodb"]["error"] = f"连接超时: {str(e)}"
    print(f"❌ MongoDB连接超时: {e}")
    print("   请检查:")
    print("   1. MongoDB服务是否启动")
    print("   2. 网络连接是否正常")
    print("   3. 防火墙设置")
except Exception as e:
    results["mongodb"]["error"] = str(e)
    print(f"❌ MongoDB测试失败: {e}")

print()
print()

# ==================== Redis测试 ====================
print("2. 测试Redis连接...")
print("-" * 60)

try:
    import redis
    from redis.exceptions import ConnectionError, TimeoutError
    
    # 从环境变量读取配置
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_pass = os.getenv("REDIS_PASSWORD", "tradingagents123")
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    print(f"连接参数:")
    print(f"  Host: {redis_host}")
    print(f"  Port: {redis_port}")
    print(f"  DB: {redis_db}")
    print()
    
    # 连接Redis
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        db=redis_db,
        socket_connect_timeout=5,
        decode_responses=True
    )
    
    # 测试连接
    r.ping()
    results["redis"]["connected"] = True
    print("✅ Redis连接成功!")
    print()
    
    # 测试写入
    print("测试写入数据...")
    test_key = "test:connection"
    test_value = f"Connection test at {datetime.now()}"
    
    r.set(test_key, test_value, ex=60)  # 60秒过期
    results["redis"]["write"] = True
    print(f"✅ 写入成功! Key: {test_key}")
    print()
    
    # 测试读取
    print("测试读取数据...")
    retrieved_value = r.get(test_key)
    if retrieved_value:
        results["redis"]["read"] = True
        print("✅ 读取成功!")
        print(f"  Value: {retrieved_value}")
    else:
        print("❌ 读取失败!")
    print()
    
    # 清理测试数据
    r.delete(test_key)
    print("🧹 测试数据已清理")
    
    r.close()
    
except ImportError:
    results["redis"]["error"] = "redis未安装"
    print("❌ 错误: redis未安装")
    print("   请运行: pip install redis")
except ConnectionError as e:
    results["redis"]["error"] = f"连接失败: {str(e)}"
    print(f"❌ Redis连接失败: {e}")
except TimeoutError as e:
    results["redis"]["error"] = f"连接超时: {str(e)}"
    print(f"❌ Redis连接超时: {e}")
    print("   请检查:")
    print("   1. Redis服务是否启动")
    print("   2. 网络连接是否正常")
    print("   3. 防火墙设置")
except Exception as e:
    results["redis"]["error"] = str(e)
    print(f"❌ Redis测试失败: {e}")

print()
print()

# ==================== 测试总结 ====================
print("=" * 60)
print("测试总结")
print("=" * 60)
print()

# MongoDB总结
print("MongoDB:")
print(f"  连接: {'✅ 成功' if results['mongodb']['connected'] else '❌ 失败'}")
print(f"  写入: {'✅ 成功' if results['mongodb']['write'] else '❌ 失败'}")
print(f"  读取: {'✅ 成功' if results['mongodb']['read'] else '❌ 失败'}")
if results['mongodb']['error']:
    print(f"  错误: {results['mongodb']['error']}")
print()

# Redis总结
print("Redis:")
print(f"  连接: {'✅ 成功' if results['redis']['connected'] else '❌ 失败'}")
print(f"  写入: {'✅ 成功' if results['redis']['write'] else '❌ 失败'}")
print(f"  读取: {'✅ 成功' if results['redis']['read'] else '❌ 失败'}")
if results['redis']['error']:
    print(f"  错误: {results['redis']['error']}")
print()

# 总体结果
all_passed = (
    results['mongodb']['connected'] and 
    results['mongodb']['write'] and 
    results['mongodb']['read'] and
    results['redis']['connected'] and 
    results['redis']['write'] and 
    results['redis']['read']
)

if all_passed:
    print("🎉 所有测试通过!")
    print("   数据库连接正常,可以正常使用")
    sys.exit(0)
else:
    print("⚠️  部分测试失败")
    print("   请检查上述错误信息并修复")
    sys.exit(1)
