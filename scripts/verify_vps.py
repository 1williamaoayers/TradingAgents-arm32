#!/usr/bin/env python3
"""
VPS 部署验证脚本 (VPS Deployment Verification Script)
用于在 Docker 容器内部验证 TradingAgents 的环境、连接和基本功能。

用法:
    docker exec -it tradingagents python scripts/verify_vps.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_vps")

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_pass(msg):
    print(f"{Colors.GREEN}✅ PASS: {msg}{Colors.END}")

def print_fail(msg):
    print(f"{Colors.RED}❌ FAIL: {msg}{Colors.END}")

def print_warn(msg):
    print(f"{Colors.YELLOW}⚠️  WARN: {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  INFO: {msg}{Colors.END}")

async def check_mongodb():
    """检查 MongoDB 连接"""
    print_info("正在检查 MongoDB 连接...")
    try:
        from app.core.database import init_db, close_db, get_database_health
        await init_db()
        health = await get_database_health()
        await close_db()
        
        if health.get("status") == "connected":
            print_pass(f"MongoDB 连接成功 ({os.getenv('MONGODB_HOST', 'localhost')})")
            return True
        else:
            print_fail(f"MongoDB 连接状态异常: {health}")
            return False
    except ImportError:
        print_warn("无法导入数据库模块，跳过 MongoDB 检查 (可能运行在纯 Streamlit 模式)")
        # 尝试使用pymongo直接连接
        try:
            import pymongo
            host = os.getenv('MONGODB_HOST', 'localhost')
            port = int(os.getenv('MONGODB_PORT', 27017))
            uri = f"mongodb://{os.getenv('MONGODB_USERNAME', '')}:{os.getenv('MONGODB_PASSWORD', '')}@{host}:{port}"
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.server_info()
            print_pass(f"MongoDB (pymongo) 连接成功")
            return True
        except Exception as e:
            print_fail(f"MongoDB 连接失败: {e}")
            return False
    except Exception as e:
        print_fail(f"MongoDB 检查出错: {e}")
        return False

async def check_redis():
    """检查 Redis 连接"""
    print_info("正在检查 Redis 连接...")
    try:
        from app.core.redis_client import init_redis, close_redis, RedisService
        await init_redis()
        redis = await RedisService.get_redis()
        if redis:
            await redis.ping()
            print_pass(f"Redis 连接成功 ({os.getenv('REDIS_HOST', 'localhost')})")
            await close_redis()
            return True
        else:
            print_fail("Redis 客户端初始化失败")
            return False
    except ImportError:
        print_warn("无法导入 Redis 模块，尝试直接连接")
        try:
            import redis
            host = os.getenv('REDIS_HOST', 'localhost')
            port = int(os.getenv('REDIS_PORT', 6379))
            password = os.getenv('REDIS_PASSWORD')
            r = redis.Redis(host=host, port=port, password=password, socket_timeout=2)
            if r.ping():
                print_pass("Redis (direct) 连接成功")
                return True
        except Exception as e:
            print_fail(f"Redis 连接失败: {e}")
            return False
    except Exception as e:
        print_fail(f"Redis 检查出错: {e}")
        return False

def check_env_vars():
    """检查关键环境变量"""
    print_info("正在检查环境变量...")
    required_keys = [
        "DEEPSEEK_API_KEY",
        "DASHSCOPE_API_KEY",
        "OPENAI_API_KEY", 
        "FINNHUB_API_KEY"
    ]
    
    found_llm = False
    
    # 检查 LLM Key
    for key in ["DEEPSEEK_API_KEY", "DASHSCOPE_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"]:
        val = os.getenv(key)
        if val and len(val) > 5:
            print_pass(f"发现 LLM Key: {key}")
            found_llm = True
            
    if not found_llm:
        print_fail("未发现任何有效的 LLM API Key (DeepSeek, DashScope, OpenAI, etc.)")
    
    # 检查数据源 Key
    finnhub = os.getenv("FINNHUB_API_KEY")
    if finnhub and len(finnhub) > 5:
        print_pass("发现 FinnHub API Key")
    else:
        print_warn("未配置 FINNHUB_API_KEY，美股/港股数据可能受限")
        
    return found_llm

def test_graph_initialization():
    """测试 TradingAgentsGraph 初始化 (验证模型配置)"""
    print_info("正在测试 AI Agent 初始化...")
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 尝试确定可用的 Provider
        provider = "openai"
        if os.getenv("DEEPSEEK_API_KEY"): provider = "deepseek"
        elif os.getenv("DASHSCOPE_API_KEY"): provider = "dashscope"
        
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = provider
        # 禁用内存以加快测试
        config["memory_enabled"] = False 
        
        print_info(f"尝试使用 Provider: {provider}")
        
        graph = TradingAgentsGraph(
            selected_analysts=["market"], # 只选一个最简单的
            config=config,
            debug=False
        )
        print_pass("TradingAgentsGraph 初始化成功 (模型配置正确)")
        return True
    except Exception as e:
        print_fail(f"AI Agent 初始化失败: {e}")
        print_info("请检查 API Key 是否正确，以及网络是否通畅")
        return False

async def main():
    print(f"\n{Colors.BLUE}========================================{Colors.END}")
    print(f"{Colors.BLUE}   TradingAgents VPS 部署验证工具   {Colors.END}")
    print(f"{Colors.BLUE}========================================{Colors.END}\n")
    
    # 1. 环境变量
    env_ok = check_env_vars()
    print("-" * 40)
    
    # 2. 数据库
    db_ok = await check_mongodb()
    redis_ok = await check_redis()
    print("-" * 40)
    
    # 3. AI 初始化
    graph_ok = False
    if env_ok:
        graph_ok = test_graph_initialization()
    
    print(f"\n{Colors.BLUE}========================================{Colors.END}")
    print(f"{Colors.BLUE}   验证总结   {Colors.END}")
    print(f"{Colors.BLUE}========================================{Colors.END}")
    
    all_pass = env_ok and db_ok and redis_ok and graph_ok
    
    if all_pass:
        print(f"\n{Colors.GREEN}🎉 恭喜！系统环境验证通过！{Colors.END}")
        print("您可以开始使用 Web 界面或 CLI 工具了。")
        print("\nCLI 使用示例:")
        print("  python -m cli.main analyze")
    else:
        print(f"\n{Colors.RED}⚠️  系统存在一些问题，请根据上述错误信息进行修复。{Colors.END}")
        
if __name__ == "__main__":
    asyncio.run(main())
