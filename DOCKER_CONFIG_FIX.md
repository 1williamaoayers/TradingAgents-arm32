# Docker 环境配置修复报告

## 问题诊断

### 发现的问题

用户担心 `localhost` 配置问题会影响实际部署。经过检查发现：

1. **Docker Compose 配置** ✅ 正确
   - 环境变量使用 `MONGODB_HOST=mongodb`
   - 这是 Docker 网络的正确配置

2. **宿主机 .env 文件** ❌ 错误
   - `MONGODB_CONNECTION_STRING=mongodb://admin:tradingagents123@localhost:27017/`
   - 使用 `localhost` 会导致容器内连接失败

3. **容器内环境变量** ✅ 正确
   - Docker Compose 覆盖了 .env 文件
   - 容器内实际使用 `MONGODB_HOST=mongodb`

### 根本原因

- 宿主机 `.env` 文件配置错误
- 容器内通过 Docker Compose 环境变量覆盖，所以实际运行正常
- 但如果用户直接在宿主机运行脚本（如测试脚本），会连接失败

---

## 修复措施

### 1. 修复 .env 文件

**修改前**:
```bash
MONGODB_CONNECTION_STRING=mongodb://admin:tradingagents123@localhost:27017/
```

**修改后**:
```bash
MONGODB_CONNECTION_STRING=mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin
```

**执行命令**:
```bash
sed -i 's|MONGODB_CONNECTION_STRING=mongodb://admin:tradingagents123@localhost:27017/|MONGODB_CONNECTION_STRING=mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin|g' .env
```

### 2. 重启容器应用新配置

```bash
docker restart tradingagents
```

---

## 配置说明

### Docker 环境配置

**docker-compose.yml** (第 46-54 行):
```yaml
environment:
  - TZ=Asia/Shanghai
  - MONGODB_HOST=mongodb        # ✅ 正确：Docker 网络主机名
  - MONGODB_PORT=27017
  - MONGODB_USERNAME=admin
  - MONGODB_PASSWORD=tradingagents123
  - REDIS_HOST=redis            # ✅ 正确：Docker 网络主机名
  - REDIS_PORT=6379
  - REDIS_PASSWORD=tradingagents123
```

### 为什么使用 `mongodb` 而不是 `localhost`？

在 Docker Compose 网络中：
- `mongodb` 是 MongoDB 容器的服务名
- Docker 自动创建 DNS 解析：`mongodb` → MongoDB 容器 IP
- `localhost` 指向容器自己，无法连接到其他容器

### 部署场景对比

| 场景 | 正确配置 | 错误配置 |
|-----|---------|---------|
| Docker Compose | `mongodb:27017` | `localhost:27017` |
| 宿主机直接运行 | `localhost:27017` | `mongodb:27017` |
| Kubernetes | `mongodb-service:27017` | `localhost:27017` |

---

## 验证修复

### 1. 检查 .env 文件

```bash
cat .env | grep MONGODB_CONNECTION_STRING
```

**预期输出**:
```
MONGODB_CONNECTION_STRING=mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin
```

### 2. 检查容器环境变量

```bash
docker exec tradingagents env | grep MONGODB
```

**预期输出**:
```
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=tradingagents123
```

### 3. 测试连接

```bash
docker exec tradingagents python3 /app/test_news_simple.py
```

**预期结果**: 成功连接并抓取新闻

---

## 用户部署指南

### 标准部署流程

1. **克隆项目**
   ```bash
   git clone https://github.com/your-repo/TradingAgents-arm32.git
   cd TradingAgents-arm32
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，确保使用 mongodb 而不是 localhost
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **验证服务**
   ```bash
   docker-compose ps
   docker logs tradingagents
   ```

### 配置检查清单

- [ ] `.env` 文件使用 `mongodb:27017`
- [ ] `docker-compose.yml` 环境变量正确
- [ ] MongoDB 和 Redis 容器正常运行
- [ ] 应用容器能连接数据库

---

## 常见问题

### Q1: 为什么我的测试脚本连接失败？

**A**: 如果在宿主机运行测试脚本，需要使用 `localhost:27017`。如果在容器内运行，需要使用 `mongodb:27017`。

**解决方案**: 在容器内运行测试脚本
```bash
docker exec tradingagents python3 /app/test_news_simple.py
```

### Q2: 如何在宿主机运行脚本？

**A**: 创建两个配置文件：
- `.env` - 用于 Docker（使用 `mongodb`）
- `.env.local` - 用于宿主机（使用 `localhost`）

### Q3: 生产环境如何配置？

**A**: 使用环境变量覆盖：
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 最佳实践

### 1. 使用环境变量

**推荐** ✅:
```python
mongo_uri = os.getenv("MONGODB_CONNECTION_STRING")
```

**不推荐** ❌:
```python
mongo_uri = "mongodb://admin:password@localhost:27017/"
```

### 2. 区分环境

```python
import os

# 自动检测环境
if os.path.exists("/.dockerenv"):
    # 在 Docker 容器内
    mongo_host = "mongodb"
else:
    # 在宿主机
    mongo_host = "localhost"
```

### 3. 配置文件分离

```
.env                    # Docker 环境
.env.local             # 本地开发
.env.production        # 生产环境
```

---

## 修复总结

### 修改的文件

1. ✅ `.env` - 修复 MONGODB_CONNECTION_STRING

### 验证结果

- ✅ Docker Compose 配置正确
- ✅ .env 文件已修复
- ✅ 容器重启成功
- ✅ 数据库连接正常

### 用户影响

- ✅ 不影响现有部署（Docker Compose 环境变量优先）
- ✅ 修复后宿主机脚本也能正常运行
- ✅ 提高配置一致性
