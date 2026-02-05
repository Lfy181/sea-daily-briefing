#!/usr/bin/env python3
"""
机器人工厂
根据配置创建对应的机器人实例
"""

import json
import logging
from typing import Dict, List, Optional

from .city_bot import CityBot

logger = logging.getLogger(__name__)


class BotFactory:
    """
    机器人工厂类
    负责从配置文件中读取机器人配置并创建实例
    """

    @staticmethod
    def load_bots_config(config_path: str = "config/bots.json") -> List[Dict]:
        """
        加载机器人配置

        Args:
            config_path: 配置文件路径

        Returns:
            List[Dict]: 机器人配置列表
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                bots = data.get("bots", [])
                logger.info(f"成功加载{len(bots)}个机器人配置")
                return bots
        except FileNotFoundError:
            logger.error(f"机器人配置文件不存在: {config_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"解析机器人配置文件失败: {e}")
            return []
        except Exception as e:
            logger.error(f"读取机器人配置失败: {e}")
            return []

    @staticmethod
    def create_bot(config: Dict) -> Optional[CityBot]:
        """
        根据配置创建机器人实例

        Args:
            config: 单个机器人配置字典

        Returns:
            Optional[CityBot]: 机器人实例，失败返回None
        """
        try:
            bot = CityBot(config)
            return bot
        except Exception as e:
            logger.error(f"创建机器人失败: {e}")
            return None

    @staticmethod
    def create_all_bots(config_path: str = "config/bots.json") -> List[CityBot]:
        """
        创建所有配置的机器人

        Args:
            config_path: 配置文件路径

        Returns:
            List[CityBot]: 机器人实例列表
        """
        configs = BotFactory.load_bots_config(config_path)
        bots = []

        for config in configs:
            bot = BotFactory.create_bot(config)
            if bot:
                bots.append(bot)

        logger.info(f"成功创建{len(bots)}个机器人实例")
        return bots

    @staticmethod
    def get_bot_by_name(name: str, config_path: str = "config/bots.json") -> Optional[CityBot]:
        """
        根据名称获取特定机器人

        Args:
            name: 机器人名称
            config_path: 配置文件路径

        Returns:
            Optional[CityBot]: 机器人实例，未找到返回None
        """
        configs = BotFactory.load_bots_config(config_path)

        for config in configs:
            if config.get("name") == name:
                return BotFactory.create_bot(config)

        logger.warning(f"未找到名为'{name}'的机器人配置")
        return None

    @staticmethod
    def get_bot_by_country(country_code: str, config_path: str = "config/bots.json") -> Optional[CityBot]:
        """
        根据国家代码获取特定机器人

        Args:
            country_code: 国家代码（如 'PH', 'VN'）
            config_path: 配置文件路径

        Returns:
            Optional[CityBot]: 机器人实例，未找到返回None
        """
        configs = BotFactory.load_bots_config(config_path)

        for config in configs:
            if config.get("country") == country_code:
                return BotFactory.create_bot(config)

        logger.warning(f"未找到国家代码'{country_code}'的机器人配置")
        return None
