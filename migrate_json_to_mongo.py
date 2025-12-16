#!/usr/bin/env python3
"""
数据迁移脚本：将 data/watchlist.json 迁移到 MongoDB
一次性脚本，用于将现有的本地 JSON 自选股数据迁移到 MongoDB 数据库
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

def migrate_json_to_mongodb():
    """迁移 JSON 数据到 MongoDB"""
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]自选股数据迁移工具[/bold cyan]\n"
        "[yellow]JSON → MongoDB[/yellow]",
        border_style="cyan"
    ))
    console.print("\n")
    
    # 步骤 1: 读取 JSON 文件
    console.print("[bold yellow]📂 步骤 1: 读取 JSON 文件[/bold yellow]")
    json_file = Path("data/watchlist.json")
    
    if not json_file.exists():
        console.print("[bold red]❌ 文件不存在: data/watchlist.json[/bold red]")
        return False
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            watchlist_data = json.load(f)
        console.print(f"[bold green]✅ 成功读取 {len(watchlist_data)} 条记录[/bold green]\n")
    except Exception as e:
        console.print(f"[bold red]❌ 读取文件失败: {e}[/bold red]")
        return False
    
    # 显示待迁移数据
    table = Table(title="待迁移的自选股数据", box=box.ROUNDED)
    table.add_column("序号", justify="center", style="cyan")
    table.add_column("股票代码", justify="center", style="yellow bold")
    table.add_column("市场", justify="center", style="green")
    table.add_column("添加日期", justify="center", style="blue")
    
    for idx, stock in enumerate(watchlist_data, 1):
        table.add_row(
            str(idx),
            stock.get("symbol", "N/A"),
            stock.get("market", "N/A"),
            stock.get("added_date", "N/A")
        )
    
    console.print(table)
    console.print("\n")
    
    # 步骤 2: 连接 MongoDB
    console.print("[bold yellow]📡 步骤 2: 连接 MongoDB[/bold yellow]")
    
    try:
        from pymongo import MongoClient
    except ImportError:
        console.print("[bold red]❌ pymongo 未安装，请运行: pip install pymongo[/bold red]")
        return False
    
    # 读取 MongoDB 配置
    mongo_host = os.getenv("MONGODB_HOST", "localhost")
    mongo_port = int(os.getenv("MONGODB_PORT", "27017"))
    mongo_username = os.getenv("MONGODB_USERNAME", "admin")
    mongo_password = os.getenv("MONGODB_PASSWORD", "tradingagents123")
    mongo_database = os.getenv("MONGODB_DATABASE", "tradingagents")
    mongo_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    
    mongo_uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/?authSource={mongo_auth_source}"
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        console.print(f"[bold green]✅ MongoDB 连接成功: {mongo_host}:{mongo_port}[/bold green]\n")
    except Exception as e:
        console.print(f"[bold red]❌ MongoDB 连接失败: {e}[/bold red]")
        return False
    
    db = client[mongo_database]
    
    # 步骤 3: 迁移数据
    console.print("[bold yellow]🔄 步骤 3: 迁移数据到 MongoDB[/bold yellow]")
    
    # 使用默认用户 ID（或创建一个测试用户）
    # 这里我们使用一个固定的用户 ID，你可以根据实际情况修改
    user_id = "default_user"
    
    console.print(f"[dim]目标用户 ID: {user_id}[/dim]\n")
    
    migrated_count = 0
    failed_count = 0
    
    for stock in watchlist_data:
        stock_code = stock.get("symbol")
        stock_name = stock.get("symbol")  # JSON 中没有 stock_name，暂时用 symbol
        market = stock.get("market", "港股")
        added_date_str = stock.get("added_date")
        
        # 转换日期格式
        try:
            added_at = datetime.strptime(added_date_str, "%Y-%m-%d")
        except:
            added_at = datetime.utcnow()
        
        # 构建自选股文档
        favorite_stock = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "market": market,
            "added_at": added_at,
            "tags": [],
            "notes": "",
            "alert_price_high": None,
            "alert_price_low": None
        }
        
        try:
            # 检查是否已存在
            existing = db.user_favorites.find_one({
                "user_id": user_id,
                "favorites.stock_code": stock_code
            })
            
            if existing:
                console.print(f"  [yellow]⚠️  {stock_code} 已存在，跳过[/yellow]")
                continue
            
            # 插入到 MongoDB
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
                console.print(f"  [green]✅ {stock_code} 迁移成功[/green]")
                migrated_count += 1
            else:
                console.print(f"  [red]❌ {stock_code} 迁移失败[/red]")
                failed_count += 1
                
        except Exception as e:
            console.print(f"  [red]❌ {stock_code} 迁移失败: {e}[/red]")
            failed_count += 1
    
    console.print("\n")
    
    # 步骤 4: 验证迁移结果
    console.print("[bold yellow]🔍 步骤 4: 验证迁移结果[/bold yellow]")
    
    try:
        user_doc = db.user_favorites.find_one({"user_id": user_id})
        
        if user_doc:
            favorites = user_doc.get("favorites", [])
            console.print(f"[bold green]✅ 数据库中找到 {len(favorites)} 条自选股记录[/bold green]\n")
            
            # 显示数据库中的数据
            verify_table = Table(title="MongoDB 中的自选股数据", box=box.ROUNDED)
            verify_table.add_column("序号", justify="center", style="cyan")
            verify_table.add_column("股票代码", justify="center", style="yellow bold")
            verify_table.add_column("股票名称", justify="center", style="green")
            verify_table.add_column("市场", justify="center", style="blue")
            verify_table.add_column("添加时间", justify="center", style="magenta")
            
            for idx, fav in enumerate(favorites, 1):
                added_at = fav.get("added_at")
                if isinstance(added_at, datetime):
                    added_at = added_at.strftime("%Y-%m-%d %H:%M:%S")
                
                verify_table.add_row(
                    str(idx),
                    fav.get("stock_code", "N/A"),
                    fav.get("stock_name", "N/A"),
                    fav.get("market", "N/A"),
                    str(added_at)
                )
            
            console.print(verify_table)
            console.print("\n")
            
            # 验证目标股票
            target_stocks = ["09618.HK", "01810.HK", "02128.HK", "02525.HK"]
            console.print("[bold cyan]🎯 验证目标股票：[/bold cyan]")
            for stock_code in target_stocks:
                found = any(f.get("stock_code") == stock_code for f in favorites)
                if found:
                    console.print(f"  [bold green]✅ {stock_code} - 已找到[/bold green]")
                else:
                    console.print(f"  [bold red]❌ {stock_code} - 未找到[/bold red]")
            
        else:
            console.print("[bold red]❌ 数据库中未找到用户数据[/bold red]")
            return False
            
    except Exception as e:
        console.print(f"[bold red]❌ 验证失败: {e}[/bold red]")
        return False
    
    # 关闭连接
    client.close()
    
    # 总结
    console.print("\n")
    console.print(Panel(
        f"[bold green]迁移成功:[/bold green] {migrated_count} 条\n"
        f"[bold yellow]跳过:[/bold yellow] {len(watchlist_data) - migrated_count - failed_count} 条\n"
        f"[bold red]失败:[/bold red] {failed_count} 条\n\n"
        f"[bold cyan]数据库记录总数:[/bold cyan] {len(favorites)} 条",
        title="[bold cyan]迁移结果汇总[/bold cyan]",
        border_style="green"
    ))
    
    console.print("\n[bold green]✨ 迁移完成！[/bold green]\n")
    
    return migrated_count > 0

if __name__ == "__main__":
    success = migrate_json_to_mongodb()
    sys.exit(0 if success else 1)
