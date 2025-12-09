#!/bin/bash

# ============================================
# TradingAgents 一键部署脚本
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示Logo
show_logo() {
    cat << 'EOF'
╔════════════════════════════════════════╗
║                                        ║
║     TradingAgents 一键部署工具         ║
║                                        ║
║     支持: VPS / NAS / 本地服务器       ║
║                                        ║
╚════════════════════════════════════════╝
EOF
    echo ""
}

# 检查Docker
check_docker() {
    print_info "检查 Docker 是否安装..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        echo ""
        echo "请先安装 Docker:"
        echo "  Linux: curl -fsSL https://get.docker.com | sh"
        echo "  Windows/Mac: 下载 Docker Desktop"
        echo ""
        exit 1
    fi
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        print_error "Docker 未运行,请启动 Docker"
        exit 1
    fi
    
    print_success "Docker 已安装并运行"
}

# 检查Docker Compose
check_docker_compose() {
    print_info "检查 Docker Compose 是否安装..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装"
        exit 1
    fi
    print_success "Docker Compose 已安装"
}

# 创建.env文件
create_env_file() {
    if [ ! -f .env ]; then
        print_info "创建 .env 配置文件..."
        cat > .env << 'EOF'
# ============================================
# TradingAgents 配置文件
# ============================================

# API密钥配置 (必填)
OPENAI_API_KEY=your_openai_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 数据库配置 (可选)
USE_MONGODB_STORAGE=false
MONGODB_URI=mongodb://localhost:27017/

# 时区设置
TZ=Asia/Shanghai

# 其他配置
# REDIS_HOST=localhost
# REDIS_PORT=6379
EOF
        print_success ".env 文件已创建"
        echo ""
        print_warning "⚠️  重要: 请编辑 .env 文件,填入你的API密钥"
        print_info "编辑命令: nano .env 或 vim .env"
        echo ""
        read -p "按回车键继续..."
    else
        print_success ".env 文件已存在"
    fi
}

# 创建数据目录
create_directories() {
    print_info "创建数据目录..."
    mkdir -p data logs cache
    print_success "数据目录已创建"
}

# 拉取镜像
pull_image() {
    print_info "拉取 Docker 镜像..."
    docker-compose pull
    print_success "镜像拉取完成"
}

# 启动服务
start_services() {
    print_info "启动服务..."
    docker-compose up -d
    print_success "服务已启动"
}

# 等待服务就绪
wait_for_service() {
    print_info "等待服务启动..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
            print_success "服务已就绪"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    echo ""
    print_warning "服务启动超时,请检查日志"
    return 1
}

# 显示状态
show_status() {
    echo ""
    echo "============================================"
    print_success "部署完成!"
    echo "============================================"
    echo ""
    print_info "服务状态:"
    docker-compose ps
    echo ""
    print_info "访问地址:"
    echo "  本地: http://localhost:8501"
    echo "  局域网: http://$(hostname -I | awk '{print $1}'):8501"
    echo ""
    print_info "常用命令:"
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo "  更新应用: docker-compose pull && docker-compose up -d"
    echo ""
}

# 主函数
main() {
    show_logo
    
    check_docker
    check_docker_compose
    create_env_file
    create_directories
    pull_image
    start_services
    wait_for_service
    show_status
}

# 执行
main
