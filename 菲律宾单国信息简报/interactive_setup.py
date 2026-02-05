#!/usr/bin/env python3
"""
交互式群配置工具
支持两种方式获取群open_conversation_id:
1. 使用已有 access_token 和 chat_id 从钉钉API获取
2. 直接粘贴从钉钉开放平台调试工具复制的完整群信息JSON

使用方法:
  方式一: python interactive_setup.py --token <access_token> --chat-id <chat_id>
  方式二: python interactive_setup.py --interactive

钉钉开放平台调试工具:
  https://open.dingtalk.com/tools/explorer/jsapi?id=11654
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict


def print_banner():
    """打印欢迎信息"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           钉钉群配置工具 - 交互式设置                        ║
║                                                              ║
║  本工具用于获取群的 open_conversation_id 并保存到 groups.json ║
╚══════════════════════════════════════════════════════════════╝
""")


def get_open_conversation_id(access_token: str, chat_id: str) -> Optional[str]:
    """
    通过钉钉API获取群的open_conversation_id

    Args:
        access_token: 钉钉访问令牌
        chat_id: 群ID

    Returns:
        Optional[str]: open_conversation_id，失败返回None
    """
    url = "https://oapi.dingtalk.com/chat/get"
    params = {
        "access_token": access_token,
        "chatid": chat_id
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("errcode") == 0:
            # 尝试从响应中获取open_conversation_id
            chat_info = data.get("chat_info", {})
            open_conversation_id = chat_info.get("open_conversation_id")

            if open_conversation_id:
                return open_conversation_id
            else:
                print("⚠️  警告: API响应中未找到open_conversation_id")
                print(f"响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return None
        else:
            print(f"❌ API调用失败: {data.get('errmsg', '未知错误')}")
            return None

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def interactive_mode():
    """交互式模式 - 引导用户完成配置"""
    print_banner()

    print("请选择配置方式:")
    print("  1. 使用钉钉开放平台调试工具获取的JSON数据")
    print("  2. 手动输入 access_token 和 chat_id")
    print()

    choice = input("请输入选项 (1/2): ").strip()

    if choice == "1":
        return interactive_json_mode()
    elif choice == "2":
        return interactive_token_mode()
    else:
        print("❌ 无效选项")
        return False


def interactive_json_mode() -> bool:
    """
    交互式JSON模式
    用户粘贴从钉钉调试工具复制的完整JSON
    """
    print("\n📋 方式一: 粘贴JSON数据")
    print("-" * 50)
    print("请访问: https://open.dingtalk.com/tools/explorer/jsapi?id=11654")
    print("1. 扫码登录获取 AccessToken")
    print("2. 调用 '查询群信息' API")
    print("3. 复制完整的响应JSON")
    print("-" * 50)
    print("请粘贴JSON数据 (输入空行结束):")

    lines = []
    while True:
        try:
            line = input()
            if not line.strip():
                break
            lines.append(line)
        except EOFError:
            break

    json_str = "\n".join(lines)

    if not json_str.strip():
        print("❌ 未输入任何数据")
        return False

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        return False

    # 尝试从JSON中提取信息
    chat_info = None

    # 钉钉API响应格式
    if "chat_info" in data:
        chat_info = data.get("chat_info", {})
    # 直接是chat_info对象
    elif "chatid" in data or "open_conversation_id" in data:
        chat_info = data
    # 在result字段中
    elif "result" in data:
        result = data.get("result", {})
        if isinstance(result, dict):
            chat_info = result

    if not chat_info:
        print("❌ 无法从JSON中解析群信息")
        print(f"响应结构: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        return False

    # 提取信息
    chat_id = chat_info.get("chatid", "")
    open_conversation_id = chat_info.get("open_conversation_id", "")
    name = chat_info.get("name", "未命名群组")
    owner = chat_info.get("owner", "")

    print(f"\n✅ 解析成功!")
    print(f"  群名称: {name}")
    print(f"  Chat ID: {chat_id}")
    print(f"  Open Conversation ID: {open_conversation_id}")
    if owner:
        print(f"  群主: {owner}")

    if not open_conversation_id:
        print("\n⚠️  警告: 未找到 open_conversation_id")
        print("请确认您使用的是新版钉钉API，或尝试方式二")
        return False

    # 保存配置
    return save_group_config(name, chat_id, open_conversation_id)


def interactive_token_mode() -> bool:
    """
    交互式Token模式
    用户输入access_token和chat_id
    """
    print("\n🔑 方式二: 使用Access Token")
    print("-" * 50)
    print("请访问: https://open.dingtalk.com/tools/explorer/jsapi?id=11654")
    print("1. 扫码登录获取 AccessToken")
    print("2. 获取您要配置的群的 chatId")
    print("-" * 50)

    access_token = input("请输入 AccessToken: ").strip()
    chat_id = input("请输入 Chat ID: ").strip()
    group_name = input("请输入群名称 (可选): ").strip()

    if not access_token or not chat_id:
        print("❌ AccessToken 和 Chat ID 不能为空")
        return False

    print(f"\n正在获取群信息...")

    # 调用API获取open_conversation_id
    open_conversation_id = get_open_conversation_id(access_token, chat_id)

    if not open_conversation_id:
        print("❌ 获取 open_conversation_id 失败")
        print("\n备选方案:")
        print("请使用方式一，直接从钉钉调试工具复制完整的JSON响应")
        return False

    # 如果没有提供群名称，尝试获取
    if not group_name:
        group_name = f"群组_{chat_id[:8]}"

    print(f"\n✅ 获取成功!")
    print(f"  Chat ID: {chat_id}")
    print(f"  Open Conversation ID: {open_conversation_id}")

    # 保存配置
    return save_group_config(group_name, chat_id, open_conversation_id)


def save_group_config(name: str, chat_id: str, open_conversation_id: str) -> bool:
    """
    保存群配置到groups.json

    Args:
        name: 群名称
        chat_id: 群ID
        open_conversation_id: 开放会话ID

    Returns:
        bool: 是否保存成功
    """
    groups_file = "groups.json"

    # 读取现有配置
    groups = []
    if os.path.exists(groups_file):
        try:
            with open(groups_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                groups = data.get("groups", [])
        except Exception as e:
            print(f"⚠️  读取现有配置失败: {e}，将创建新文件")
            groups = []

    # 检查是否已存在
    existing = None
    for i, group in enumerate(groups):
        if group.get("chat_id") == chat_id:
            existing = i
            break

    # 构建新配置
    new_group = {
        "name": name,
        "chat_id": chat_id,
        "open_conversation_id": open_conversation_id
    }

    if existing is not None:
        # 更新现有配置
        groups[existing] = new_group
        action = "更新"
    else:
        # 添加新配置
        groups.append(new_group)
        action = "添加"

    # 保存文件
    try:
        with open(groups_file, "w", encoding="utf-8") as f:
            json.dump({"groups": groups}, f, ensure_ascii=False, indent=2)

        print(f"\n✅ {action}成功!")
        print(f"配置已保存到: {groups_file}")
        print(f"\n当前配置的群组 ({len(groups)}个):")
        for i, group in enumerate(groups, 1):
            print(f"  {i}. {group.get('name', '未命名')} ({group.get('chat_id', 'N/A')})")

        return True

    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        return False


def show_groups():
    """显示当前配置的所有群组"""
    groups_file = "groups.json"

    if not os.path.exists(groups_file):
        print("❌ 配置文件不存在，请先添加群组")
        return

    try:
        with open(groups_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            groups = data.get("groups", [])

        if not groups:
            print("当前没有配置任何群组")
            return

        print(f"\n已配置的群组 ({len(groups)}个):")
        print("-" * 60)
        print(f"{'序号':<6} {'群名称':<20} {'Chat ID':<20}")
        print("-" * 60)

        for i, group in enumerate(groups, 1):
            name = group.get('name', '未命名')
            chat_id = group.get('chat_id', 'N/A')
            print(f"{i:<6} {name:<20} {chat_id:<20}")

        print("-" * 60)

    except Exception as e:
        print(f"❌ 读取配置失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="钉钉群配置工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python interactive_setup.py                    # 交互式模式
  python interactive_setup.py --list             # 列出所有群组
  python interactive_setup.py --token xxx --chat-id xxx
        """
    )

    parser.add_argument(
        "--token", "-t",
        type=str,
        help="钉钉AccessToken"
    )

    parser.add_argument(
        "--chat-id", "-c",
        type=str,
        help="群Chat ID"
    )

    parser.add_argument(
        "--name", "-n",
        type=str,
        default="简报信息",
        help="群名称（默认: 简报信息）"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有已配置的群组"
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="强制使用交互式模式"
    )

    args = parser.parse_args()

    if args.list:
        show_groups()
        return

    if args.token and args.chat_id:
        # 命令行模式
        print(f"正在获取群信息...")
        open_conversation_id = get_open_conversation_id(args.token, args.chat_id)

        if open_conversation_id:
            save_group_config(args.name, args.chat_id, open_conversation_id)
        else:
            print("❌ 获取失败，请检查token和chat_id是否正确")
            sys.exit(1)
    else:
        # 交互式模式
        interactive_mode()


if __name__ == "__main__":
    main()
