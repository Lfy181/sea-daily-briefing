#!/usr/bin/env python3
"""
多城市每日简报机器人 - 主入口
支持菲律宾、越南、印尼、马来西亚四个城市

功能:
- 读取config/bots.json获取机器人配置
- 遍历所有机器人，获取天气和汇率数据
- 发送简报到配置的钉钉群
- 支持定时调度

部署:
1. 配置.env文件（添加DINGTALK_CLIENT_ID, DINGTALK_CLIENT_SECRET, DING_ROBOT_CODE, JUHE_API_KEY）
2. 运行interactive_setup.py配置群信息
3. 配置crontab: 30 8 * * * cd /opt/philippines-briefing && /usr/bin/python3 main.py
"""

import os
import sys
import logging
import argparse
from datetime import datetime

import pytz
from dotenv import load_dotenv

from bots.bot_factory import BotFactory

# 加载环境变量
load_dotenv()

# 配置日志
LOG_DIR = "/var/log/daily-briefing"
LOG_FILE = os.path.join(LOG_DIR, "briefing.log")

# 如果日志目录存在则使用，否则使用当前目录
if os.path.exists(LOG_DIR):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

logger = logging.getLogger(__name__)

# 上海时区
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')


def run_all_bots():
    """
    运行所有配置的机器人
    """
    logger.info("=" * 60)
    logger.info("多城市每日简报推送开始")
    logger.info("=" * 60)

    # 获取当前上海时间
    now = datetime.now(SHANGHAI_TZ)
    logger.info(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} (Asia/Shanghai)")

    # 创建所有机器人
    bots = BotFactory.create_all_bots("config/bots.json")

    if not bots:
        logger.error("没有可用的机器人配置")
        return

    # 执行每个机器人
    success_count = 0
    for bot in bots:
        try:
            result = bot.run()
            if result:
                success_count += 1
        except Exception as e:
            logger.error(f"运行机器人'{bot.name}'时出错: {e}")

    logger.info("=" * 60)
    logger.info(f"简报推送完成: {success_count}/{len(bots)}个机器人成功")
    logger.info("=" * 60)


def run_single_bot(bot_name: str):
    """
    运行单个指定的机器人

    Args:
        bot_name: 机器人名称
    """
    logger.info("=" * 60)
    logger.info(f"运行单个机器人: {bot_name}")
    logger.info("=" * 60)

    bot = BotFactory.get_bot_by_name(bot_name, "config/bots.json")

    if not bot:
        logger.error(f"未找到机器人: {bot_name}")
        return

    try:
        result = bot.run()
        if result:
            logger.info(f"机器人'{bot_name}'执行成功")
        else:
            logger.error(f"机器人'{bot_name}'执行失败")
    except Exception as e:
        logger.error(f"运行机器人'{bot_name}'时出错: {e}")


def run_by_country(country_code: str):
    """
    运行指定国家的机器人

    Args:
        country_code: 国家代码（如 'PH', 'VN', 'ID', 'MY'）
    """
    logger.info("=" * 60)
    logger.info(f"运行国家机器人: {country_code}")
    logger.info("=" * 60)

    bot = BotFactory.get_bot_by_country(country_code, "config/bots.json")

    if not bot:
        logger.error(f"未找到国家代码为'{country_code}'的机器人")
        return

    try:
        result = bot.run()
        if result:
            logger.info(f"国家'{country_code}'机器人执行成功")
        else:
            logger.error(f"国家'{country_code}'机器人执行失败")
    except Exception as e:
        logger.error(f"运行国家'{country_code}'机器人时出错: {e}")


def list_bots():
    """
    列出所有配置的机器人
    """
    configs = BotFactory.load_bots_config("config/bots.json")

    print("\n已配置的机器人列表:")
    print("-" * 60)
    print(f"{'名称':<20} {'国家':<6} {'城市':<20} {'货币':<10}")
    print("-" * 60)

    for config in configs:
        name = config.get('name', 'N/A')
        country = config.get('country', 'N/A')
        city = config.get('city', 'N/A')
        currency = config.get('currency', 'N/A')
        print(f"{name:<20} {country:<6} {city:<20} {currency:<10}")

    print("-" * 60)
    print(f"总计: {len(configs)}个机器人\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="多城市每日简报机器人",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 运行所有机器人
  python main.py --list             # 列出所有机器人
  python main.py --bot "菲律宾简报机器人"  # 运行指定机器人
  python main.py --country PH       # 运行指定国家机器人
        """
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有配置的机器人"
    )

    parser.add_argument(
        "--bot", "-b",
        type=str,
        help="运行指定名称的机器人"
    )

    parser.add_argument(
        "--country", "-c",
        type=str,
        help="运行指定国家代码的机器人（如 PH, VN, ID, MY）"
    )

    args = parser.parse_args()

    if args.list:
        list_bots()
    elif args.bot:
        run_single_bot(args.bot)
    elif args.country:
        run_by_country(args.country.upper())
    else:
        run_all_bots()


if __name__ == "__main__":
    main()
