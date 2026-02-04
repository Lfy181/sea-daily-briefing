#!/usr/bin/env python3
"""
东南亚四国每日要闻与生活指数推送助手
每日自动抓取菲律宾、印度尼西亚、越南、马来西亚的天气、汇率、新闻数据
并推送至钉钉群机器人
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 四国配置
COUNTRIES = {
    "ph": {
        "name": "菲律宾",
        "lat": 14.6,
        "lon": 120.9,
        "news_code": "ph",
        "currency": "PHP",
    },
    "id": {
        "name": "印度尼西亚",
        "lat": -6.2,
        "lon": 106.8,
        "news_code": "id",
        "currency": "IDR",
    },
    "vn": {
        "name": "越南",
        "lat": 21.0,
        "lon": 105.8,
        "news_code": "vi",
        "currency": "VND",
    },
    "my": {
        "name": "马来西亚",
        "lat": 3.1,
        "lon": 101.7,
        "news_code": "my",
        "currency": "MYR",
    },
}

# API 配置
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
EXCHANGE_API_URL = "http://op.juhe.cn/onebox/exchange/currency"
NEWS_API_URL = "https://newsdata.io/api/1/news"


def get_weather(lat: float, lon: float) -> dict:
    """获取天气数据"""
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max",
            "timezone": "auto",
        }
        response = requests.get(WEATHER_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        daily = data.get("daily", {})
        return {
            "temp_max": daily.get("temperature_2m_max", [None])[0],
            "temp_min": daily.get("temperature_2m_min", [None])[0],
            "precipitation": daily.get("precipitation_sum", [None])[0],
            "windspeed": daily.get("windspeed_10m_max", [None])[0],
        }
    except Exception as e:
        print(f"获取天气失败: {e}")
        return None


def get_exchange_rate(currency: str) -> str:
    """获取汇率数据 (CNY -> 目标货币)"""
    api_key = os.getenv("JUHE_API_KEY")
    if not api_key:
        print("未配置 JUHE_API_KEY")
        return None

    try:
        params = {
            "key": api_key,
            "from": "CNY",
            "to": currency,
            "version": 2,
        }
        response = requests.get(EXCHANGE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("error_code") == 0:
            result = data.get("result", [])
            # 聚合数据返回的是列表，第一个元素是 CNY->目标货币
            if result and len(result) > 0:
                rate = result[0].get("exchange")
                return rate
            return None
        else:
            print(f"汇率 API 错误: {data.get('reason', '未知错误')}")
            return None
    except Exception as e:
        print(f"获取汇率失败: {e}")
        return None


def get_news(country_code: str) -> list:
    """获取新闻列表 (Top 3)"""
    api_key = os.getenv("NEWSDATA_API_KEY")
    if not api_key:
        print("未配置 NEWSDATA_API_KEY")
        return []

    try:
        params = {
            "apikey": api_key,
            "country": country_code,
            "language": "zh",
        }
        response = requests.get(NEWS_API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            results = data.get("results", [])[:3]
            news_list = []
            for item in results:
                title = item.get("title", "无标题")
                link = item.get("link", "#")
                news_list.append({"title": title, "link": link})
            return news_list
        else:
            print(f"新闻 API 错误: {data.get('results', {}).get('message', '未知错误')}")
            return []
    except Exception as e:
        print(f"获取新闻失败: {e}")
        return []


def generate_weather_tip(weather: dict) -> str:
    """根据天气生成建议"""
    if not weather:
        return "暂无天气提示。"

    tips = []
    precipitation = weather.get("precipitation")
    windspeed = weather.get("windspeed")
    temp_max = weather.get("temp_max")

    # 降水预警
    if precipitation is not None and precipitation > 30:
        tips.append("⚠️ 今日降水较大，请注意防雨并避免外出")
    elif precipitation is not None and precipitation > 10:
        tips.append("🌧️ 今日有雨，出门请带伞")

    # 风速预警
    if windspeed is not None and windspeed > 40:
        tips.append("⚠️ 今日风力较大，请注意安全")
    elif windspeed is not None and windspeed > 25:
        tips.append("🌬️ 今日风力较强，外出注意防风")

    # 高温提示
    if temp_max is not None and temp_max > 35:
        tips.append("🌡️ 今日高温，请注意防暑降温")

    # 默认提示
    if not tips:
        if precipitation is not None and precipitation < 5:
            tips.append("今日天气晴好，适合外出活动。")
        else:
            tips.append("请根据实际天气情况安排出行。")

    return " ".join(tips)


def build_message(country_name: str, weather: dict, rate: str, news: list, currency: str) -> str:
    """构建钉钉消息内容"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 天气部分
    if weather:
        temp_min = weather.get("temp_min", "N/A")
        temp_max = weather.get("temp_max", "N/A")
        windspeed = weather.get("windspeed", "N/A")
        precipitation = weather.get("precipitation", "N/A")
        weather_text = f"{temp_min}℃ ~ {temp_max}℃ | 🌬️ 风速: {windspeed}km/h | 🌧️ 降水: {precipitation}mm"
    else:
        weather_text = "获取失败"

    # 汇率部分
    if rate:
        rate_text = f"1 人民币(CNY) = {rate} {currency}"
    else:
        rate_text = "获取失败"

    # 新闻部分
    if news:
        news_lines = []
        for i, item in enumerate(news, 1):
            news_lines.append(f"{i}. [{item['title']}]({item['link']})")
        news_text = "\n".join(news_lines)
    else:
        news_text = "暂无中文新闻"

    # 天气提示
    tip = generate_weather_tip(weather)

    # 构建完整消息
    message = f"""### 📍 {country_name} 今日简报

---

📅 **日期**: {today}

🌡️ **天气**: {weather_text}

💰 **汇率**: {rate_text}

📰 **当地要闻**:

{news_text}

---

*温馨提示：{tip}*"""

    return message


def send_to_dingtalk(webhook: str, message: str, country_name: str) -> bool:
    """发送消息到钉钉群"""
    if not webhook:
        print("未配置 DINGTALK_WEBHOOK")
        return False

    try:
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"{country_name} 今日简报",
                "text": message,
            },
        }
        response = requests.post(webhook, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get("errcode") == 0:
            print(f"✅ {country_name} 简报发送成功")
            return True
        else:
            print(f"❌ {country_name} 简报发送失败: {result.get('errmsg', '未知错误')}")
            return False
    except Exception as e:
        print(f"❌ 发送钉钉消息失败: {e}")
        return False


def main():
    """主函数：遍历四国并发送简报"""
    print("=" * 50)
    print("东南亚四国每日要闻推送开始")
    print("=" * 50)

    webhook = os.getenv("DINGTALK_WEBHOOK")
    if not webhook:
        print("错误: 未配置 DINGTALK_WEBHOOK 环境变量")
        return

    success_count = 0
    for code, config in COUNTRIES.items():
        country_name = config["name"]
        print(f"\n正在处理: {country_name}")

        # 获取天气
        weather = get_weather(config["lat"], config["lon"])
        print(f"  - 天气: {'成功' if weather else '失败'}")

        # 获取汇率
        rate = get_exchange_rate(config["currency"])
        print(f"  - 汇率: {'成功' if rate else '失败'}")

        # 获取新闻
        news = get_news(config["news_code"])
        print(f"  - 新闻: 获取到 {len(news)} 条")

        # 构建消息
        message = build_message(country_name, weather, rate, news, config["currency"])

        # 发送到钉钉
        if send_to_dingtalk(webhook, message, country_name):
            success_count += 1

    print("\n" + "=" * 50)
    print(f"推送完成: {success_count}/4 个国家成功")
    print("=" * 50)


if __name__ == "__main__":
    main()
