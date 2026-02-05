#!/usr/bin/env python3
"""
群ID查询工具（一次性运行）
根据chatId（群号）获取open_conversation_id并保存到groups.json

使用方法:
    python3 get_group_id.py <chat_id>

示例:
    python3 get_group_id.py 161775015441
"""

import sys
import json
import os
from dingtalk_client import DingTalkClient

# 配置文件路径
GROUPS_FILE = "groups.json"


def load_groups() -> dict:
    """加载现有群配置"""
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] 读取{GROUPS_FILE}失败: {e}")
    return {"groups": []}


def save_groups(groups: dict):
    """保存群配置到文件"""
    try:
        with open(GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(groups, f, ensure_ascii=False, indent=2)
        print(f"[SUCCESS] 配置已保存到 {GROUPS_FILE}")
    except Exception as e:
        print(f"[ERROR] 保存配置失败: {e}")


def get_group_name() -> str:
    """获取群名称（可选）"""
    try:
        name = input("请输入群名称（可选，直接回车跳过）: ").strip()
        return name if name else "未命名"
    except KeyboardInterrupt:
        return "未命名"


def main():
    """主函数"""
    # 检查参数
    if len(sys.argv) < 2:
        print("用法: python3 get_group_id.py <chat_id>")
        print("示例: python3 get_group_id.py 161775015441")
        sys.exit(1)

    chat_id = sys.argv[1]
    print(f"[INFO] 正在查询群 {chat_id} 的 open_conversation_id...")

    try:
        # 初始化钉钉客户端
        client = DingTalkClient()

        # 查询open_conversation_id
        open_conversation_id = client.get_open_conversation_id_by_chat_id(chat_id)

        if open_conversation_id:
            # 获取群名称
            group_name = get_group_name()

            # 加载现有配置
            groups = load_groups()

            # 检查是否已存在
            existing = False
            for group in groups["groups"]:
                if group["chat_id"] == chat_id:
                    group["open_conversation_id"] = open_conversation_id
                    group["name"] = group_name
                    existing = True
                    print(f"[INFO] 更新已有群配置: {chat_id}")
                    break

            # 添加新群
            if not existing:
                groups["groups"].append(
                    {
                        "chat_id": chat_id,
                        "open_conversation_id": open_conversation_id,
                        "name": group_name,
                    }
                )
                print(f"[INFO] 添加新群配置: {chat_id}")

            # 保存配置
            save_groups(groups)

            print("\n[RESULT]")
            print(f"  chat_id: {chat_id}")
            print(f"  open_conversation_id: {open_conversation_id}")
            print(f"  name: {group_name}")
            print("\n[SUCCESS] 现在可以在main.py中使用此群配置发送简报。")
        else:
            print("[ERROR] 无法获取open_conversation_id，请检查:")
            print("  1. 机器人是否已加入该群")
            print("  2. chat_id是否正确")
            print("  3. 钉钉应用权限是否已开通")
            sys.exit(1)

    except ValueError as e:
        print(f"[ERROR] 配置错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
