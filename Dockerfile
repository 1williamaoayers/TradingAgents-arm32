# ============================================
# TradingAgents Docker 镜像
# 支持 amd64 和 arm64 架构
# ============================================

# 阶段1: 基础镜像
FROM python:3.10-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# 阶段2: 依赖安装
# ============================================
FROM base as builder

WORKDIR /build

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --user --no-warn-script-location -r requirements.txt

# ============================================
# 阶段3: 运行环境
# ============================================
FROM base as runtime

# 创建应用用户
RUN useradd -m -u 1000 -s /bin/bash appuser

# 设置工作目录
WORKDIR /app

# 从builder复制依赖到多个位置，确保无论以何种用户运行都能找到
COPY --from=builder /root/.local /root/.local
COPY --from=builder /root/.local /home/appuser/.local

# 设置PATH（同时支持root和appuser）
ENV PATH=/root/.local/bin:/home/appuser/.local/bin:$PATH

# 创建数据目录和配置文件（这些层很少变动，放在COPY代码之前）
RUN mkdir -p /app/data /app/logs /app/cache /app/backups && \
    touch /app/.env && \
    chown -R appuser:appuser /app && \
    chmod 644 /app/.env

# 复制应用代码（这是最常变动的层，放在最后）
COPY --chown=appuser:appuser . .

# 复制初始化脚本并设置权限
# 注意：虽然COPY . .已经包含了scripts目录，但为了确保权限正确，再次显式设置
RUN chmod +x /app/scripts/docker-init.sh

# 切换到应用用户
USER appuser

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 使用初始化脚本作为入口点
ENTRYPOINT ["/app/scripts/docker-init.sh"]

# 启动Streamlit应用
CMD ["python", "-m", "streamlit", "run", "web/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
