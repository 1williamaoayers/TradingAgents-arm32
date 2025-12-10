# 🚀 TradingAgents 快速部署指南

> 一键部署,开箱即用!

---

## 📋 前置要求

- 一台服务器 (VPS/NAS/本地)
- 已安装 Docker
- 至少 2GB 内存
- 至少 10GB 磁盘空间

---

## 🎯 快速开始 (3步)

### 1️⃣ 安装 Docker

**Linux (推荐)**:
```bash
curl -fsSL https://get.docker.com | sh
```

**其他系统**:
- Windows/Mac: 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop)

### 2️⃣ 下载项目

```bash
git clone https://github.com/1williamaoayers/TradingAgents-arm32.git
cd TradingAgents-arm32
```

### 3️⃣ 一键部署

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**就这么简单!** 🎉

---

### 🎯 更简单的方式 (不需要克隆仓库)

```bash
# 1. 创建部署目录
mkdir -p /home/tradingagents && cd /home/tradingagents

# 2. 下载配置文件
curl -O https://raw.githubusercontent.com/1williamaoayers/TradingAgents-arm32/main/docker-compose.yml

# 3. 启动服务
docker-compose up -d

# 首次访问 http://你的IP:8501 在Web界面配置API密钥
```

---

## 🌐 访问应用

部署完成后,在浏览器中访问:

```
http://你的服务器IP:8501
```

例如:
- 本地: `http://localhost:8501`
- VPS: `http://123.456.789.0:8501`
- NAS: `http://192.168.1.100:8501`

---

## ⚙️ 配置API密钥

编辑 `.env` 文件:

```bash
nano .env
```

填入你的API密钥:
```env
OPENAI_API_KEY=sk-xxxxx
DEEPSEEK_API_KEY=sk-xxxxx
```

保存后重启:
```bash
docker-compose restart
```

---

## 📱 支持的架构

- ✅ x86_64 (Intel/AMD)
- ✅ ARM64 (树莓派4/5, Apple M系列)
- ✅ ARM32 (树莓派3)

镜像会自动选择适合你设备的版本!

---

## 🔧 常用命令

### 查看日志
```bash
docker-compose logs -f
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 更新到最新版本
```bash
docker-compose pull
docker-compose up -d
```

### 备份数据
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/
```

### 完全卸载 (释放全部磁盘空间)
```bash
cd /home/tradingagents && docker-compose down -v --rmi all && cd / && rm -rf /home/tradingagents
```

---

## 🐛 故障排查

### 问题1: 端口被占用

**错误**: `port is already allocated`

**解决**:
```bash
# 修改端口
nano docker-compose.yml
# 将 8501:8501 改为 8502:8501
```

### 问题2: 内存不足

**错误**: `cannot allocate memory`

**解决**:
- 增加服务器内存
- 或关闭其他服务

### 问题3: 权限不足

**错误**: `permission denied`

**解决**:
```bash
sudo chmod +x scripts/deploy.sh
sudo ./scripts/deploy.sh
```

### 问题4: Docker未运行

**错误**: `Cannot connect to the Docker daemon`

**解决**:
```bash
# Linux
sudo systemctl start docker

# Windows/Mac
# 启动 Docker Desktop
```

---

## 🔄 更新应用

### 自动更新 (推荐)

```bash
./scripts/update.sh
```

### 手动更新

```bash
# 1. 拉取最新镜像
docker-compose pull

# 2. 重启服务
docker-compose up -d
```

---

## 📊 性能优化

### 增加内存限制

编辑 `docker-compose.yml`:
```yaml
services:
  tradingagents:
    deploy:
      resources:
        limits:
          memory: 4G
```

### 使用SSD存储

将数据目录挂载到SSD:
```yaml
volumes:
  - /path/to/ssd/data:/app/data
```

---

## 🔒 安全建议

### 1. 修改默认端口

```yaml
ports:
  - "8888:8501"  # 改为其他端口
```

### 2. 使用反向代理

推荐使用 Nginx 或 Caddy:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
    }
}
```

### 3. 启用HTTPS

使用 Let's Encrypt 免费证书

---

## 📚 进阶配置

### 使用MongoDB

编辑 `.env`:
```env
USE_MONGODB_STORAGE=true
MONGODB_URI=mongodb://localhost:27017/
```

启动MongoDB:
```bash
docker run -d -p 27017:27017 --name mongodb mongo:7
```

### 使用Redis

编辑 `.env`:
```env
REDIS_HOST=localhost
REDIS_PORT=6379
```

启动Redis:
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

---

## 🆘 需要帮助?

- 📖 查看 [完整文档](docs/DOCKER.md)
- 🐛 提交 [Issue](https://github.com/1williamaoayers/TradingAgents-arm32/issues)
- 💬 加入讨论群

---

## 📝 许可证

MIT License

---

**祝你使用愉快!** 🎉
