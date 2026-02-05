#!/usr/bin/env python3
"""
城市简报机器人实现类
提供标准的消息构建模板
"""

from datetime import datetime
from typing import Dict
from .base_bot import BaseBot, logger


class CityBot(BaseBot):
    """
    标准城市简报机器人
    使用统一的消息模板格式
    """

    def build_message(self, weather_data: Dict, exchange_data: Dict) -> str:
        """
        构建钉钉消息内容
        简洁清晰的7天预报格式，使用定性描述
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 汇率部分
        if exchange_data.get("success"):
            rate = exchange_data.get("rate", "N/A")
            from_currency = exchange_data.get("from_currency", "CNY")
            to_currency = exchange_data.get("to_currency", "")
            rate_text = f"1 {from_currency} = {rate} {to_currency}"
        else:
            rate_text = "获取失败"

        # 天气表格（Markdown表格格式）
        forecast = weather_data.get("forecast", [])

        # 表头
        table_header = "| 日期 | 星期 | 天气 | 温度 | 风速 |<br>"
        table_separator = "| ---- | ---- | ---- | ---- | ---- |<br>"

        table_rows = []
        for day in forecast:
            date_short = day.get("date_short", "")
            weekday = day.get("weekday", "")
            weather = day.get("weather", "")
            temp_max = day.get("temp_max")
            temp_min = day.get("temp_min")
            wind_level = day.get("wind_level", "静风")
            wind_icon = day.get("wind_icon", "")

            # 格式化温度
            if temp_min is not None and temp_max is not None:
                temp_str = f"{temp_min:.0f}~{temp_max:.0f}℃"
            else:
                temp_str = "N/A"

            # 格式化风速（定性描述）
            wind_str = f"{wind_icon}{wind_level}"

            table_rows.append(
                f"| {date_short} | {weekday} | {weather} | {temp_str} | {wind_str} |<br>"
            )

        weather_table = table_header + table_separator + "".join(table_rows)

        # 检查极端天气
        alerts = self.check_extreme_weather(forecast)
        alert_section = ""
        if alerts:
            alert_section = f"<br><br>## 🚨 极端天气预警<br><br>{'<br>'.join(alerts)}"

        # 构建完整消息
        message = f"""{self.country}{self.city} 今日简报<br><br>📅 日期：{today}<br>💱 汇率：{rate_text}<br><br>## 📊 7天天气预报<br><br>{weather_table}{alert_section}<br><br><i>*数据来自Open-Meteo和Juhe.cn*</i>"""

        return message
