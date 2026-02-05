#!/bin/bash
set -e

# 多城市简报机器人 - 部署脚本
# 支持标准部署、测试运行和systemd配置

APP_DIR="/opt/philippines-briefing/菲律宾单国信息简报"
LOG_DIR="/var/log/daily-briefing"
USER_NAME="briefing"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

# 显示帮助信息
show_help() {
    cat << EOF
多城市简报机器人 - 部署脚本

用法: $0 [选项]

选项:
    --help, -h          显示此帮助信息
    --test, -t          部署后运行测试
    --systemd           配置systemd定时器（需要root权限）
    --check, -c         仅检查环境，不部署
    --force, -f         强制重新部署（忽略部分检查）

示例:
    $0                  # 标准部署
    $0 --test           # 部署并测试运行
    $0 --systemd        # 配置systemd定时器
    $0 --check          # 仅检查环境

EOF
}

# 解析命令行参数
RUN_TEST=false
SETUP_SYSTEMD=false
CHECK_ONLY=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --test|-t)
            RUN_TEST=true
            shift
            ;;
        --systemd)
            SETUP_SYSTEMD=true
            shift
            ;;
        --check|-c)
            CHECK_ONLY=true
            shift
            ;;
        --force|-f)
            FORCE=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "========================================"
echo "  多城市简报机器人 - 部署脚本"
echo "========================================"
echo ""

# 1. 检查系统环境
print_info "检查系统环境..."

# 检查操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME=$NAME
        OS_VERSION=$VERSION_ID
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    OS_NAME="macOS"
else
    OS_TYPE="unknown"
    OS_NAME="Unknown"
fi
print_info "操作系统: $OS_NAME"

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    print_error "未找到Python3，请先安装Python3.8或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python版本过低: $PYTHON_VERSION (需要3.8+)"
    exit 1
fi
print_success "Python版本: $PYTHON_VERSION"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    print_warning "未找到pip3，尝试安装..."
    if [ "$OS_TYPE" == "linux" ]; then
        if command -v apt-get &> /dev/null; then
            apt-get update && apt-get install -y python3-pip
        elif command -v yum &> /dev/null; then
            yum install -y python3-pip
        else
            print_error "无法自动安装pip3，请手动安装"
            exit 1
        fi
    else
        print_error "请在macOS上手动安装pip3"
        exit 1
    fi
fi
print_success "pip3已安装"

# 检查项目目录
if [ ! -d "$APP_DIR" ]; then
    print_error "项目目录不存在: $APP_DIR"
    print_info "请先将项目上传到该目录，或使用当前目录运行"

    # 尝试使用当前目录
    CURRENT_DIR=$(pwd)
    if [ -f "$CURRENT_DIR/main.py" ]; then
        print_warning "检测到当前目录包含项目文件，使用当前目录: $CURRENT_DIR"
        APP_DIR=$CURRENT_DIR
    else
        exit 1
    fi
else
    cd $APP_DIR
    print_success "项目目录: $APP_DIR"
fi

# 仅检查模式
if [ "$CHECK_ONLY" = true ]; then
    echo ""
    echo "========================================"
    print_success "环境检查完成"
    echo "========================================"
    exit 0
fi

# 2. 创建必要的目录
echo ""
print_info "创建必要的目录..."

# 创建日志目录
if [ ! -d "$LOG_DIR" ]; then
    if [ "$EUID" -eq 0 ]; then
        mkdir -p $LOG_DIR
        chmod 755 $LOG_DIR
        print_success "创建日志目录: $LOG_DIR"
    else
        print_warning "需要root权限创建 $LOG_DIR，将使用当前目录存储日志"
        LOG_DIR="$APP_DIR/logs"
        mkdir -p $LOG_DIR
    fi
else
    print_success "日志目录已存在: $LOG_DIR"
fi

# 创建数据目录
mkdir -p "$APP_DIR/data"
print_success "数据目录: $APP_DIR/data"

# 创建子目录
mkdir -p bots config systemd logrotate
print_success "子目录创建完成"

# 3. 安装Python依赖
echo ""
print_info "安装Python依赖..."

if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --upgrade --quiet
    print_success "Python依赖安装完成"
else
    print_warning "未找到requirements.txt，跳过依赖安装"
fi

# 4. 检查环境变量配置
echo ""
print_info "检查环境变量配置..."

REQUIRED_ENV_VARS=(
    "DINGTALK_CLIENT_ID"
    "DINGTALK_CLIENT_SECRET"
    "DING_ROBOT_CODE"
    "JUHE_API_KEY"
)

MISSING_ENV_VARS=()

# 检查.env文件
if [ -f ".env" ]; then
    print_success "找到.env文件"
    # 加载.env文件
    set -a
    source .env
    set +a
else
    print_warning "未找到.env文件"
fi

# 检查必需的环境变量
for var in "${REQUIRED_ENV_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_ENV_VARS+=($var)
    fi
done

if [ ${#MISSING_ENV_VARS[@]} -gt 0 ]; then
    print_warning "以下环境变量未配置:"
    for var in "${MISSING_ENV_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    print_info "请创建.env文件并配置环境变量:"
    echo ""
    cat << 'EOF'
# 钉钉机器人配置
DINGTALK_CLIENT_ID=your_client_id
DINGTALK_CLIENT_SECRET=your_client_secret
DING_ROBOT_CODE=your_robot_code

# Juhe汇率API密钥
JUHE_API_KEY=your_juhe_api_key
EOF
    echo ""
else
    print_success "所有必需的环境变量已配置"
fi

# 5. 检查配置文件完整性
echo ""
print_info "检查配置文件完整性..."

# 检查机器人配置
if [ -f "config/bots.json" ]; then
    print_success "找到config/bots.json"
    # 验证JSON格式
    if python3 -c "import json; json.load(open('config/bots.json'))" 2>/dev/null; then
        BOT_COUNT=$(python3 -c "import json; data=json.load(open('config/bots.json')); print(len(data.get('bots', [])))" 2>/dev/null || echo "0")
        print_success "机器人配置有效，共 $BOT_COUNT 个机器人"
    else
        print_error "config/bots.json 格式无效"
    fi
else
    print_error "未找到config/bots.json"
fi

# 检查群配置
if [ -f "groups.json" ]; then
    print_success "找到groups.json"
    if python3 -c "import json; json.load(open('groups.json'))" 2>/dev/null; then
        GROUP_COUNT=$(python3 -c "import json; data=json.load(open('groups.json')); print(len(data.get('groups', [])))" 2>/dev/null || echo "0")
        print_success "群配置有效，共 $GROUP_COUNT 个群组"
    else
        print_error "groups.json 格式无效"
    fi
else
    print_warning "未找到groups.json，请运行以下命令配置群组:"
    echo "  python3 interactive_setup.py"
fi

# 6. 配置systemd服务（可选）
if [ "$SETUP_SYSTEMD" = true ]; then
    echo ""
    print_info "配置systemd服务..."

    if [ "$EUID" -ne 0 ]; then
        print_error "配置systemd需要root权限，请使用sudo运行"
    else
        # 复制服务文件
        if [ -f "systemd/daily-briefing.service" ]; then
            cp systemd/daily-briefing.service /etc/systemd/system/
            cp systemd/daily-briefing.timer /etc/systemd/system/

            # 重新加载systemd
            systemctl daemon-reload

            # 启用并启动定时器
            systemctl enable daily-briefing.timer
            systemctl start daily-briefing.timer

            print_success "systemd定时器已配置"
            print_info "查看状态: systemctl status daily-briefing.timer"
            print_info "查看日志: journalctl -u daily-briefing.service"
        else
            print_error "未找到systemd服务文件"
        fi
    fi
fi

# 7. 配置日志轮转（可选）
if [ "$EUID" -eq 0 ] && [ -f "logrotate/daily-briefing" ]; then
    echo ""
    print_info "配置日志轮转..."
    cp logrotate/daily-briefing /etc/logrotate.d/
    print_success "日志轮转已配置"
fi

# 8. 测试运行（可选）
if [ "$RUN_TEST" = true ]; then
    echo ""
    print_info "运行测试..."

    # 列出机器人
    echo ""
    print_info "已配置的机器人:"
    python3 main.py --list || true

    # 询问是否发送测试消息
    echo ""
    read -p "是否发送测试消息到钉钉群? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "运行菲律宾机器人测试..."
        python3 main.py --country PH || print_error "测试运行失败"
    fi
fi

# 9. 部署完成信息
echo ""
echo "========================================"
print_success "部署完成！"
echo "========================================"
echo ""

print_info "项目目录: $APP_DIR"
print_info "日志目录: $LOG_DIR"
echo ""

echo "下一步操作:"
echo ""

if [ ${#MISSING_ENV_VARS[@]} -gt 0 ]; then
    echo "1. 配置环境变量 (.env文件)"
    echo "   vim $APP_DIR/.env"
    echo ""
fi

if [ ! -f "groups.json" ]; then
    echo "2. 配置群组信息"
    echo "   cd $APP_DIR && python3 interactive_setup.py"
    echo ""
fi

echo "3. 手动测试运行"
echo "   cd $APP_DIR"
echo "   python3 main.py --list          # 列出所有机器人"
echo "   python3 main.py                 # 运行所有机器人"
echo "   python3 main.py --country PH    # 仅运行菲律宾机器人"
echo ""

if [ "$SETUP_SYSTEMD" = false ]; then
    echo "4. 配置定时任务 (二选一)"
    echo ""
    echo "   方式A - crontab:"
    echo "   crontab -e"
    echo "   # 添加以下行 (每天上海时间8:30运行)"
    echo "   30 8 * * * cd $APP_DIR && /usr/bin/python3 main.py >> $LOG_DIR/briefing.log 2>&1"
    echo ""
    echo "   方式B - systemd:"
    echo "   sudo $0 --systemd"
    echo ""
fi

echo "5. 健康检查"
echo "   python3 health_check.py         # 完整检查"
echo "   python3 health_check.py --api   # 测试API连接"
echo ""

echo "6. 查看日志"
echo "   tail -f $LOG_DIR/briefing.log"
echo ""

echo "========================================"
