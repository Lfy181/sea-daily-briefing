#!/bin/bash
# 菲律宾每日简报机器人 - 部署脚本
# 在阿里云ECS上运行此脚本完成部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
APP_DIR="/opt/daily-briefing"
LOG_DIR="/var/log/daily-briefing"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  菲律宾每日简报机器人 - 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 1. 安装依赖
echo -e "${YELLOW}[1/7] 安装系统依赖...${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv git curl

# 2. 创建工作目录
echo -e "${YELLOW}[2/7] 创建工作目录...${NC}"
mkdir -p $APP_DIR
mkdir -p $LOG_DIR

# 3. 复制代码文件（假设代码已通过SCP上传）
echo -e "${YELLOW}[3/7] 检查代码文件...${NC}"
if [ ! -f "$APP_DIR/main.py" ]; then
    echo -e "${RED}错误: 代码文件不存在于 $APP_DIR${NC}"
    echo "请先上传代码文件到 $APP_DIR 目录:"
    echo "  - main.py"
    echo "  - dingtalk_client.py"
    echo "  - get_group_id.py"
    echo "  - requirements.txt"
    echo "  - .env"
    echo "  - groups.json"
    exit 1
fi

# 4. 安装Python依赖
echo -e "${YELLOW}[4/7] 安装Python依赖...${NC}"
cd $APP_DIR
pip3 install -r requirements.txt

# 5. 设置文件权限
echo -e "${YELLOW}[5/7] 设置文件权限...${NC}"
chmod +x $APP_DIR/main.py
chmod +x $APP_DIR/get_group_id.py
chmod 644 $APP_DIR/.env
chmod 666 $LOG_DIR

# 6. 配置crontab
echo -e "${YELLOW}[6/7] 配置定时任务...${NC}"
echo "添加以下行到crontab（每天UTC 00:00运行，即北京时间8:00）:"
echo "0 0 * * * cd $APP_DIR && /usr/bin/python3 main.py >> $LOG_DIR/briefing.log 2>&1"
echo ""
read -p "是否自动添加crontab? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    (crontab -l 2>/dev/null || echo "") | grep -v "daily-briefing" | (cat; echo "0 0 * * * cd $APP_DIR && /usr/bin/python3 main.py >> $LOG_DIR/briefing.log 2>&1") | crontab -
    echo -e "${GREEN}定时任务已添加${NC}"
else
    echo -e "${YELLOW}跳过自动添加，请手动添加crontab${NC}"
fi

# 7. 完成提示
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "下一步操作:"
echo "1. 确保机器人已加入目标群（群号: 161775015441）"
echo "2. 运行以下命令获取群open_conversation_id:"
echo "   cd $APP_DIR && python3 get_group_id.py 161775015441"
echo ""
echo "3. 手动测试运行:"
echo "   cd $APP_DIR && python3 main.py"
echo ""
echo "4. 查看日志:"
echo "   tail -f $LOG_DIR/briefing.log"
echo ""
echo "5. 检查定时任务:"
echo "   crontab -l"
echo ""
