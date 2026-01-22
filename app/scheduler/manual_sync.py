#!/usr/bin/env python3
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    try:
        print("START", flush=True)
        import asyncio
        print("导入asyncio", flush=True)
        
        from app.worker.akshare_sync_service import get_akshare_sync_service
        print("导入get_akshare_sync_service", flush=True)
        
        async def run_sync():
            print("run_sync开始", flush=True)
            service = await get_akshare_sync_service()
            print(f"服务获取成功: {type(service)}", flush=True)
            
            result = await service.sync_news_data(symbols=None, favorites_only=True, sync_type="manual")
            print(f"同步完成: {result}", flush=True)
            return result
        
        print("执行asyncio.run", flush=True)
        result = asyncio.run(run_sync())
        print(f"结果: {result}", flush=True)
        
        output = {
            "success": True,
            "news_count": result.get("news_count", 0) if isinstance(result, dict) else 0,
            "message": "同步成功"
        }
        
        print(json.dumps(output, ensure_ascii=False), flush=True)
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
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
