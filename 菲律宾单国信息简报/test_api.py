import requests
import json

# ==================== 配置区域（已填写完整）====================
APP_KEY = "dingqswguvtbhcnprqxc"
APP_SECRET = "O5yH3OpwXm7adFBqpL60QzNUVlb-TFRG7jQHOkyOFg5XgCTvrNZ7YI9MT-kOKZZv"
ROBOT_CODE = "dingqswguvtbhcnprqxc"
CONVERSATION_ID = "chat6437e92380126a3932600eb22d9b0671"
# =============================================================


def get_access_token():
    """获取 AccessToken（新版接口）"""
    url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
    headers = {"Content-Type": "application/json"}
    data = {"appKey": APP_KEY, "appSecret": APP_SECRET}

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        result = resp.json()
        print(f"[INFO] [获取Token] 成功")
        return result.get("accessToken")
    except Exception as e:
        print(f"[ERROR] 获取Token失败: {e}")
        return None


def send_message(access_token):
    """发送群消息（新版API）"""
    url = "https://api.dingtalk.com/v1.0/robot/groupMessages/send"

    headers = {
        "x-acs-dingtalk-access-token": access_token,
        "Content-Type": "application/json",
    }

    payload = {
        "robotCode": ROBOT_CODE,
        "openConversationId": CONVERSATION_ID,
        "msgKey": "sampleMarkdown",
        "msgParam": json.dumps(
            {
                "title": "菲律宾每日简报",
                "markdown": "## 🇵🇭 菲律宾每日简报\n\n**日期**：2026-02-04\n\n**天气**：马尼拉 晴朗 25-32°C\n\n**汇率**：1 CNY = 7.85 PHP\n\n测试消息，验证机器人正常工作！",
                "single_title": "查看详情",
                "single_url": "https://www.dingtalk.com",
            },
            ensure_ascii=False,
        ),
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        result = resp.json()
        print(f"[INFO] [发送结果] {result}")

        if "processQueryKey" in result:
            print("[SUCCESS] 消息发送成功！请检查钉钉群")
            return True
        else:
            print(f"[ERROR] 发送失败: {result.get('message', '未知错误')}")
            return False

    except Exception as e:
        print(f"[ERROR] 请求异常: {e}")
        return False

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("钉钉机器人最终测试")
    print("=" * 60)

    token = get_access_token()
    if token:
        print(f"Token获取成功: {token[:20]}...")
        send_message(token)
