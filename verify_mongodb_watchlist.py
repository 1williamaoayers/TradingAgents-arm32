#!/usr/bin/env python3
"""
MongoDB 自选股数据验证脚本
直接连接 MongoDB 数据库，查询 user_favorites 集合中的自选股数据
"""

import os
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import json

def verify_mongodb_watchlist():
    """验证 MongoDB 中的自选股数据"""
    console = Console()
    
    # 打印标题
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]MongoDB 自选股数据验证报告[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\n")
    
    try:
        from pymongo import MongoClient
        console.print("[bold green]✅ pymongo 库已安装[/bold green]")
    except ImportError:
        console.print("[bold red]❌ pymongo 未安装，请运行: pip install pymongo[/bold red]")
        return
    
    # 从环境变量读取 MongoDB 配置
    mongo_host = os.getenv("MONGODB_HOST", "localhost")
    mongo_port = int(os.getenv("MONGODB_PORT", "27017"))
    mongo_username = os.getenv("MONGODB_USERNAME", "admin")
    mongo_password = os.getenv("MONGODB_PASSWORD", "tradingagents123")
    mongo_database = os.getenv("MONGODB_DATABASE", "tradingagents")
    mongo_auth_source = os.getenv("MONGODB_AUTH_SOURCE", "admin")
    
    # 构建连接字符串
    mongo_uri = f"mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/?authSource={mongo_auth_source}"
    
    console.print("[bold yellow]📡 MongoDB 连接信息:[/bold yellow]")
    console.print(f"  Host: {mongo_host}")
    console.print(f"  Port: {mongo_port}")
    console.print(f"  Database: {mongo_database}")
    console.print(f"  Username: {mongo_username}")
    console.print(f"  Auth Source: {mongo_auth_source}")
    console.print("\n")
    
    try:
        # 连接 MongoDB
        console.print("[bold yellow]🔌 正在连接 MongoDB...[/bold yellow]")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # 测试连接
        client.server_info()
        console.print("[bold green]✅ MongoDB 连接成功！[/bold green]\n")
        
        # 获取数据库
        db = client[mongo_database]
        
        # 查询 user_favorites 集合
        console.print("[bold cyan]📊 查询 user_favorites 集合...[/bold cyan]\n")
        user_favorites_coll = db["user_favorites"]
        
        # 获取所有自选股文档
        all_favorites = list(user_favorites_coll.find({}))
        
        console.print(f"[bold green]✅ 找到 {len(all_favorites)} 个用户的自选股数据[/bold green]\n")
        
        # 遍历每个用户的自选股
        for idx, user_fav in enumerate(all_favorites, 1):
            user_id = user_fav.get("user_id", "未知")
            favorites = user_fav.get("favorites", [])
            created_at = user_fav.get("created_at")
            updated_at = user_fav.get("updated_at")
            
            console.print(Panel(
                f"[bold yellow]用户 ID:[/bold yellow] {user_id}\n"
                f"[bold yellow]自选股数量:[/bold yellow] {len(favorites)}\n"
                f"[bold yellow]创建时间:[/bold yellow] {created_at}\n"
                f"[bold yellow]更新时间:[/bold yellow] {updated_at}",
                title=f"[bold cyan]用户 #{idx}[/bold cyan]",
                border_style="blue"
            ))
            
            if favorites:
                # 创建自选股表格
                table = Table(
                    title=f"用户 {user_id} 的自选股列表",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold magenta"
                )
                
                table.add_column("序号", justify="center", style="cyan", width=6)
                table.add_column("股票代码", justify="center", style="yellow bold", width=15)
                table.add_column("股票名称", justify="center", style="green", width=20)
                table.add_column("市场", justify="center", style="blue", width=10)
                table.add_column("添加时间", justify="center", style="magenta", width=20)
                table.add_column("标签", justify="left", style="cyan", width=15)
                
                for i, stock in enumerate(favorites, 1):
                    stock_code = stock.get("stock_code", "N/A")
                    stock_name = stock.get("stock_name", "N/A")
                    market = stock.get("market", "N/A")
                    added_at = stock.get("added_at", "N/A")
                    tags = ", ".join(stock.get("tags", []))
                    
                    # 格式化时间
                    if isinstance(added_at, datetime):
                        added_at = added_at.strftime("%Y-%m-%d %H:%M:%S")
                    
                    table.add_row(
                        str(i),
                        stock_code,
                        stock_name,
                        market,
                        str(added_at),
                        tags or "-"
                    )
                
                console.print(table)
                console.print("\n")
                
                # 检查是否包含指定的港股代码
                target_stocks = ["09618.HK", "01810.HK", "02128.HK", "02525.HK"]
                console.print("[bold cyan]🔍 验证指定的港股代码：[/bold cyan]")
                for stock_code in target_stocks:
                    found = any(s.get("stock_code") == stock_code for s in favorites)
                    if found:
                        console.print(f"  [bold green]✅ {stock_code} - 已找到[/bold green]")
                    else:
                        console.print(f"  [bold yellow]⚠️  {stock_code} - 未找到[/bold yellow]")
                console.print("\n")
                
                # 显示原始 JSON 数据
                console.print(Panel(
                    json.dumps(favorites, ensure_ascii=False, indent=2, default=str),
                    title="[bold yellow]原始 MongoDB 文档数据[/bold yellow]",
                    border_style="yellow"
                ))
                console.print("\n")
        
        # 统计信息
        total_stocks = sum(len(uf.get("favorites", [])) for uf in all_favorites)
        console.print(Panel(
            f"[bold green]总用户数:[/bold green] {len(all_favorites)}\n"
            f"[bold green]总自选股数:[/bold green] {total_stocks}",
            title="[bold cyan]统计信息[/bold cyan]",
            border_style="green"
        ))
        
        # 关闭连接
        client.close()
        console.print("\n[bold green]✨ 验证完成！[/bold green]\n")
        
    except Exception as e:
        console.print(f"[bold red]❌ 错误: {type(e).__name__}: {str(e)}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

if __name__ == "__main__":
    verify_mongodb_watchlist()
