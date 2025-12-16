#!/usr/bin/env python3
"""
自选股数据验证脚本
用于验证自选股数据是否正确存储在 data/watchlist.json 文件中
"""

import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

def verify_watchlist():
    """验证自选股数据"""
    console = Console()
    
    # 打印标题
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]自选股数据验证报告[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\n")
    
    # 读取数据文件
    watchlist_file = Path("data/watchlist.json")
    
    # 检查文件是否存在
    if not watchlist_file.exists():
        console.print("[bold red]❌ 错误：data/watchlist.json 文件不存在！[/bold red]")
        return
    
    # 读取 JSON 数据
    try:
        with open(watchlist_file, 'r', encoding='utf-8') as f:
            watchlist_data = json.load(f)
    except Exception as e:
        console.print(f"[bold red]❌ 读取文件失败：{e}[/bold red]")
        return
    
    # 显示存储信息
    console.print("[bold green]✅ 数据存储方式：JSON 文件[/bold green]")
    console.print(f"[bold green]✅ 文件路径：{watchlist_file.absolute()}[/bold green]")
    console.print(f"[bold green]✅ 文件大小：{watchlist_file.stat().st_size} 字节[/bold green]")
    console.print(f"[bold green]✅ 最后修改时间：{datetime.fromtimestamp(watchlist_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}[/bold green]")
    console.print("\n")
    
    # 创建表格显示数据
    table = Table(
        title="📊 自选股列表详情",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        border_style="blue"
    )
    
    table.add_column("序号", justify="center", style="cyan", width=6)
    table.add_column("股票代码", justify="center", style="yellow bold", width=15)
    table.add_column("市场", justify="center", style="green", width=10)
    table.add_column("添加日期", justify="center", style="blue", width=12)
    table.add_column("新闻数量", justify="center", style="magenta", width=10)
    
    # 添加数据行
    for idx, stock in enumerate(watchlist_data, 1):
        table.add_row(
            str(idx),
            stock.get("symbol", "N/A"),
            stock.get("market", "N/A"),
            stock.get("added_date", "N/A"),
            str(stock.get("news_count", 0))
        )
    
    console.print(table)
    console.print("\n")
    
    # 统计信息
    total_count = len(watchlist_data)
    hk_stocks = [s for s in watchlist_data if s.get("market") == "港股"]
    a_stocks = [s for s in watchlist_data if s.get("market") == "A股"]
    us_stocks = [s for s in watchlist_data if s.get("market") == "美股"]
    
    stats_table = Table(
        title="📈 统计信息",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan"
    )
    
    stats_table.add_column("项目", style="cyan")
    stats_table.add_column("数量", justify="right", style="green bold")
    
    stats_table.add_row("自选股总数", str(total_count))
    stats_table.add_row("港股数量", str(len(hk_stocks)))
    stats_table.add_row("A股数量", str(len(a_stocks)))
    stats_table.add_row("美股数量", str(len(us_stocks)))
    
    console.print(stats_table)
    console.print("\n")
    
    # 显示原始 JSON 数据
    console.print(Panel(
        json.dumps(watchlist_data, ensure_ascii=False, indent=2),
        title="[bold yellow]原始 JSON 数据[/bold yellow]",
        border_style="yellow"
    ))
    console.print("\n")
    
    # 验证特定股票
    console.print("[bold cyan]🔍 验证指定的港股代码：[/bold cyan]")
    target_stocks = ["09618.HK", "01810.HK", "02128.HK", "02525.HK"]
    
    for stock_code in target_stocks:
        found = any(s.get("symbol") == stock_code for s in watchlist_data)
        if found:
            console.print(f"  [bold green]✅ {stock_code} - 已找到[/bold green]")
        else:
            console.print(f"  [bold red]❌ {stock_code} - 未找到[/bold red]")
    
    console.print("\n")
    console.print("[bold green]✨ 验证完成！[/bold green]")
    console.print("\n")

if __name__ == "__main__":
    verify_watchlist()
