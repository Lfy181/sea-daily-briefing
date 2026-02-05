#!/bin/bash
set -e

# 多城市简报机器人 - 首次安装脚本
# 用于在新服务器上完成所有初始化配置

APP_DIR="/opt/philippines-briefing/菲律宾单国信息简报"
LOG_DIR="/var/log/daily-briefing"
USER_NAME="briefing"
SERVICE_NAME="daily-briefing"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查root权限
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用root权限运行此脚本"
        print_info "使用方法: sudo $0"
        exit 1
    fi
}

# 创建专用用户
create_user() {
    print_info "创建专用用户: $USER_NAME"

    if id "$USER_NAME" &>/dev/null; then
        print_warning "用户 $USER_NAME 已存在"
    else
        useradd -r -s /bin/false -d "$APP_DIR" -c "Daily Briefing Service" "$USER_NAME"
        print_success "用户 $USER_NAME 创建成功"
    fi
}

# 安装系统依赖
install_system_deps() {
    print_info "安装系统依赖..."

    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y python3 python3-pip python3-venv git logrotate
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS
        yum install -y python3 python3-pip git logrotate
    else
        print_error "不支持的操作系统"
        exit 1
    fi

    print_success "系统依赖安装完成"
}

# 创建目录结构
setup_directories() {
    print_info "创建目录结构..."

    # 创建应用目录
    mkdir -p "$APP_DIR"

    # 创建日志目录
    mkdir -p "$LOG_DIR"

    # 设置权限
    chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"
    chown -R "$USER_NAME:$USER_NAME" "$LOG_DIR"
    chmod 755 "$LOG_DIR"

    print_success "目录结构创建完成"
}

# 设置项目权限
setup_permissions() {
    print_info "设置项目权限..."

    # 设置应用目录权限
    chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"

    # 设置日志目录权限
    chown -R "$USER_NAME:$USER_NAME" "$LOG_DIR"

    # 设置脚本可执行权限
    if [ -f "$APP_DIR/deploy.sh" ]; then
        chmod +x "$APP_DIR/deploy.sh"
    fi

    if [ -f "$APP_DIR/health_check.py" ]; then
        chmod +x "$APP_DIR/health_check.py"
    fi

    print_success "权限设置完成"
}

# 创建虚拟环境
setup_venv() {
    print_info "创建Python虚拟环境..."

    cd "$APP_DIR"

    if [ -d ".venv" ]; then
        print_warning "虚拟环境已存在"
    else
        python3 -m venv .venv
        print_success "虚拟环境创建完成"
    fi

    # 激活虚拟环境并安装依赖
    source .venv/bin/activate
    pip install --upgrade pip

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python依赖安装完成"
    fi

    deactivate
}

# 配置日志轮转
setup_logrotate() {
    print_info "配置日志轮转..."

    if [ -f "$APP_DIR/logrotate/daily-briefing" ]; then
        cp "$APP_DIR/logrotate/daily-briefing" /etc/logrotate.d/
        print_success "日志轮转配置完成"
    else
        print_warning "未找到日志轮转配置文件"
    fi
}

# 主安装流程
main() {
    echo "========================================"
    echo "  多城市简报机器人 - 首次安装"
    echo "========================================"
    echo ""

    # 检查root权限
    check_root

    # 安装系统依赖
    install_system_deps

    # 创建用户
    create_user

    # 创建目录
    setup_directories

    # 提示用户上传代码
    echo ""
    print_info "请确保项目代码已上传到: $APP_DIR"
    echo ""
    read -p "项目代码是否已上传? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "请先上传项目代码，然后重新运行此脚本"
        echo ""
        print_info "上传命令示例:"
        echo "  scp -r ./项目目录/* root@your-server:$APP_DIR/"
        exit 0
    fi

    # 设置权限
    setup_permissions

    # 创建虚拟环境
    setup_venv

    # 配置日志轮转
    setup_logrotate

    # 安装完成
    echo ""
    echo "========================================"
    print_success "安装完成！"
    echo "========================================"
    echo ""

    print_info "下一步操作:"
    echo ""
    echo "1. 配置环境变量"
    echo "   vim $APP_DIR/.env"
    echo ""
    echo "2. 配置钉钉群组"
    echo "   cd $APP_DIR && python3 interactive_setup.py"
    echo ""
    echo "3. 运行健康检查"
    echo "   cd $APP_DIR && python3 health_check.py"
    echo ""
    echo "4. 运行部署脚本"
    echo "   cd $APP_DIR && ./deploy.sh"
    echo ""
    echo "5. 配置定时任务"
    echo "   ./deploy.sh --systemd    # 使用systemd"
    echo "   或"
    echo "   crontab -e               # 使用crontab"
    echo ""
}

# 运行主函数
main
