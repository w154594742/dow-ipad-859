# encoding:utf-8

"""
百度千帆平台机器人模块

此模块实现了与百度千帆平台的集成，提供聊天机器人功能。

主要组件:
- QianfanBot: 千帆聊天机器人主类
- QianfanSession: 千帆会话管理类
- QianfanSessionManager: 千帆会话管理器

使用方法:
1. 在 config.json 中配置以下参数:
   - qianfan_api_base: 千帆API基础URL
   - qianfan_app_id: 千帆应用ID
   - qianfan_api_key: 千帆API密钥

2. 设置 bot_type 为 "qianfan" 来使用千帆机器人

示例配置:
{
    "bot_type": "qianfan",
    "qianfan_api_base": "https://qianfan.baidubce.com/v2",
    "qianfan_app_id": "your_app_id",
    "qianfan_api_key": "your_api_key"
}
"""

from .qianfan_bot import QianfanBot
from .qianfan_session import QianfanSession, QianfanSessionManager

__all__ = ["QianfanBot", "QianfanSession", "QianfanSessionManager"]