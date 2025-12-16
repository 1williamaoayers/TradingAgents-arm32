#!/usr/bin/env python3
"""
Redis 数据验证脚本
连接 Redis 数据库，列出所有键值，查看与自选股相关的数据
"""

import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
import json

def verify_redis_data():
    """验证 Redis 中的数据"""
    console = Console()
    
    # 打印标题
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Redis 数据验证报告[/bold cyan]",
        border_style="cyan"
    ))
    console.print("\n")
    
    try:
        import redis
        console.print("[bold green]✅ redis 库已安装[/bold green]")
    except ImportError:
        console.print("[bold red]❌ redis 未安装，请运行: pip install redis[/bold red]")
        return
    
    # 从环境变量读取 Redis 配置
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD", "tradingagents123")
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    console.print("[bold yellow]📡 Redis 连接信息:[/bold yellow]")
    console.print(f"  Host: {redis_host}")
    console.print(f"  Port: {redis_port}")
    console.print(f"  DB: {redis_db}")
    console.print(f"  Password: {'***' if redis_password else '(无)'}")
    console.print("\n")
    
    try:
        # 连接 Redis
        console.print("[bold yellow]🔌 正在连接 Redis...[/bold yellow]")
        
        connect_kwargs = {
            "host": redis_host,
            "port": redis_port,
            "db": redis_db,
            "decode_responses": True,
            "socket_timeout": 5,
            "socket_connect_timeout": 5
        }
        
        if redis_password:
            connect_kwargs["password"] = redis_password
        
        r = redis.Redis(**connect_kwargs)
        
        # 测试连接
        r.ping()
        console.print("[bold green]✅ Redis 连接成功！[/bold green]\n")
        
        # 获取 Redis 信息
        info = r.info()
        console.print(Panel(
            f"[bold yellow]Redis 版本:[/bold yellow] {info.get('redis_version', 'N/A')}\n"
            f"[bold yellow]运行模式:[/bold yellow] {info.get('redis_mode', 'N/A')}\n"
            f"[bold yellow]已用内存:[/bold yellow] {info.get('used_memory_human', 'N/A')}\n"
            f"[bold yellow]连接数:[/bold yellow] {info.get('connected_clients', 'N/A')}\n"
            f"[bold yellow]键总数:[/bold yellow] {r.dbsize()}",
            title="[bold cyan]Redis 服务器信息[/bold cyan]",
            border_style="blue"
        ))
        console.print("\n")
        
        # 获取所有键
        console.print("[bold cyan]🔑 获取所有 Redis 键...[/bold cyan]\n")
        all_keys = r.keys("*")
        
        console.print(f"[bold green]✅ 找到 {len(all_keys)} 个键[/bold green]\n")
        
        if all_keys:
            # 创建键列表表格
            table = Table(
                title="Redis 键列表",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("键名", justify="left", style="yellow bold", width=50)
            table.add_column("类型", justify="center", style="green", width=10)
            table.add_column("TTL", justify="center", style="blue", width=10)
            table.add_column("大小/长度", justify="center", style="magenta", width=12)
            
            for idx, key in enumerate(sorted(all_keys), 1):
                key_type = r.type(key)
                ttl = r.ttl(key)
                
                # 获取键的大小/长度
                if key_type == "string":
                    size = len(r.get(key) or "")
                elif key_type == "list":
                    size = r.llen(key)
                elif key_type == "set":
                    size = r.scard(key)
                elif key_type == "zset":
                    size = r.zcard(key)
                elif key_type == "hash":
                    size = r.hlen(key)
                else:
                    size = "-"
                
                ttl_str = str(ttl) if ttl >= 0 else "永久"
                
                table.add_row(
                    str(idx),
                    key,
                    key_type,
                    ttl_str,
                    str(size)
                )
            
            console.print(table)
            console.print("\n")
            
            # 查找与自选股、股票、任务相关的键
            console.print("[bold cyan]🔍 查找相关键值：[/bold cyan]\n")
            
            patterns = {
                "自选股相关": ["*favorite*", "*watchlist*", "*stock*"],
                "任务队列相关": ["*queue*", "*task*", "*job*"],
                "缓存相关": ["*cache*", "*screening*", "*analysis*"],
                "用户相关": ["*user*", "*session*"],
            }
            
            for category, pattern_list in patterns.items():
                console.print(f"[bold yellow]{category}:[/bold yellow]")
                found_keys = []
                for pattern in pattern_list:
                    matched = r.keys(pattern)
                    found_keys.extend(matched)
                
                found_keys = list(set(found_keys))  # 去重
                
                if found_keys:
                    for key in sorted(found_keys):
                        key_type = r.type(key)
                        console.print(f"  [green]✓[/green] {key} [dim]({key_type})[/dim]")
                        
                        # 尝试显示键的值（如果是字符串且不太长）
                        if key_type == "string":
                            value = r.get(key)
                            if value and len(value) < 200:
                                try:
                                    # 尝试解析 JSON
                                    parsed = json.loads(value)
                                    console.print(f"    [dim]{json.dumps(parsed, ensure_ascii=False, indent=2)}[/dim]")
                                except:
                                    console.print(f"    [dim]{value}[/dim]")
                else:
                    console.print(f"  [dim]未找到相关键[/dim]")
                
                console.print()
        else:
            console.print("[bold yellow]⚠️  Redis 中没有任何键[/bold yellow]")
        
        # Redis 用途说明
        console.print(Panel(
            "[bold yellow]Redis 在本项目中的用途:[/bold yellow]\n\n"
            "1. [cyan]任务队列[/cyan]: 存储待处理的分析任务\n"
            "2. [cyan]缓存[/cyan]: 缓存股票行情、筛选结果等\n"
            "3. [cyan]会话管理[/cyan]: 存储用户会话信息\n"
            "4. [cyan]分布式锁[/cyan]: 防止并发冲突\n"
            "5. [cyan]进度跟踪[/cyan]: 实时任务进度更新\n\n"
            "[bold green]注意:[/bold green] 自选股数据主要存储在 MongoDB 中，\n"
            "Redis 仅用于缓存和临时数据。",
            title="[bold cyan]Redis 用途说明[/bold cyan]",
            border_style="green"
        ))
        
        console.print("\n[bold green]✨ 验证完成！[/bold green]\n")
        
    except redis.ConnectionError as e:
        console.print(f"[bold red]❌ Redis 连接失败: {str(e)}[/bold red]")
        console.print("[bold yellow]💡 提示: 请确保 Redis 服务正在运行[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]❌ 错误: {type(e).__name__}: {str(e)}[/bold red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

if __name__ == "__main__":
    verify_redis_data()
