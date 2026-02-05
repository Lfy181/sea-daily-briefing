import requests
import json

# ==================== 配置区域（已更新）====================
APP_KEY = "dingqswguvtbhcnprqxc"
APP_SECRET = "O5yH3OpwXm7adFBqpL60QzNUVlb-TFRG7jQHOkyOFg5XgCTvrNZ7YI9MT-kOKZZv"
ROBOT_CODE = "dingqswguvtbhcnprqxc"
OPEN_CONVERSATION_ID = "cidjqh5//NCDSwyIjzWWCnRWw=="  # 刚获取的正确ID
# =========================================================


def get_access_token():
    """获取 AccessToken"""
    url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
    resp = requests.post(url, json={"appKey": APP_KEY, "appSecret": APP_SECRET})
    return resp.json()["accessToken"]


def send_message(access_token):
    """发送群消息"""
    url = "https://api.dingtalk.com/v1.0/robot/groupMessages/send"

    headers = {
        "x-acs-dingtalk-access-token": access_token,
        "Content-Type": "application/json",
    }

    payload = {
        "robotCode": ROBOT_CODE,
        "openConversationId": OPEN_CONVERSATION_ID,
        "msgKey": "sampleMarkdown",
        "msgParam": json.dumps(
            {
                "title": "🇵🇭 菲律宾每日简报",
                "markdown": "## 🇵🇭 菲律宾每日简报\n\n📅 **日期**: 2026年2月4日 星期三\n\n🌤️ **马尼拉天气**\n- 天气: 多云转晴\n- 温度: 25°C ~ 32°C\n- 湿度: 65%\n\n💱 **汇率信息**\n- 1 CNY = 7.85 PHP\n- 1 USD = 57.20 PHP\n\n📰 **今日要闻**\n- 菲律宾央行维持利率不变\n- 马尼拉股市上涨1.2%\n\n---\n*由 菲每日简报 机器人自动推送*",
                "single_title": "查看更多详情",
                "single_url": "https://www.dingtalk.com",
            },
            ensure_ascii=False,
        ),
    }

    resp = requests.post(url, headers=headers, json=payload)
    result = resp.json()
    print(f"[INFO] [响应] {result}")

    if "processQueryKey" in result:
        print("[SUCCESS] 消息发送成功！请检查钉钉群【简报信息】")
        return True
    else:
        print(f"[ERROR] 发送失败: {result.get('message')}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("[INFO] 钉钉机器人 - 菲律宾简报发送测试")
    print("=" * 60)

    token = get_access_token()
    print(f"[INFO] Token: {token[:20]}...")
    send_message(token)
