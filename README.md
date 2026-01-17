# 🤖 TradingAgents DEV版 - 小白专用一键部署指南

> 🎯 **本版本专为"零基础用户"设计** - 复制粘贴即可完成部署，无需懂代码！

---

## 📋 DEV版本特色功能

| 功能 | 说明 |
|------|------|
| 🇺🇸 **美股完整支持** | TSLA/GOOGL等美股新闻+基本面分析，无需OpenAI Key |
| 🇭🇰 **港股完整支持** | 小米/腾讯等港股新闻+财报+回购动态 |
| 🇨🇳 **A股完整支持** | 沪深股票分析，东方财富数据源 |
| 🔄 **新闻智能去重** | 自动过滤重复新闻，保留最完整版本 |
| ⏰ **自动定时同步** | 新闻每2小时自动更新 |
| 🚀 **开箱即用** | 自动配置，小白也能一键部署 |

---

## 🚀 一键部署（3分钟完成）

### 第1步：复制粘贴这行命令

```bash
mkdir -p /home/tradingagents && cd /home/tradingagents && curl -O https://raw.githubusercontent.com/1williamaoayers/TradingAgents-arm32/dev/docker-compose.yml && docker-compose up -d
```

### 第2步：等待1-2分钟，打开浏览器

```
http://你的服务器IP:8501
```

**完成！** 🎉 就这么简单！

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
- 手动触发同步
- 查看各股票新闻数量

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
docker-compose pull
docker-compose up -d
```

---

## 🛠️ 技术架构（高级用户）

```
┌─────────────────────────────────────────────────┐
│                  TradingAgents                  │
├─────────────────────────────────────────────────┤
│  前端: Streamlit (8501)    后端: FastAPI (8000) │
├─────────────────────────────────────────────────┤
│  数据库: MongoDB (27017)   缓存: Redis (6379)   │
├─────────────────────────────────────────────────┤
│  数据源: 东方财富 | AKShare | FinnHub | Serper  │
└─────────────────────────────────────────────────┘
```

### 支持的股票格式

| 市场 | 格式示例 | 说明 |
|------|----------|------|
| 美股 | `TSLA`, `GOOGL` | 纯字母 |
| 港股 | `01810`, `00700.HK` | 5位数字或带.HK |
| A股 | `600036`, `000001` | 6位数字 |

---

## 📊 DEV版 vs MAIN版

| 特性 | DEV版 | MAIN版 |
|------|-------|--------|
| 美股支持 | ✅ 完整(AKShare) | ⚠️ 需OpenAI |
| 新闻去重 | ✅ 智能去重 | ❌ 无 |
| 后端自启 | ✅ 自动 | ❌ 需手动 |
| 定时同步 | ✅ 每2小时 | ❌ 需手动 |
| 推荐 | 🔥 推荐使用 | - |

---

## 📞 获取帮助

- 📖 [完整文档](https://github.com/1williamaoayers/TradingAgents-arm32/wiki)
- 🐛 [提交Issue](https://github.com/1williamaoayers/TradingAgents-arm32/issues)
- 💬 [讨论区](https://github.com/1williamaoayers/TradingAgents-arm32/discussions)

---

> 🎉 **DEV分支** - 最新功能，持续更新中！
>
> 最后更新: 2026-01-17
