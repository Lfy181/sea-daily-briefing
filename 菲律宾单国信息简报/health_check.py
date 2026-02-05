#!/usr/bin/env python3
"""
健康检查脚本
检查机器人配置完整性、API连接和系统环境
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 添加项目目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str):
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_info(message: str):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def print_header(message: str):
    print(f"\n{Colors.BOLD}{message}{Colors.RESET}")
    print("=" * 60)


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_warnings = 0

    def check_result(self, passed: bool, message: str, is_warning: bool = False):
        """记录检查结果"""
        if passed:
            print_success(message)
            self.checks_passed += 1
        elif is_warning:
            print_warning(message)
            self.checks_warnings += 1
        else:
            print_error(message)
            self.checks_failed += 1
        return passed

    def check_python_version(self) -> bool:
        """检查Python版本"""
        print_header("Python环境检查")

        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        if version.major == 3 and version.minor >= 8:
            return self.check_result(True, f"Python版本: {version_str} (符合要求 3.8+)")
        else:
            return self.check_result(False, f"Python版本: {version_str} (需要 3.8+)")

    def check_dependencies(self) -> bool:
        """检查Python依赖"""
        print_header("依赖检查")

        required_packages = [
            "requests",
            "python-dotenv",
            "pytz",
        ]

        all_passed = True
        for package in required_packages:
            try:
                if package == "python-dotenv":
                    __import__("dotenv")
                else:
                    __import__(package)
                self.check_result(True, f"{package} 已安装")
            except ImportError:
                self.check_result(False, f"{package} 未安装")
                all_passed = False

        return all_passed

    def check_environment_variables(self) -> bool:
        """检查环境变量"""
        print_header("环境变量检查")

        required_vars = [
            ("DINGTALK_CLIENT_ID", "钉钉Client ID"),
            ("DINGTALK_CLIENT_SECRET", "钉钉Client Secret"),
            ("DING_ROBOT_CODE", "钉钉机器人Code"),
            ("JUHE_API_KEY", "Juhe API密钥"),
        ]

        all_passed = True
        for var_name, description in required_vars:
            value = os.getenv(var_name)
            if value:
                # 显示部分值（保护敏感信息）
                masked = value[:4] + "****" if len(value) > 4 else "****"
                self.check_result(True, f"{description} ({var_name}): {masked}")
            else:
                self.check_result(False, f"{description} ({var_name}): 未配置")
                all_passed = False

        return all_passed

    def check_config_files(self) -> bool:
        """检查配置文件"""
        print_header("配置文件检查")

        all_passed = True

        # 检查机器人配置
        if os.path.exists("config/bots.json"):
            try:
                with open("config/bots.json", "r", encoding="utf-8") as f:
                    bots_config = json.load(f)
                bots = bots_config.get("bots", [])
                self.check_result(True, f"config/bots.json 有效，配置 {len(bots)} 个机器人")

                # 检查每个机器人的配置
                for bot in bots:
                    name = bot.get("name", "未命名")
                    required_fields = ["name", "country", "city", "latitude", "longitude", "currency"]
                    missing = [f for f in required_fields if not bot.get(f)]
                    if missing:
                        self.check_result(False, f"机器人 '{name}' 缺少字段: {', '.join(missing)}")
                        all_passed = False

            except json.JSONDecodeError as e:
                self.check_result(False, f"config/bots.json 格式错误: {e}")
                all_passed = False
            except Exception as e:
                self.check_result(False, f"config/bots.json 读取失败: {e}")
                all_passed = False
        else:
            self.check_result(False, "config/bots.json 不存在")
            all_passed = False

        # 检查群配置
        if os.path.exists("groups.json"):
            try:
                with open("groups.json", "r", encoding="utf-8") as f:
                    groups_config = json.load(f)
                groups = groups_config.get("groups", [])
                self.check_result(True, f"groups.json 有效，配置 {len(groups)} 个群组")

                # 检查每个群的配置
                for group in groups:
                    name = group.get("name", "未命名")
                    if not group.get("open_conversation_id"):
                        self.check_result(
                            False,
                            f"群组 '{name}' 缺少 open_conversation_id"
                        )
                        all_passed = False

            except json.JSONDecodeError as e:
                self.check_result(False, f"groups.json 格式错误: {e}")
                all_passed = False
            except Exception as e:
                self.check_result(False, f"groups.json 读取失败: {e}")
                all_passed = False
        else:
            self.check_result(False, "groups.json 不存在")
            all_passed = False

        # 检查.env文件
        if os.path.exists(".env"):
            self.check_result(True, ".env 文件存在")
        else:
            self.check_result(True, ".env 文件不存在（将从环境变量读取）", is_warning=True)

        return all_passed

    def check_directories(self) -> bool:
        """检查目录结构"""
        print_header("目录结构检查")

        required_dirs = [
            "bots",
            "config",
            "data",
        ]

        all_passed = True
        for dir_name in required_dirs:
            if os.path.isdir(dir_name):
                self.check_result(True, f"{dir_name}/ 目录存在")
            else:
                if dir_name == "data":
                    # data目录可以自动创建
                    try:
                        os.makedirs(dir_name, exist_ok=True)
                        self.check_result(True, f"{dir_name}/ 目录已创建")
                    except Exception as e:
                        self.check_result(False, f"{dir_name}/ 目录创建失败: {e}")
                        all_passed = False
                else:
                    self.check_result(False, f"{dir_name}/ 目录不存在")
                    all_passed = False

        # 检查日志目录
        log_dir = "/var/log/daily-briefing"
        if os.path.isdir(log_dir):
            self.check_result(True, f"日志目录 {log_dir} 存在")
        else:
            self.check_result(
                True,
                f"日志目录 {log_dir} 不存在（将使用本地logs目录）",
                is_warning=True
            )

        return all_passed

    def test_juhe_api(self) -> bool:
        """测试Juhe汇率API"""
        print_header("Juhe汇率API测试")

        api_key = os.getenv("JUHE_API_KEY")
        if not api_key:
            self.check_result(False, "未配置JUHE_API_KEY，跳过API测试")
            return False

        try:
            import requests

            url = "http://op.juhe.cn/onebox/exchange/currency"
            params = {
                "key": api_key,
                "from": "CNY",
                "to": "PHP",
                "version": 2
            }

            print_info("正在测试汇率API...")
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("error_code") == 0:
                result = data.get("result", [])
                if result:
                    rate = result[0].get("exchange")
                    self.check_result(True, f"API连接成功，CNY/PHP汇率: {rate}")
                    return True
                else:
                    self.check_result(False, "API返回空数据")
                    return False
            else:
                error_msg = data.get("reason", "未知错误")
                self.check_result(False, f"API错误: {error_msg}")
                return False

        except Exception as e:
            self.check_result(False, f"API测试失败: {e}")
            return False

    def test_dingtalk_connection(self) -> bool:
        """测试钉钉连接"""
        print_header("钉钉连接测试")

        app_key = os.getenv("DINGTALK_CLIENT_ID")
        app_secret = os.getenv("DINGTALK_CLIENT_SECRET")

        if not app_key or not app_secret:
            self.check_result(False, "未配置钉钉凭证，跳过连接测试")
            return False

        try:
            import requests

            url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
            headers = {"Content-Type": "application/json"}
            data = {"appKey": app_key, "appSecret": app_secret}

            print_info("正在测试钉钉API...")
            response = requests.post(url, headers=headers, json=data, timeout=10)
            result = response.json()

            if "accessToken" in result:
                self.check_result(True, "钉钉API连接成功，Token获取正常")
                return True
            else:
                error_code = result.get("code", "unknown")
                error_msg = result.get("message", "未知错误")
                self.check_result(False, f"钉钉API错误: {error_code} - {error_msg}")
                return False

        except Exception as e:
            self.check_result(False, f"钉钉连接测试失败: {e}")
            return False

    def test_weather_api(self) -> bool:
        """测试天气API"""
        print_header("天气API测试")

        try:
            import requests

            # 测试马尼拉天气
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": 14.5995,
                "longitude": 120.9842,
                "daily": "weather_code",
                "forecast_days": 1,
                "timezone": "Asia/Manila",
            }

            print_info("正在测试天气API...")
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if "daily" in data:
                self.check_result(True, "天气API连接成功，数据获取正常")
                return True
            else:
                self.check_result(False, "天气API返回异常数据")
                return False

        except Exception as e:
            self.check_result(False, f"天气API测试失败: {e}")
            return False

    def print_summary(self):
        """打印检查摘要"""
        print_header("检查摘要")

        total = self.checks_passed + self.checks_failed + self.checks_warnings

        print(f"总检查项: {total}")
        print(f"{Colors.GREEN}通过: {self.checks_passed}{Colors.RESET}")
        print(f"{Colors.RED}失败: {self.checks_failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}警告: {self.checks_warnings}{Colors.RESET}")

        print()
        if self.checks_failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ 所有关键检查通过！系统健康。{Colors.RESET}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ 发现 {self.checks_failed} 个问题，请修复后重试。{Colors.RESET}")

        return self.checks_failed == 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="健康检查脚本 - 检查机器人配置和API连接",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python health_check.py              # 完整检查
  python health_check.py --config     # 仅检查配置
  python health_check.py --api        # 仅测试API连接
        """
    )

    parser.add_argument(
        "--config", "-c",
        action="store_true",
        help="仅检查配置（不测试API）"
    )

    parser.add_argument(
        "--api", "-a",
        action="store_true",
        help="仅测试API连接"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细信息"
    )

    args = parser.parse_args()

    print(f"{Colors.BOLD}")
    print("=" * 60)
    print("  多城市简报机器人 - 健康检查")
    print("=" * 60)
    print(f"{Colors.RESET}")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    checker = HealthChecker()

    # 根据参数执行检查
    if args.api:
        # 仅测试API
        checker.test_juhe_api()
        checker.test_dingtalk_connection()
        checker.test_weather_api()
    elif args.config:
        # 仅检查配置
        checker.check_python_version()
        checker.check_dependencies()
        checker.check_environment_variables()
        checker.check_config_files()
        checker.check_directories()
    else:
        # 完整检查
        checker.check_python_version()
        checker.check_dependencies()
        checker.check_environment_variables()
        checker.check_config_files()
        checker.check_directories()
        checker.test_juhe_api()
        checker.test_dingtalk_connection()
        checker.test_weather_api()

    # 打印摘要
    success = checker.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
