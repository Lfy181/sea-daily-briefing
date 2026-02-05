#!/usr/bin/env python3
"""
基础机器人类 - 抽象基类
定义多城市简报机器人的通用接口和共享逻辑
"""

import os
import json
import logging
import requests
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# 汇率历史存储路径
EXCHANGE_HISTORY_FILE = "data/exchange_history.json"

# 汇率波动阈值 (%)
EXCHANGE_RATE_CHANGE_THRESHOLD = 5.0

# 汇率合理范围
EXCHANGE_RATE_MIN = 0.01
EXCHANGE_RATE_MAX = 10000.0

# 配置日志
logger = logging.getLogger(__name__)

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

# 风速等级映射 (km/h, 最小值, 最大值, 描述, 图标)
WIND_LEVEL_MAP = [
    (0, 5, "静风", "🍃"),
    (5, 20, "微风", "🌿"),
    (20, 40, "轻风", "🍃"),
    (40, 60, "和风", "🌾"),
    (60, 80, "强风", "💨"),
    (80, float('inf'), "大风", "🌪️"),
]

# 降雨等级映射 (mm, 最小值, 最大值, 描述)
RAIN_LEVEL_MAP = [
    (0, 0.1, "无雨", ""),
    (0.1, 5, "小雨", "🌦️"),
    (5, 20, "中雨", "🌧️"),
    (20, 50, "大雨", "🌧️"),
    (50, float('inf'), "暴雨", "⛈️"),
]


class DingTalkClient:
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


class BaseBot(ABC):
    """
    简报机器人抽象基类
    所有城市机器人需要继承此类并实现抽象方法
    """

    # API配置
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    EXCHANGE_API_URL = "http://op.juhe.cn/onebox/exchange/currency"

    def __init__(self, config: Dict):
        """
        初始化机器人

        Args:
            config: 机器人配置字典，包含:
                - name: 机器人名称
                - country: 国家代码
                - city: 城市名称
                - latitude: 纬度
                - longitude: 经度
                - currency: 货币代码
                - currency_name: 货币名称
                - target_currency: 目标货币代码（默认CNY）
                - groups: 目标群组列表
                - timezone: 时区（用于天气API）
                - dingtalk: 钉钉应用配置
                    - client_id: Client ID (AppKey)
                    - client_secret: Client Secret
                    - robot_code: Robot Code
        """
        self.name = config.get('name', '简报机器人')
        self.country = config.get('country', '')
        self.city = config.get('city', '')
        self.lat = config.get('latitude', 0)
        self.lon = config.get('longitude', 0)
        self.currency = config.get('currency', '')
        self.currency_name = config.get('currency_name', '')
        self.target_currency = config.get('target_currency', 'CNY')
        self.groups = config.get('groups', [])
        self.timezone = config.get('timezone', 'Asia/Shanghai')

        # 钉钉应用配置
        self.dingtalk_config = config.get('dingtalk', {})

        # 天气API时区（根据城市所在国家调整）
        self.weather_timezone = self._get_weather_timezone()

        logger.info(f"[{self.name}] 初始化完成，城市: {self.city}")

    def _get_weather_timezone(self) -> str:
        """根据国家和城市获取天气API时区"""
        timezone_map = {
            'PH': 'Asia/Manila',
            'VN': 'Asia/Ho_Chi_Minh',
            'ID': 'Asia/Jakarta',
            'MY': 'Asia/Kuala_Lumpur',
        }
        return timezone_map.get(self.country, 'Asia/Shanghai')

    @staticmethod
    def get_wind_level(wind_speed_kmh: float) -> Tuple[str, str]:
        """
        将风速(km/h)转换为定性描述

        Args:
            wind_speed_kmh: 风速，单位km/h

        Returns:
            Tuple[图标, 描述]: 如 ("🍃", "静风")
        """
        for min_speed, max_speed, desc, icon in WIND_LEVEL_MAP:
            if min_speed <= wind_speed_kmh < max_speed:
                return icon, desc
        return "🌪️", "大风"

    @staticmethod
    def get_rain_level(precipitation_mm: float) -> Tuple[str, str]:
        """
        将降雨量(mm)转换为定性描述

        Args:
            precipitation_mm: 降雨量，单位mm

        Returns:
            Tuple[图标, 描述]: 如 ("", "无雨")
        """
        for min_rain, max_rain, desc, icon in RAIN_LEVEL_MAP:
            if min_rain <= precipitation_mm < max_rain:
                return icon, desc
        return "⛈️", "暴雨"

    def get_weather_forecast(self) -> Dict:
        """
        获取7天天气预报
        返回包含日期、天气代码、温度、降雨、风速的字典
        """
        try:
            params = {
                "latitude": self.lat,
                "longitude": self.lon,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
                "forecast_days": 7,
                "timezone": self.weather_timezone,
            }

            logger.info(f"[{self.name}] 正在获取天气数据...")
            response = requests.get(self.WEATHER_API_URL, params=params, timeout=15)
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

                # 获取风速和降雨的定性描述
                wind_speed = windspeed[i] if i < len(windspeed) else 0
                wind_icon, wind_level = self.get_wind_level(wind_speed)

                rain_amount = precipitation[i] if i < len(precipitation) else 0
                rain_icon, rain_level = self.get_rain_level(rain_amount)

                forecast.append(
                    {
                        "date": dates[i],
                        "date_short": dates[i][5:].replace("-", "/"),  # MM/DD格式
                        "weekday": weekday,
                        "weather_code": weather_code,
                        "weather": weather_desc,
                        "temp_max": temp_max[i] if i < len(temp_max) else None,
                        "temp_min": temp_min[i] if i < len(temp_min) else None,
                        "precipitation": rain_amount,
                        "precipitation_level": rain_level,
                        "precipitation_icon": rain_icon,
                        "windspeed": wind_speed,
                        "wind_level": wind_level,
                        "wind_icon": wind_icon,
                    }
                )

            logger.info(f"[{self.name}] 成功获取{len(forecast)}天天气预报")
            return {"forecast": forecast, "success": True}

        except Exception as e:
            logger.error(f"[{self.name}] 获取天气数据失败: {e}")
            return {"forecast": [], "success": False, "error": str(e)}

    def _load_exchange_history(self) -> Dict:
        """加载汇率历史记录"""
        try:
            if os.path.exists(EXCHANGE_HISTORY_FILE):
                with open(EXCHANGE_HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"[{self.name}] 加载汇率历史失败: {e}")
        return {}

    def _save_exchange_history(self, history: Dict):
        """保存汇率历史记录"""
        try:
            os.makedirs(os.path.dirname(EXCHANGE_HISTORY_FILE), exist_ok=True)
            with open(EXCHANGE_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[{self.name}] 保存汇率历史失败: {e}")

    def validate_exchange_rate(
        self, rate: float, history_rate: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        校验汇率是否异常

        Args:
            rate: 当前汇率值
            history_rate: 历史汇率值（用于波动检测）

        Returns:
            Tuple[bool, str]: (是否通过校验, 错误信息)
        """
        # 检查是否为0或负数
        if rate <= 0:
            return False, f"汇率值异常: {rate} (应为正数)"

        # 检查是否为None或无效值
        if rate is None:
            return False, "汇率值为空"

        # 检查是否在合理范围
        if rate < EXCHANGE_RATE_MIN or rate > EXCHANGE_RATE_MAX:
            return False, f"汇率值超出合理范围: {rate} (应在 {EXCHANGE_RATE_MIN} ~ {EXCHANGE_RATE_MAX} 之间)"

        # 检查波动幅度
        if history_rate and history_rate > 0:
            change_pct = abs(rate - history_rate) / history_rate * 100
            if change_pct > EXCHANGE_RATE_CHANGE_THRESHOLD:
                return (
                    False,
                    f"汇率波动过大: {change_pct:.2f}% (从 {history_rate} 到 {rate}, 阈值 {EXCHANGE_RATE_CHANGE_THRESHOLD}%)",
                )

        return True, "正常"

    def send_exchange_alert(self, alert_msg: str, current_rate: float, history_rate: Optional[float] = None):
        """
        发送汇率异常告警

        Args:
            alert_msg: 告警消息
            current_rate: 当前汇率
            history_rate: 历史汇率
        """
        # 钉钉配置（从机器人配置读取）
        app_key = self.dingtalk_config.get("client_id", "")
        app_secret = self.dingtalk_config.get("client_secret", "")
        robot_code = self.dingtalk_config.get("robot_code", app_key)

        # 如果没有配置钉钉凭证，尝试使用环境变量（向后兼容）
        if not app_key:
            app_key = os.getenv("DINGTALK_CLIENT_ID", "")
            app_secret = os.getenv("DINGTALK_CLIENT_SECRET", "")
            robot_code = os.getenv("DING_ROBOT_CODE", app_key)

        if not app_secret:
            logger.error(f"[{self.name}] 无法发送告警: 未配置钉钉Client Secret")
            return

        try:
            client = DingTalkClient(
                app_key=app_key,
                app_secret=app_secret,
                robot_code=robot_code,
            )

            # 构建告警消息
            change_info = ""
            if history_rate and history_rate > 0:
                change_pct = (current_rate - history_rate) / history_rate * 100
                change_info = f"\n\n**波动幅度**: {change_pct:+.2f}%\n**上次汇率**: {history_rate}"

            alert_text = f"""## 🚨 汇率异常告警

**机器人**: {self.name}
**货币对**: {self.target_currency}/{self.currency}
**异常类型**: {alert_msg}
**当前汇率**: {current_rate}{change_info}

**时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

请检查汇率API或联系管理员。
"""

            # 发送到所有配置的群组
            groups = self.load_groups()
            for group in groups:
                open_conversation_id = group.get("open_conversation_id")
                name = group.get("name", "未命名")

                if open_conversation_id:
                    try:
                        client.send_markdown_message(
                            open_conversation_id=open_conversation_id,
                            title=f"汇率异常告警 - {self.currency}",
                            text=alert_text,
                        )
                        logger.info(f"[{self.name}] 汇率告警已发送到群: {name}")
                    except Exception as e:
                        logger.error(f"[{self.name}] 发送告警到群{name}失败: {e}")

        except Exception as e:
            logger.error(f"[{self.name}] 发送汇率告警失败: {e}")

    def get_exchange_rate(self) -> Dict:
        """
        获取汇率数据（带异常监控）
        使用Juhe.cn汇率API

        Returns:
            Dict: 包含汇率信息的字典
        """
        api_key = os.getenv("JUHE_API_KEY")
        if not api_key:
            error_msg = "未配置JUHE_API_KEY环境变量"
            logger.error(f"[{self.name}] {error_msg}")
            return {"rate": None, "success": False, "error": error_msg}

        try:
            params = {
                "key": api_key,
                "from": self.target_currency,
                "to": self.currency,
                "version": 2
            }

            logger.info(f"[{self.name}] 正在获取汇率数据...")
            response = requests.get(self.EXCHANGE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("error_code") == 0:
                result = data.get("result", [])
                if result and len(result) > 0:
                    rate_data = result[0]
                    rate_str = rate_data.get("exchange")
                    update_time = rate_data.get("updateTime", "")

                    # 解析汇率值
                    try:
                        rate = float(rate_str) if rate_str else None
                    except (ValueError, TypeError):
                        error_msg = f"汇率格式无效: {rate_str}"
                        logger.error(f"[{self.name}] {error_msg}")
                        return {"rate": None, "success": False, "error": error_msg}

                    # 加载历史汇率
                    history = self._load_exchange_history()
                    currency_key = f"{self.target_currency}_{self.currency}"
                    history_rate = history.get(currency_key, {}).get("rate")

                    # 校验汇率
                    is_valid, validation_msg = self.validate_exchange_rate(rate, history_rate)

                    if not is_valid:
                        logger.error(f"[{self.name}] 汇率校验失败: {validation_msg}")
                        # 发送告警
                        self.send_exchange_alert(validation_msg, rate, history_rate)
                        return {
                            "rate": rate,
                            "update_time": update_time,
                            "from_currency": self.target_currency,
                            "to_currency": self.currency,
                            "to_currency_name": self.currency_name,
                            "success": False,
                            "error": validation_msg,
                            "alert_sent": True
                        }

                    # 保存当前汇率到历史记录
                    history[currency_key] = {
                        "rate": rate,
                        "timestamp": datetime.now().isoformat(),
                        "update_time": update_time
                    }
                    self._save_exchange_history(history)

                    logger.info(f"[{self.name}] 成功获取汇率: 1 {self.target_currency} = {rate} {self.currency}")
                    return {
                        "rate": rate,
                        "update_time": update_time,
                        "from_currency": self.target_currency,
                        "to_currency": self.currency,
                        "to_currency_name": self.currency_name,
                        "success": True
                    }
                else:
                    error_msg = "汇率数据为空"
                    logger.error(f"[{self.name}] {error_msg}")
                    # 发送告警
                    self.send_exchange_alert("API返回空数据", 0)
                    return {"rate": None, "success": False, "error": error_msg, "alert_sent": True}
            else:
                error_msg = data.get("reason", "未知错误")
                logger.error(f"[{self.name}] 汇率API错误: {error_msg}")
                # 发送告警
                self.send_exchange_alert(f"API错误: {error_msg}", 0)
                return {"rate": None, "success": False, "error": error_msg, "alert_sent": True}

        except requests.exceptions.RequestException as e:
            error_msg = f"API请求失败: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            # 发送告警
            self.send_exchange_alert(f"API调用失败: {e}", 0)
            return {"rate": None, "success": False, "error": error_msg, "alert_sent": True}
        except Exception as e:
            error_msg = f"获取汇率失败: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            # 发送告警
            self.send_exchange_alert(f"系统异常: {e}", 0)
            return {"rate": None, "success": False, "error": error_msg, "alert_sent": True}

    def check_extreme_weather(self, forecast: List[Dict]) -> List[str]:
        """
        检查极端天气条件
        触发条件: 风速>60km/h 或 日降雨>30mm
        返回预警信息列表（保留定量数值）
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

    @abstractmethod
    def build_message(self, weather_data: Dict, exchange_data: Dict) -> str:
        """
        构建钉钉消息内容
        子类可以重写此方法以自定义消息格式

        Args:
            weather_data: 天气数据
            exchange_data: 汇率数据

        Returns:
            str: Markdown格式的消息内容
        """
        pass

    def load_groups(self) -> List[Dict]:
        """
        加载群配置
        从groups.json读取群列表
        """
        groups_file = "groups.json"

        if not os.path.exists(groups_file):
            logger.error(f"群配置文件不存在: {groups_file}")
            return []

        try:
            with open(groups_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_groups = data.get("groups", [])

                # 过滤出本机器人需要发送的群组
                # 支持通过群名称匹配
                filtered_groups = []
                for group in all_groups:
                    group_name = group.get("name", "")
                    if group_name in self.groups:
                        filtered_groups.append(group)

                logger.info(f"[{self.name}] 成功加载{len(filtered_groups)}个目标群配置")
                return filtered_groups
        except Exception as e:
            logger.error(f"[{self.name}] 读取群配置失败: {e}")
            return []

    def send_to_groups(self, message: str) -> int:
        """
        发送消息到所有配置的群

        Args:
            message: 消息内容

        Returns:
            int: 成功发送的群数量
        """
        # 钉钉配置（从机器人配置读取）
        app_key = self.dingtalk_config.get("client_id", "")
        app_secret = self.dingtalk_config.get("client_secret", "")
        robot_code = self.dingtalk_config.get("robot_code", app_key)

        # 如果没有配置钉钉凭证，尝试使用环境变量（向后兼容）
        if not app_key:
            app_key = os.getenv("DINGTALK_CLIENT_ID", "")
            app_secret = os.getenv("DINGTALK_CLIENT_SECRET", "")
            robot_code = os.getenv("DING_ROBOT_CODE", app_key)

        # 检查配置
        if not app_secret:
            logger.error(f"[{self.name}] 未配置钉钉Client Secret")
            return 0

        if not app_key:
            logger.error(f"[{self.name}] 未配置钉钉Client ID")
            return 0

        # 初始化钉钉客户端
        try:
            client = DingTalkClient(
                app_key=app_key,
                app_secret=app_secret,
                robot_code=robot_code,
            )
        except Exception as e:
            logger.error(f"[{self.name}] 初始化钉钉客户端失败: {e}")
            return 0

        groups = self.load_groups()
        if not groups:
            logger.error(f"[{self.name}] 没有可用的群配置")
            return 0

        success_count = 0

        for group in groups:
            open_conversation_id = group.get("open_conversation_id")
            chat_id = group.get("chat_id", "未知")
            name = group.get("name", "未命名")

            if not open_conversation_id:
                logger.warning(f"[{self.name}] 群{name}({chat_id})没有open_conversation_id，跳过")
                continue

            logger.info(f"[{self.name}] 正在发送消息到群: {name}({chat_id})")

            try:
                result = client.send_markdown_message(
                    open_conversation_id=open_conversation_id,
                    title=f"{self.city}今日简报",
                    text=message,
                )

                if result:
                    logger.info(f"[{self.name}] ✅ 群{name}消息发送成功")
                    success_count += 1
                else:
                    logger.error(f"[{self.name}] ❌ 群{name}消息发送失败")

            except Exception as e:
                logger.error(f"[{self.name}] ❌ 发送到群{name}时出错: {e}")

        return success_count

    def run(self) -> bool:
        """
        执行机器人任务

        Returns:
            bool: 是否执行成功
        """
        logger.info(f"[{self.name}] 开始执行简报任务")

        # 获取天气数据
        weather_data = self.get_weather_forecast()

        # 获取汇率数据
        exchange_data = self.get_exchange_rate()

        # 检查数据获取是否成功
        if not weather_data.get("success") and not exchange_data.get("success"):
            logger.error(f"[{self.name}] 天气和汇率数据均获取失败，停止发送")
            return False

        # 构建消息
        message = self.build_message(weather_data, exchange_data)

        # 发送简报
        success_count = self.send_to_groups(message)

        logger.info(f"[{self.name}] 简报推送完成: {success_count}个群成功")

        return success_count > 0
