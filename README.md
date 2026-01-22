# 🤖 TradingAgents-CN - AI驱动的多市场股票分析平台

> 🎯 **专为"零基础用户"设计** - 复制粘贴即可完成部署，无需懂代码！

---

## 📊 项目定位

**TradingAgents-CN** 是一个**AI驱动的股票分析平台**，支持 A股、港股、美股 三大市场。它通过多数据源采集新闻和市场数据，结合大语言模型（LLM）生成专业的投资分析报告。

---

## 📋 DEV版本特色功能

| 功能 | 说明 |
|------|------|
| 🇺🇸 **美股完整支持** | TSLA/GOOGL等美股新闻+基本面分析，无需OpenAI Key |
| 🇭🇰 **港股完整支持** | 小米/腾讯等港股新闻+财报+回购动态 |
| 🇨🇳 **A股完整支持** | 沪深股票分析，东方财富数据源 |
| 🔄 **新闻智能去重** | 自动过滤重复新闻，保留最完整版本 |
| ⏰ **自动定时同步** | AKShare每4小时整点/爬虫每4小时半点/多源5/10/21点 |
| 🚀 **开箱即用** | 自动配置，小白也能一键部署 |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      TradingAgents-CN                           │
├─────────────────────────────────────────────────────────────────┤
│  前端 (Streamlit)                后端 (FastAPI)                 │
│  ├─ 主页.py (分析入口)           ├─ main.py (913行，核心入口)   │
│  ├─ 自选股管理                   ├─ 37个路由模块               │
│  ├─ 新闻同步监控                 ├─ 61个服务模块               │
│  └─ 系统配置                     └─ 定时任务调度器              │
├─────────────────────────────────────────────────────────────────┤
│  AI分析引擎 (tradingagents/)                                    │
│  ├─ agents/ (19个分析师角色)                                    │
│  ├─ tools/ (统一新闻工具、基本面工具)                           │
│  ├─ dataflows/ (46个数据流模块)                                 │
│  └─ llm_adapters/ (DeepSeek/Qwen/OpenAI适配器)                  │
├─────────────────────────────────────────────────────────────────┤
│  数据层                                                         │
│  ├─ MongoDB (持久化存储)         ├─ Redis (缓存)               │
│  └─ 多数据源: AKShare | 东方财富 | FinnHub | Serper             │
├─────────────────────────────────────────────────────────────────┤
│  外部爬虫 (PlaywriteOCR - 独立服务, 端口9527)                   │
│  └─ 8个爬虫: 财联社/华尔街见闻/智通财经/今日头条等              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 核心目录结构

| 目录 | 用途 | 核心文件数 |
|------|------|------------|
| `app/` | 后端服务 | 168个文件 |
| `app/routers/` | API路由 | 37个模块 |
| `app/services/` | 业务逻辑 | 61个模块 |
| `app/worker/` | 后台任务 | 26个模块 |
| `tradingagents/` | AI分析核心 | 107个文件 |
| `tradingagents/agents/` | 分析师角色 | 19个 |
| `web/` | 前端界面 | 46个文件 |
| `cli/` | 命令行工具 | 7个文件 |

---

## 📡 新闻数据采集架构（6+1并行源）

```
用户发起分析
     ↓
┌─────────────────────────────────────────────┐
│           unified_news_tool.py              │
│  (统一新闻分析器)                            │
├─────────────────────────────────────────────┤
│  1. 东方财富个股新闻 (stock_news_em)         │
│  2. AKShare多源快讯 (7个财经源聚合)          │
│  3. Serper实时搜索 (Google API)             │
│  4. Alpha Vantage (美股专用)                 │
│  5. RSS新闻源 (金十/财联社/格隆汇)           │
│  6. 数据库缓存 (历史数据兜底)                │
├─────────────────────────────────────────────┤
│  7. PlaywriteOCR爬虫 (港股专用, 端口9527)    │
│     → 8个爬虫并行 → 直达LLM (不经数据库)     │
└─────────────────────────────────────────────┘
     ↓
  AI分析报告生成
```

---

## 🚀 一键部署（3分钟完成）

### 第1步：复制粘贴这行命令

```bash
mkdir -p /home/tradingagents && cd /home/tradingagents && git clone -b dev https://github.com/1williamaoayers/TradingAgents-arm32.git . && cp .env.docker .env && docker-compose up -d
```

### 第2步：等待1-2分钟，打开浏览器

```
http://你的服务器IP:8501
```

**完成！** 🎉 就这么简单！

---

## ⚠️ MongoDB 兼容性说明

本项目使用 **MongoDB 4.4**，兼容所有 CPU（包括不支持 AVX 指令集的老旧/低端 CPU）。

> **注意**：MongoDB 5.0+ 强制要求 AVX 指令集，在部分 VPS 上会启动失败。我们已降级到 4.4 解决此问题。

---

## 🔑 配置API密钥（分析功能必需）

### 进入Web配置页面

1. 打开 `http://你的服务器IP:8501`
2. 左侧菜单点击 **"⚙️ 系统配置"**
3. 填入你的API密钥

### 必需的密钥

| 密钥 | 用途 | 获取地址 |
|------|------|----------|
| **DASHSCOPE_API_KEY** | AI分析报告 | [阿里云](https://dashscope.console.aliyun.com/) |

### 可选的密钥（增强功能）

| 密钥 | 用途 | 获取地址 |
|------|------|----------|
| FINNHUB_API_KEY | 美股新闻 | [finnhub.io](https://finnhub.io/) |
| ALPHA_VANTAGE_API_KEY | 美股数据 | [alphavantage.co](https://www.alphavantage.co/) |
| SERPER_API_KEY | 实时搜索 | [serper.dev](https://serper.dev/) |

> 💡 **提示**：只需要DASHSCOPE_API_KEY就能用，其他是锦上添花

---

## 📱 功能界面说明

### 首页 - 股票分析

1. 输入股票代码（如 `TSLA`、`01810`、`600036`）
2. 选择分析师（建议全选）
3. 点击"开始分析"
4. 等待AI生成报告（约1-3分钟）

### 自选股管理

- 添加你关注的股票
- 一键查看自选股列表
- 快速跳转分析

### 新闻同步监控

- 查看最近同步状态
- 手动触发同步（AKShare/多源/爬虫）
- 查看各股票新闻数量

---

## 🛠️ CLI命令行模式（无头分析）

无需前端，直接在容器内运行分析：

```bash
docker exec -it tradingagents python -m cli.main analyze
```

详细文档：[CLI使用说明书.md](./CLI使用说明书.md)

---

## ❓ 常见问题

### Q: 页面打不开？

检查容器状态：
```bash
docker ps
```
如果没有看到 `tradingagents`，运行：
```bash
cd /home/tradingagents && docker-compose up -d
```

### Q: MongoDB启动失败（Illegal instruction）？

你的CPU不支持AVX指令集。确保使用本项目的 `docker-compose.yml`（已配置 `mongo:4.4`）。

### Q: 分析失败？

检查API密钥是否配置正确，在Web页面"系统配置"中确认

### Q: 如何重启？

```bash
cd /home/tradingagents && docker-compose restart
```

### Q: 如何查看日志？

```bash
docker logs tradingagents --tail 100
```

### Q: 如何更新到最新版？

```bash
cd /home/tradingagents
git pull origin dev
docker-compose restart
```

---

## 📊 项目规模统计

| 指标 | 数量 |
|------|------|
| 主项目文件 | 1944+ |
| Python模块 | 100+ |
| API路由 | 37个 |
| 服务模块 | 61个 |
| AI分析师角色 | 19个 |
| 外部爬虫 | 8个 |

---

## 🔧 定时同步调度

| 任务 | 调度时间 | 用途 |
|------|----------|------|
| **AKShare同步** | 每4小时整点 `0 */4 * * *` | A股新闻入库 |
| **Scraper同步** | 每4小时半点 `30 */4 * * *` | 爬虫数据入库 |
| **MultiSource同步** | `0 5,10,21 * * *` | 多源聚合（港美股时段） |

---

## 📊 DEV版 vs MAIN版

| 特性 | DEV版 | MAIN版 |
|------|-------|--------|
| 美股支持 | ✅ 完整(AKShare) | ⚠️ 需OpenAI |
| 新闻去重 | ✅ 智能去重 | ❌ 无 |
| 后端自启 | ✅ 自动 | ❌ 需手动 |
| 定时同步 | ✅ 错峰执行 | ❌ 需手动 |
| MongoDB兼容 | ✅ 4.4（无AVX需求） | ⚠️ 7.0（需AVX） |
| 推荐 | 🔥 推荐使用 | - |

---

## 📞 获取帮助

- 📖 [完整文档](https://github.com/1williamaoayers/TradingAgents-arm32/wiki)
- 🐛 [提交Issue](https://github.com/1williamaoayers/TradingAgents-arm32/issues)
- 💬 [讨论区](https://github.com/1williamaoayers/TradingAgents-arm32/discussions)

---

> 🎉 **DEV分支** - 最新功能，持续更新中！
>
> 最后更新: 2026-01-22
