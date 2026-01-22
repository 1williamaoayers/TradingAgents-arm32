#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import asyncio

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    try:
        # 1. 导入服务
        from app.worker.multi_source_news_service import get_multi_source_news_service
        
        async def run_sync():
            # 2. 初始化数据库 (CLI模式必须手动初始化)
            from app.core.database import init_database
            await init_database()
            
            # 3. 获取服务实例 (异步方法)
            service = await get_multi_source_news_service()
            print("服务获取成功", flush=True)
            
            # 3. 执行同步
            # sync_news_data 返回 Dict[str, Any] with 'news_count' etc.
            result = await service.sync_news_data(favorites_only=True)
            return result
        
        # 4. 运行
        result = asyncio.run(run_sync())
        
        # 5. 格式化输出
        output = {
            "success": result.get("error_count", 0) == 0 or result.get("success_count", 0) > 0,
            "news_count": result.get("news_count", 0),
            "total_processed": result.get("total_processed", 0),
            "message": "同步完成",
            "details": result
        }
        
        print(json.dumps(output, ensure_ascii=False), flush=True)
        return 0
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        output = {
            "success": False,
            "error": str(e),
            "message": "同步失败"
        }
        print(json.dumps(output, ensure_ascii=False), flush=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
