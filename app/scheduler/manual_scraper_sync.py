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
        from app.worker.scraper_sync_service import get_scraper_sync_service
        
        async def run_sync():
            # 2. 获取服务实例 (同步方法)
            service = get_scraper_sync_service()
            print("服务获取成功", flush=True)
            
            # 3. 执行同步 (内部会自动initialize)
            result = await service.sync_favorite_stocks()
            return result
        
        # 4. 运行
        result = asyncio.run(run_sync())
        
        # 5. 格式化输出
        output = {
            "success": result.get("status") == "success",
            "news_count": result.get("total_news_saved", 0),
            "favorites_count": result.get("favorites_count", 0),
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
