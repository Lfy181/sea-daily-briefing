#!/usr/bin/env python3
"""
钉钉连接和消息发送测试脚本
测试每个国家的钉钉应用配置是否正确
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from bots.base_bot import DingTalkClient, BaseBot, logger
from bots.city_bot import CityBot

# 加载环境变量
load_dotenv()

import logging

# 配置日志输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def test_dingtalk_connection(name: str, client_id: str, client_secret: str, robot_code: str) -> bool:
    """测试钉钉连接"""
    print(f"\n{'='*60}")
    print(f"测试国家: {name}")
    print(f"{'='*60}")
    print(f"Client ID: {client_id[:10]}...")
    print(f"Robot Code: {robot_code}")

    try:
        client = DingTalkClient(
            app_key=client_id,
            app_secret=client_secret,
            robot_code=robot_code,
        )
        print(f"✅ {name} - 钉钉连接成功!")
        return True, client
    except Exception as e:
        print(f"❌ {name} - 钉钉连接失败: {e}")
        return False, None


def test_send_message(client: DingTalkClient, open_conversation_id: str, country_name: str) -> bool:
    """测试发送消息"""
    title = f"{country_name} 简报测试"
    text = f"""## {country_name} 机器人测试消息

📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

这是一条测试消息，用于验证 {country_name} 机器人配置是否正确。

如果看到此消息，说明：
- ✅ 钉钉应用配置正确
- ✅ 机器人已添加到群组
- ✅ 消息发送权限正常

---
*此消息由测试脚本自动发送*
"""

    try:
        result = client.send_markdown_message(
            open_conversation_id=open_conversation_id,
            title=title,
            text=text,
        )
        if result:
            print(f"✅ 消息发送成功!")
            return True
        else:
            print(f"❌ 消息发送失败")
            return False
    except Exception as e:
        print(f"❌ 消息发送异常: {e}")
        return False


def main():
    print("=" * 60)
    print("钉钉配置测试工具")
    print("=" * 60)

    # 读取配置
    with open("config/bots.json", "r", encoding="utf-8") as f:
        bots_config = json.load(f)

    with open("groups.json", "r", encoding="utf-8") as f:
        groups_config = json.load(f)

    # 获取群的 open_conversation_id
    groups = groups_config.get("groups", [])
    if not groups:
        print("❌ 未配置群组")
        return

    open_conversation_id = groups[0].get("open_conversation_id")
    group_name = groups[0].get("name", "未命名")

    print(f"\n目标群组: {group_name}")
    print(f"open_conversation_id: {open_conversation_id}")

    # 测试每个国家
    results = []
    for bot_config in bots_config.get("bots", []):
        country = bot_config.get("country", "Unknown")
        name = bot_config.get("name", country)
        dingtalk = bot_config.get("dingtalk", {})

        client_id = dingtalk.get("client_id", "")
        client_secret = dingtalk.get("client_secret", "")
        robot_code = dingtalk.get("robot_code", client_id)

        if not client_id or not client_secret:
            print(f"⚠️ {name} - 未配置钉钉凭证，跳过")
            continue

        # 测试连接
        success, client = test_dingtalk_connection(name, client_id, client_secret, robot_code)

        if success and client:
            # 自动发送测试消息
            print(f"\n正在发送测试消息...")
            send_success = test_send_message(client, open_conversation_id, country)
            results.append({
                "country": country,
                "name": name,
                "connected": True,
                "message_sent": send_success
            })
        else:
            results.append({
                "country": country,
                "name": name,
                "connected": False,
                "message_sent": False
            })

    # 打印测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)

    for r in results:
        status = "✅" if r["connected"] else "❌"
        msg_status = "✅ 已发送" if r["message_sent"] else "⏭️ 未发送"
        print(f"{status} {r['name']}: 连接{'成功' if r['connected'] else '失败'}, {msg_status}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
