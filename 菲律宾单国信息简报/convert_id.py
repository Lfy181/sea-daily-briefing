import requests
import json

APP_KEY = "dingqswguvtbhcnprqxc"
APP_SECRET = "O5yH3OpwXm7adFBqpL60QzNUVlb-TFRG7jQHOkyOFg5XgCTvrNZ7YI9MT-kOKZZv"
CHAT_ID = "chat6437e92380126a3932600eb22d9b0671"

# 获取Token
token_resp = requests.post(
    "https://api.dingtalk.com/v1.0/oauth2/accessToken",
    json={"appKey": APP_KEY, "appSecret": APP_SECRET},
)
access_token = token_resp.json()["accessToken"]
print(f"[INFO] Token: {access_token[:20]}...")

# 转换ID
convert_resp = requests.post(
    f"https://api.dingtalk.com/v1.0/im/chat/{CHAT_ID}/convertToOpenConversationId",
    headers={"x-acs-dingtalk-access-token": access_token},
)
result = convert_resp.json()
print(f"\n[INFO] 转换结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

if "openConversationId" in result:
    print(f"\n[SUCCESS] 正确的 openConversationId: {result['openConversationId']}")
    print("[INFO] 请把这个ID替换到你的主程序中！")
