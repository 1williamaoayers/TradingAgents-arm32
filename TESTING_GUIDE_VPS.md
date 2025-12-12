# VPS 真实环境测试指南

本指南将协助您在 VPS 上验证 TradingAgents 的部署状态，并进行真实的股票分析测试。

## 📋 准备工作

1. 确保您已经通过 Docker 启动了服务：
   ```bash
   docker-compose up -d
   ```

2. 确保您的代码是最新的（包含了 `scripts/verify_vps.py`）：
   ```bash
   git pull
   ```

## 🛠️ 步骤 1：系统健康自检

我们提供了一个自动化脚本，可以在容器内部运行，检查数据库连接、API Key 配置和 AI 模型初始化状态。

在 VPS 终端执行以下命令：

```bash
# 进入容器并运行验证脚本
docker exec -it tradingagents python scripts/verify_vps.py
```

**预期输出：**
- ✅ MongoDB 连接成功
- ✅ Redis 连接成功
- ✅ 发现 LLM Key
- ✅ TradingAgentsGraph 初始化成功

如果遇到 ❌ 失败，请根据错误提示检查 `.env` 文件或数据库服务状态。

## 🖥️ 步骤 2：CLI 交互式测试 (推荐)

在不配置浏览器访问的情况下，最直接的测试方式是使用命令行界面 (CLI)。这将完整跑通整个 AI 分析流程。

1. **进入 CLI 模式**：
   ```bash
   docker exec -it tradingagents python -m cli.main analyze
   ```

2. **按照提示操作**：
   - 选择市场（如 A股）
   - 输入代码（如 `000001`）
   - 选择分析师（建议全选）
   - 选择研究深度（建议先选 `1` 级进行快速测试）

3. **观察输出**：
   - 您应该能看到各个 Agent 开始工作，输出分析日志。
   - 最终会生成一份投资报告。

如果这一步成功，说明核心业务逻辑完全正常。

## 🌐 步骤 3：Web 界面测试

如果您开放了 VPS 的 `8501` 端口，可以通过浏览器访问：

1. 打开浏览器访问 `http://<您的VPS_IP>:8501`
2. 尝试输入一个股票代码进行分析。
3. 观察右侧的进度条是否正常走动。

**注意**：Streamlit 应用首次启动分析时可能需要下载一些数据，可能会稍慢。

## ❓ 常见问题排查

### 1. 数据库连接失败
- 检查 `docker ps` 确保 `mongo` 和 `redis` 容器都在运行。
- 检查 `.env` 中的 `MONGODB_HOST` 是否设置为 `mongo`（在 Docker 网络中）。

### 2. API Key 报错
- 确认 `.env` 文件中已填入正确的 Key。
- 如果使用的是 DeepSeek 或 DashScope，确保没有余额不足。
- 修改配置后需要重启容器：`docker-compose restart`

### 3. 分析过程卡住
- 可能是网络问题导致连接 LLM 超时。
- 尝试在 CLI 模式下运行，可以看到更详细的错误日志。
- 查看容器日志：`docker logs -f tradingagents`

### 4. 找不到 verify_vps.py
- 如果您无法更新代码，可以手动创建该文件，或者直接使用 CLI 测试（步骤 2）。
