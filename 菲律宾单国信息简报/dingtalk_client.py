#!/usr/bin/env python3
"""
钉钉API客户端封装
提供AccessToken管理和群消息发送功能
"""

import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 钉钉API配置
DINGTALK_API_URL = "https://api.dingtalk.com"


class DingTalkClient:
    """钉钉API客户端"""

    def __init__(self):
        self.client_id = os.getenv("DINGTALK_CLIENT_ID")
        self.client_secret = os.getenv("DINGTALK_CLIENT_SECRET")
        self.access_token = None
        self.token_expire_time = 0

        if not self.client_id or not self.client_secret:
            raise ValueError("未配置 DINGTALK_CLIENT_ID 或 DINGTALK_CLIENT_SECRET")

    def get_access_token(self) -> str | None:
        """
        获取并缓存AccessToken（2小时有效期）
        使用钉钉企业内部应用获取access_token
        """
        # 检查缓存的token是否有效
        current_time = time.time()
        if self.access_token and current_time < self.token_expire_time:
            return self.access_token

        try:
            url = f"{DINGTALK_API_URL}/v1.0/oauth2/accessToken"
            payload = {"appKey": self.client_id, "appSecret": self.client_secret}
            headers = {"Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "accessToken" in data:
                self.access_token = data["accessToken"]
                expires_in = data.get("expireIn", 7200)
                self.token_expire_time = current_time + expires_in - 300
                print(f"[INFO] [钉钉] AccessToken获取成功，有效期{expires_in}秒")
                return self.access_token
            else:
                error_msg = data.get("errmsg", "未知错误")
                print(f"[ERROR] [钉钉] 获取AccessToken失败: {error_msg}")
                return None

        except Exception as e:
            print(f"[ERROR] [钉钉] 获取AccessToken异常: {e}")
            return None

    def get_open_conversation_id_by_chat_id(self, chat_id: str) -> str | None:
        """
        根据chatId（群号）查询open_conversation_id
        使用钉钉群会话信息查询接口
        """
        access_token = self.get_access_token()
        if not access_token:
            return None

        try:
            # 使用钉钉新版API查询群信息
            url = f"{DINGTALK_API_URL}/v1.0/im/interconnections/chatIds/{chat_id}/openConversations"
            headers = {"x-acs-dingtalk-access-token": access_token}

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "openConversationId" in data:
                open_conversation_id = data["openConversationId"]
                print(
                    f"[INFO] [钉钉] 群{chat_id}的open_conversation_id: {open_conversation_id}"
                )
                return open_conversation_id
            else:
                error_msg = data.get("errmsg", "未知错误")
                print(f"[ERROR] [钉钉] 查询群ID失败: {error_msg}")
                return None

        except Exception as e:
            print(f"[ERROR] [钉钉] 查询群ID异常: {e}")
            return None

        except Exception as e:
            print(f"[钉钉] 查询群ID异常: {e}")
            return None

    def send_markdown_message(
        self, open_conversation_id: str, title: str, text: str
    ) -> bool:
        """
        发送Markdown消息到群
        使用钉钉工作通知消息发送接口（支持Markdown格式）
        """
        access_token = self.get_access_token()
        if not access_token:
            return False

        try:
            # 方案1: 使用新版IM群消息发送接口
            url = f"{DINGTALK_API_URL}/v1.0/im/chat/messages/send"
            headers = {
                "x-acs-dingtalk-access-token": access_token,
                "Content-Type": "application/json",
            }

            # 构造Markdown消息
            payload = {
                "openConversationId": open_conversation_id,
                "msgKey": "sampleMarkdown",
                "msgParam": json.dumps(
                    {"title": title, "markdown": text, "text": text}, ensure_ascii=False
                ),
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # 检查返回结果
            if "processQueryKey" in data:
                print(
                    f"[INFO] [钉钉] 消息发送成功，processQueryKey: {data['processQueryKey']}"
                )
                return True
            elif response.status_code == 200 and "errcode" not in data:
                print(f"[INFO] [钉钉] 消息发送成功")
                return True
            else:
                error_msg = data.get("errmsg", data.get("message", "未知错误"))
                print(f"[ERROR] [钉钉] 消息发送失败: {error_msg}")
                print(
                    f"[DEBUG] [钉钉] 完整响应: {json.dumps(data, ensure_ascii=False)}"
                )
                return False

        except requests.exceptions.HTTPError as e:
            # 处理HTTP错误，打印详细响应
            try:
                error_data = e.response.json()
                print(f"[ERROR] [钉钉] HTTP错误: {e.response.status_code}")
                print(
                    f"[DEBUG] [钉钉] 错误详情: {json.dumps(error_data, ensure_ascii=False)}"
                )
            except:
                print(f"[ERROR] [钉钉] 发送消息HTTP异常: {e}")
                print(
                    f"[DEBUG] [钉钉] 响应内容: {e.response.text if e.response else '无'}"
                )
            return False
        except Exception as e:
            print(f"[ERROR] [钉钉] 发送消息异常: {e}")
            return False

        except requests.exceptions.HTTPError as e:
            # 处理HTTP错误，打印详细响应
            try:
                error_data = e.response.json()
                print(f"[钉钉] HTTP错误: {e.response.status_code}")
                print(f"[钉钉] 错误详情: {json.dumps(error_data, ensure_ascii=False)}")
            except:
                print(f"[钉钉] 发送消息HTTP异常: {e}")
                print(f"[钉钉] 响应内容: {e.response.text if e.response else '无'}")
            return False
        except Exception as e:
            print(f"[钉钉] 发送消息异常: {e}")
            return False


# 便捷函数接口
def get_client() -> DingTalkClient:
    """获取钉钉客户端实例"""
    return DingTalkClient()


def send_message_to_group(open_conversation_id: str, title: str, text: str) -> bool:
    """发送消息到指定群"""
    client = get_client()
    return client.send_markdown_message(open_conversation_id, title, text)
