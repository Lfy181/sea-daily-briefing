#!/usr/bin/env python3
"""
菲律宾每日简报机器人 - 企业机器人版（已修复）
每日自动抓取马尼拉天气（7天预报）和汇率，推送至钉钉群

功能:
- 获取Open-Meteo 7天天气数据（含weather_code）
- 获取Juhe汇率（CNY→PHP）
- 生成简洁文本格式（日期、天气、温度、降雨、风速）
- 读取groups.json获取群列表
- 遍历群列表发送简报
- 日志输出到/var/log/daily-briefing/briefing.log

部署:
1. 配置.env文件（添加DINGTALK_CLIENT_ID, DINGTALK_CLIENT_SECRET, DING_ROBOT_CODE）
2. 运行get_group_id.py获取群open_conversation_id
3. 配置crontab: 0 0 * * * cd /opt/daily-briefing && /usr/bin/python3 main.py >> /var/log/daily-briefing/briefing.log 2>&1
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

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

# API配置
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
EXCHANGE_API_URL = "http://op.juhe.cn/onebox/exchange/currency"

# 钉钉配置（从环境变量读取）
DINGTALK_CLIENT_ID = os.getenv("DINGTALK_CLIENT_ID", "dingqswguvtbhcnprqxc")
DINGTALK_CLIENT_SECRET = os.getenv("DINGTALK_CLIENT_SECRET", "")
DING_ROBOT_CODE = os.getenv("DING_ROBOT_CODE", "dingqswguvtbhcnprqxc")

# 马尼拉坐标
MANILA_LAT = 14.5995
MANILA_LON = 120.9842

# WMO天气代码映射（中文）
WEATHER_CODE_MAP = {
    0: "☀️ 晴",
    1: "🌤️ 多云",
    2: "⛅ 多云",
    3: "☁️ 阴",
    45: "🌫️ 雾",
    48: "🌫️ 雾凇",
    51: "🌧️ 小雨",
    53: "🌧️ 中雨",
    55: "🌧️ 大雨",
    56: "🌧️ 冻雨",
    57: "🌧️ 冻雨",
    61: "🌧️ 小雨",
    63: "🌧️ 中雨",
    65: "🌧️ 大雨",
    66: "🌧️ 冻雨",
    67: "🌧️ 冻雨",
    71: "🌨️ 小雪",
    73: "🌨️ 中雪",
    75: "🌨️ 大雪",
    77: "🌨️ 雪粒",
    80: "🌧️ 阵雨",
    81: "🌧️ 中雨",
    82: "⛈️ 暴雨",
    85: "🌨️ 阵雪",
    86: "🌨️ 阵雪",
    95: "⛈️ 雷暴",
    96: "⛈️ 雷暴伴冰雹",
    99: "⛈️ 雷暴伴冰雹",
}

# 星期映射
WEEKDAY_MAP = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class DingTalkRobot:
    """
    钉钉企业机器人客户端（新版API）
    """

    def __init__(self, app_key: str, app_secret: str, robot_code: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.robot_code = robot_code
        self.access_token = None
        self._get_access_token()

    def _get_access_token(self):
        """获取 AccessToken（新版接口）"""
        url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
        headers = {"Content-Type": "application/json"}
        data = {"appKey": self.app_key, "appSecret": self.app_secret}

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            result = resp.json()

            if "accessToken" in result:
                self.access_token = result["accessToken"]
                logger.info("[钉钉] AccessToken获取成功，有效期7200秒")
            else:
                logger.error(f"[钉钉] 获取Token失败: {result}")
                raise Exception("Failed to get access token")
        except Exception as e:
            logger.error(f"[钉钉] 获取Token异常: {e}")
            raise

    def send_markdown_message(
        self, open_conversation_id: str, title: str, text: str
    ) -> bool:
        """
        发送Markdown消息到群

        Args:
            open_conversation_id: 群的openConversationId（cid开头）
            title: 消息标题
            text: Markdown格式的消息内容

        Returns:
            bool: 是否发送成功
        """
        url = "https://api.dingtalk.com/v1.0/robot/groupMessages/send"

        headers = {
            "x-acs-dingtalk-access-token": self.access_token,
            "Content-Type": "application/json",
        }

        payload = {
            "robotCode": self.robot_code,
            "openConversationId": open_conversation_id,
            "msgKey": "sampleMarkdown",
            "msgParam": json.dumps(
                {
                    "title": title,
                    "text": text,
                    "single_title": "查看更多",
                    "single_url": "https://www.dingtalk.com",
                },
                ensure_ascii=False,
            ),
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            result = resp.json()

            if "processQueryKey" in result:
                logger.info(
                    f"[钉钉] 消息发送成功，QueryKey: {result['processQueryKey']}"
                )
                return True
            else:
                error_code = result.get("code", "unknown")
                error_msg = result.get("message", "未知错误")
                logger.error(f"[钉钉] 发送消息失败: {error_code} - {error_msg}")

                # Token过期，尝试刷新一次
                if error_code == "InvalidAuthentication":
                    logger.info("[钉钉] Token可能过期，尝试刷新...")
                    self._get_access_token()
                    # 重试一次
                    headers["x-acs-dingtalk-access-token"] = self.access_token
                    resp = requests.post(url, headers=headers, json=payload, timeout=10)
                    result = resp.json()
                    if "processQueryKey" in result:
                        logger.info("[钉钉] 重试发送成功")
                        return True
                return False

        except Exception as e:
            logger.error(f"[钉钉] 发送消息异常: {e}")
            return False


def get_weather_forecast() -> dict:
    """
    获取马尼拉7天天气预报
    返回包含日期、天气代码、温度、降雨、风速的字典
    """
    try:
        params = {
            "latitude": MANILA_LAT,
            "longitude": MANILA_LON,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "forecast_days": 7,
            "timezone": "Asia/Manila",
        }

        logger.info("正在获取马尼拉天气数据...")
        response = requests.get(WEATHER_API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        weather_codes = daily.get("weather_code", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        precipitation = daily.get("precipitation_sum", [])
        windspeed = daily.get("windspeed_10m_max", [])

        forecast = []
        for i in range(len(dates)):
            date_obj = datetime.strptime(dates[i], "%Y-%m-%d")
            weekday = WEEKDAY_MAP[date_obj.weekday()]

            weather_code = weather_codes[i] if i < len(weather_codes) else 0
            weather_desc = WEATHER_CODE_MAP.get(weather_code, "🌡️ 未知")

            forecast.append(
                {
                    "date": dates[i],
                    "date_short": dates[i][5:].replace("-", "/"),  # MM/DD格式
                    "weekday": weekday,
                    "weather_code": weather_code,
                    "weather": weather_desc,
                    "temp_max": temp_max[i] if i < len(temp_max) else None,
                    "temp_min": temp_min[i] if i < len(temp_min) else None,
                    "precipitation": precipitation[i] if i < len(precipitation) else 0,
                    "windspeed": windspeed[i] if i < len(windspeed) else 0,
                }
            )

        logger.info(f"成功获取{len(forecast)}天天气预报")
        return {"forecast": forecast, "success": True}

    except Exception as e:
        logger.error(f"获取天气数据失败: {e}")
        return {"forecast": [], "success": False, "error": str(e)}


def get_exchange_rate() -> dict:
    """
    获取人民币对菲律宾比索汇率
    使用Juhe.cn汇率API
    """
    api_key = os.getenv("JUHE_API_KEY")
    if not api_key:
        logger.error("未配置JUHE_API_KEY环境变量")
        return {"rate": None, "success": False, "error": "未配置API密钥"}

    try:
        params = {"key": api_key, "from": "CNY", "to": "PHP", "version": 2}

        logger.info("正在获取汇率数据...")
        response = requests.get(EXCHANGE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("error_code") == 0:
            result = data.get("result", [])
            if result and len(result) > 0:
                rate = result[0].get("exchange")
                update_time = result[0].get("updateTime", "")
                logger.info(f"成功获取汇率: 1 CNY = {rate} PHP")
                return {"rate": rate, "update_time": update_time, "success": True}
            else:
                return {"rate": None, "success": False, "error": "汇率数据为空"}
        else:
            error_msg = data.get("reason", "未知错误")
            logger.error(f"汇率API错误: {error_msg}")
            return {"rate": None, "success": False, "error": error_msg}

    except Exception as e:
        logger.error(f"获取汇率失败: {e}")
        return {"rate": None, "success": False, "error": str(e)}


def check_extreme_weather(forecast: list) -> list:
    """
    检查极端天气条件
    触发条件: 风速>60km/h 或 日降雨>30mm
    返回预警信息列表
    """
    alerts = []

    for day in forecast:
        windspeed = day.get("windspeed", 0) or 0
        precipitation = day.get("precipitation", 0) or 0
        date_str = day.get("date_short", "")
        weekday = day.get("weekday", "")

        # 风速预警 (>60km/h)
        if windspeed > 60:
            alerts.append(
                f"⚠️ **{date_str} {weekday}**: 风速达{windspeed:.1f}km/h，请注意防风安全"
            )

        # 降雨预警 (>30mm)
        if precipitation > 30:
            alerts.append(
                f"⚠️ **{date_str} {weekday}**: 日降雨量达{precipitation:.1f}mm，请注意防雨"
            )

    return alerts


def build_message(weather_data: dict, exchange_data: dict) -> str:
    """
    构建钉钉消息内容
    简洁清晰的7天预报格式
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # 汇率部分
    if exchange_data.get("success"):
        rate = exchange_data.get("rate", "N/A")
        rate_text = f"1 CNY = {rate} PHP"
    else:
        rate_text = "获取失败"

    # 天气表格（Markdown表格格式）
    forecast = weather_data.get("forecast", [])

    # 表头
    table_header = "| 日期 | 星期 | 天气 | 温度 | 降雨 | 风速 |<br>"
    table_separator = "| ---- | ---- | ---- | ---- | ---- | ---- |<br>"

    table_rows = []
    for day in forecast:
        date_short = day.get("date_short", "")
        weekday = day.get("weekday", "")
        weather = day.get("weather", "")
        temp_max = day.get("temp_max")
        temp_min = day.get("temp_min")
        precipitation = day.get("precipitation", 0) or 0
        windspeed = day.get("windspeed", 0) or 0

        # 格式化温度
        if temp_min is not None and temp_max is not None:
            temp_str = f"{temp_min:.0f}~{temp_max:.0f}℃"
        else:
            temp_str = "N/A"

        # 格式化降雨
        if precipitation == 0:
            rain_str = "无雨"
        else:
            rain_str = f"{precipitation:.0f}mm"

        # 格式化风速
        wind_str = f"{windspeed:.0f}km/h"

        table_rows.append(
            f"| {date_short} | {weekday} | {weather} | {temp_str} | {rain_str} | {wind_str} |<br>"
        )

    weather_table = table_header + table_separator + "".join(table_rows)

    # 检查极端天气
    alerts = check_extreme_weather(forecast)
    alert_section = ""
    if alerts:
        alert_section = f"<br><br>## 🚨 极端天气预警<br><br>{'<br>'.join(alerts)}"

    # 构建完整消息
    message = f"""菲律宾马尼拉 今日简报<br><br>📅 日期：{today}<br>💱 汇率：{rate_text}<br><br>## 📊 7天天气预报<br><br>{weather_table}{alert_section}<br><br><i>*数据来自Open-Meteo和Juhe.cn*</i>"""

    return message


def load_groups() -> list:
    """
    加载群配置
    从groups.json读取群列表
    """
    groups_file = "groups.json"

    if not os.path.exists(groups_file):
        logger.error(f"群配置文件不存在: {groups_file}")
        logger.error("请先运行: python3 get_group_id.py <chat_id>")
        return []

    try:
        with open(groups_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            groups = data.get("groups", [])
            logger.info(f"成功加载{len(groups)}个群配置")
            return groups
    except Exception as e:
        logger.error(f"读取群配置失败: {e}")
        return []


def send_briefing_to_groups(message: str) -> int:
    """
    发送简报到所有配置的群
    返回成功发送的群数量
    """
    # 检查配置
    if not DINGTALK_CLIENT_SECRET:
        logger.error("未配置DINGTALK_CLIENT_SECRET环境变量")
        return 0

    # 初始化钉钉客户端
    try:
        robot = DingTalkRobot(
            app_key=DINGTALK_CLIENT_ID,
            app_secret=DINGTALK_CLIENT_SECRET,
            robot_code=DING_ROBOT_CODE,
        )
    except Exception as e:
        logger.error(f"初始化钉钉机器人失败: {e}")
        return 0

    groups = load_groups()
    if not groups:
        logger.error("没有可用的群配置")
        return 0

    success_count = 0

    for group in groups:
        open_conversation_id = group.get("open_conversation_id")
        chat_id = group.get("chat_id", "未知")
        name = group.get("name", "未命名")

        if not open_conversation_id:
            logger.warning(f"群{name}({chat_id})没有open_conversation_id，跳过")
            continue

        logger.info(f"正在发送简报到群: {name}({chat_id})")

        try:
            result = robot.send_markdown_message(
                open_conversation_id=open_conversation_id,
                title="今日简报",
                text=message,
            )

            if result:
                logger.info(f"✅ 群{name}简报发送成功")
                success_count += 1
            else:
                logger.error(f"❌ 群{name}简报发送失败")

        except Exception as e:
            logger.error(f"❌ 发送到群{name}时出错: {e}")

    return success_count


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("菲律宾每日简报推送开始")
    logger.info("=" * 50)

    # 获取天气数据
    weather_data = get_weather_forecast()

    # 获取汇率数据
    exchange_data = get_exchange_rate()

    # 检查数据获取是否成功
    if not weather_data.get("success") and not exchange_data.get("success"):
        logger.error("天气和汇率数据均获取失败，停止发送")
        return

    # 构建消息
    message = build_message(weather_data, exchange_data)

    # 发送简报
    success_count = send_briefing_to_groups(message)

    logger.info("=" * 50)
    logger.info(f"简报推送完成: {success_count}个群成功")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
