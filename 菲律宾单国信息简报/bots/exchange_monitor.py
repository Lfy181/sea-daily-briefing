#!/usr/bin/env python3
"""
汇率监控独立模块
提供汇率异常检测、告警和历史记录功能
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_HISTORY_FILE = "data/exchange_history.json"
DEFAULT_CHANGE_THRESHOLD = 5.0  # 5%波动阈值
DEFAULT_RATE_MIN = 0.01
DEFAULT_RATE_MAX = 10000.0


class ExchangeMonitor:
    """
    汇率监控器
    负责汇率数据校验、波动检测和告警
    """

    def __init__(
        self,
        history_file: str = DEFAULT_HISTORY_FILE,
        change_threshold: float = DEFAULT_CHANGE_THRESHOLD,
        rate_min: float = DEFAULT_RATE_MIN,
        rate_max: float = DEFAULT_RATE_MAX,
    ):
        """
        初始化汇率监控器

        Args:
            history_file: 历史汇率存储文件路径
            change_threshold: 波动阈值（百分比）
            rate_min: 汇率最小合理值
            rate_max: 汇率最大合理值
        """
        self.history_file = history_file
        self.change_threshold = change_threshold
        self.rate_min = rate_min
        self.rate_max = rate_max

        # 确保数据目录存在
        os.makedirs(os.path.dirname(history_file), exist_ok=True)

    def _get_currency_key(self, from_currency: str, to_currency: str) -> str:
        """生成货币对的唯一键"""
        return f"{from_currency}_{to_currency}"

    def load_history(self) -> Dict:
        """
        加载汇率历史记录

        Returns:
            Dict: 历史汇率数据字典
        """
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载汇率历史失败: {e}")
        return {}

    def save_history(self, history: Dict):
        """
        保存汇率历史记录

        Args:
            history: 历史汇率数据字典
        """
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存汇率历史失败: {e}")

    def get_last_rate(
        self, from_currency: str, to_currency: str
    ) -> Optional[Dict]:
        """
        获取上次汇率记录

        Args:
            from_currency: 源货币代码
            to_currency: 目标货币代码

        Returns:
            Optional[Dict]: 上次汇率记录，包含rate、timestamp等
        """
        history = self.load_history()
        key = self._get_currency_key(from_currency, to_currency)
        return history.get(key)

    def validate_rate(
        self,
        rate: float,
        from_currency: str,
        to_currency: str,
        check_volatility: bool = True,
    ) -> Tuple[bool, str, Optional[float]]:
        """
        校验汇率是否异常

        Args:
            rate: 当前汇率值
            from_currency: 源货币代码
            to_currency: 目标货币代码
            check_volatility: 是否检查波动幅度

        Returns:
            Tuple[bool, str, Optional[float]]: (是否通过校验, 错误信息, 波动百分比)
        """
        # 检查是否为None
        if rate is None:
            return False, "汇率值为空", None

        # 检查是否为0或负数
        if rate <= 0:
            return False, f"汇率值异常: {rate} (应为正数)", None

        # 检查是否在合理范围
        if rate < self.rate_min or rate > self.rate_max:
            return (
                False,
                f"汇率值超出合理范围: {rate} (应在 {self.rate_min} ~ {self.rate_max} 之间)",
                None,
            )

        # 检查波动幅度
        change_pct = None
        if check_volatility:
            last_record = self.get_last_rate(from_currency, to_currency)
            if last_record:
                last_rate = last_record.get("rate")
                if last_rate and last_rate > 0:
                    change_pct = (rate - last_rate) / last_rate * 100
                    if abs(change_pct) > self.change_threshold:
                        return (
                            False,
                            f"汇率波动过大: {change_pct:+.2f}% (从 {last_rate} 到 {rate}, 阈值 {self.change_threshold}%)",
                            change_pct,
                        )

        return True, "正常", change_pct

    def record_rate(
        self,
        rate: float,
        from_currency: str,
        to_currency: str,
        update_time: str = "",
    ):
        """
        记录当前汇率到历史

        Args:
            rate: 当前汇率值
            from_currency: 源货币代码
            to_currency: 目标货币代码
            update_time: API返回的更新时间
        """
        history = self.load_history()
        key = self._get_currency_key(from_currency, to_currency)

        # 保留最近30天的记录
        history[key] = {
            "rate": rate,
            "timestamp": datetime.now().isoformat(),
            "update_time": update_time,
        }

        self.save_history(history)
        logger.info(f"汇率已记录: {key} = {rate}")

    def check_and_record(
        self,
        rate: float,
        from_currency: str,
        to_currency: str,
        update_time: str = "",
        send_alert_func=None,
    ) -> Dict:
        """
        校验汇率并记录（完整流程）

        Args:
            rate: 当前汇率值
            from_currency: 源货币代码
            to_currency: 目标货币代码
            update_time: API返回的更新时间
            send_alert_func: 发送告警的回调函数，接收(alert_msg, current_rate, change_pct)

        Returns:
            Dict: 校验结果，包含success、error、change_pct等
        """
        # 获取上次汇率
        last_record = self.get_last_rate(from_currency, to_currency)
        last_rate = last_record.get("rate") if last_record else None

        # 校验汇率
        is_valid, message, change_pct = self.validate_rate(
            rate, from_currency, to_currency
        )

        result = {
            "success": is_valid,
            "message": message,
            "rate": rate,
            "last_rate": last_rate,
            "change_pct": change_pct,
            "alert_sent": False,
        }

        if not is_valid:
            logger.error(f"汇率校验失败: {message}")
            # 发送告警
            if send_alert_func:
                try:
                    send_alert_func(message, rate, change_pct)
                    result["alert_sent"] = True
                except Exception as e:
                    logger.error(f"发送告警失败: {e}")
        else:
            # 记录正常汇率
            self.record_rate(rate, from_currency, to_currency, update_time)
            if change_pct is not None:
                logger.info(f"汇率正常: {rate} (波动: {change_pct:+.2f}%)")

        return result

    def get_rate_history(
        self, from_currency: str, to_currency: str, days: int = 7
    ) -> List[Dict]:
        """
        获取汇率历史记录（用于趋势分析）

        Args:
            from_currency: 源货币代码
            to_currency: 目标货币代码
            days: 查询天数

        Returns:
            List[Dict]: 历史记录列表
        """
        # 注意：当前实现只保存最新值，如需完整历史需要扩展存储结构
        last_record = self.get_last_rate(from_currency, to_currency)
        if last_record:
            return [last_record]
        return []

    def clean_old_records(self, days: int = 30):
        """
        清理过期的历史记录

        Args:
            days: 保留天数
        """
        history = self.load_history()
        cutoff_date = datetime.now() - timedelta(days=days)

        cleaned = {}
        for key, record in history.items():
            timestamp = record.get("timestamp", "")
            try:
                record_date = datetime.fromisoformat(timestamp)
                if record_date > cutoff_date:
                    cleaned[key] = record
            except (ValueError, TypeError):
                # 无法解析时间戳，保留记录
                cleaned[key] = record

        self.save_history(cleaned)
        removed_count = len(history) - len(cleaned)
        if removed_count > 0:
            logger.info(f"清理了 {removed_count} 条过期汇率记录")


class ExchangeAlertSender:
    """
    汇率告警发送器
    封装告警消息构建和发送逻辑
    """

    def __init__(self, bot_name: str = "汇率监控"):
        self.bot_name = bot_name

    def build_alert_message(
        self,
        alert_type: str,
        currency_pair: str,
        current_rate: float,
        last_rate: Optional[float] = None,
        change_pct: Optional[float] = None,
    ) -> str:
        """
        构建告警消息

        Args:
            alert_type: 异常类型描述
            currency_pair: 货币对，如 "CNY/PHP"
            current_rate: 当前汇率
            last_rate: 上次汇率
            change_pct: 波动百分比

        Returns:
            str: Markdown格式的告警消息
        """
        change_info = ""
        if change_pct is not None:
            change_info = f"\n**波动幅度**: {change_pct:+.2f}%"
        elif last_rate is not None:
            change_pct_calc = (current_rate - last_rate) / last_rate * 100
            change_info = f"\n**波动幅度**: {change_pct_calc:+.2f}%"

        last_rate_info = f"\n**上次汇率**: {last_rate}" if last_rate else ""

        return f"""## 🚨 汇率异常告警

**监控器**: {self.bot_name}
**货币对**: {currency_pair}
**异常类型**: {alert_type}
**当前汇率**: {current_rate}{change_info}{last_rate_info}

**时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

请检查汇率API或联系管理员。
"""

    def send_alert(
        self,
        dingtalk_client,
        groups: List[Dict],
        alert_message: str,
        currency_code: str = "",
    ):
        """
        发送告警到指定群组

        Args:
            dingtalk_client: 钉钉客户端实例
            groups: 群组列表
            alert_message: 告警消息内容
            currency_code: 货币代码（用于标题）
        """
        title = f"汇率异常告警"
        if currency_code:
            title += f" - {currency_code}"

        for group in groups:
            open_conversation_id = group.get("open_conversation_id")
            name = group.get("name", "未命名")

            if open_conversation_id:
                try:
                    dingtalk_client.send_markdown_message(
                        open_conversation_id=open_conversation_id,
                        title=title,
                        text=alert_message,
                    )
                    logger.info(f"汇率告警已发送到群: {name}")
                except Exception as e:
                    logger.error(f"发送告警到群{name}失败: {e}")


# 便捷函数
def create_default_monitor() -> ExchangeMonitor:
    """创建默认配置的监控器"""
    return ExchangeMonitor()


def validate_exchange_rate(
    rate: float,
    from_currency: str,
    to_currency: str,
    history_file: str = DEFAULT_HISTORY_FILE,
) -> Tuple[bool, str]:
    """
    快速校验汇率（便捷函数）

    Args:
        rate: 当前汇率值
        from_currency: 源货币代码
        to_currency: 目标货币代码
        history_file: 历史记录文件路径

    Returns:
        Tuple[bool, str]: (是否通过校验, 错误信息)
    """
    monitor = ExchangeMonitor(history_file=history_file)
    is_valid, message, _ = monitor.validate_rate(rate, from_currency, to_currency)
    return is_valid, message
