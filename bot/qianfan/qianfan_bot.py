# encoding:utf-8

import time
import json
import requests
from typing import Dict, Any, Optional, Tuple

from bot.bot import Bot
from bot.qianfan.qianfan_session import QianfanSession, QianfanSessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf


class QianfanBot(Bot):
    """
    百度千帆平台聊天机器人
    实现与百度千帆APP对话接口的集成，支持多轮对话和会话管理
    """
    
    def __init__(self):
        """
        初始化千帆机器人
        从配置文件读取必要的API参数
        """
        super().__init__()
        # 使用千帆专用的会话管理器
        self.sessions = QianfanSessionManager(QianfanSession, model=conf().get("model") or "qianfan")
        
        # 验证配置参数
        self._validate_config()

    def _validate_config(self):
        """
        验证配置文件中的千帆相关参数
        """
        required_configs = ["qianfan_api_base", "qianfan_app_id", "qianfan_api_key"]
        missing_configs = []
        
        for config_key in required_configs:
            if not conf().get(config_key):
                missing_configs.append(config_key)
        
        if missing_configs:
            logger.error(f"[QIANFAN] 缺少必要的配置参数: {missing_configs}")
            raise ValueError(f"千帆机器人配置缺失: {missing_configs}")
        
        logger.info("[QIANFAN] 配置验证通过")

    def reply(self, query, context=None):
        """
        处理用户查询并返回回复
        
        Args:
            query: 用户查询内容
            context: 上下文信息，包含session_id等
            
        Returns:
            Reply: 回复对象
        """
        # 仅处理文本类型的消息
        if context.type == ContextType.TEXT:
            logger.info("[QIANFAN] 用户查询={}".format(query))

            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            logger.debug("[QIANFAN] 会话查询={}".format(session.messages))
            
            reply_result, err = self._reply_text(session_id, session)
            if err is not None:
                logger.error("[QIANFAN] 回复错误={}".format(err))
                return Reply(ReplyType.ERROR, "我暂时遇到了一些问题，请您稍后重试~")
            
            logger.debug(
                "[QIANFAN] 查询={}, 会话ID={}, 回复内容={}, 完成tokens={}".format(
                    query,
                    session_id,
                    reply_result["content"],
                    reply_result["completion_tokens"],
                )
            )
            
            # 将回复保存到会话中
            self.sessions.session_reply(reply_result["content"], session_id, reply_result["total_tokens"])
            
            # 检查是否包含图片URL，优先返回图片类型
            if reply_result.get("image_url"):
                logger.info(f"[QIANFAN] 检测到图片回复，返回图片URL: {reply_result['image_url']}")
                return Reply(ReplyType.IMAGE_URL, reply_result["image_url"])
            else:
                return Reply(ReplyType.TEXT, reply_result["content"])
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session):
        """
        兼容性方法，直接调用reply
        """
        return self.reply(session)

    def _get_api_base_url(self):
        """
        获取千帆API基础URL
        
        Returns:
            str: API基础URL
        """
        return conf().get("qianfan_api_base", "https://qianfan.baidubce.com/v2")

    def _get_headers(self):
        """
        构建API请求头
        
        Returns:
            dict: 包含认证信息的请求头
        """
        api_key = conf().get("qianfan_api_key", "")
        return {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def _get_app_id(self):
        """
        获取千帆应用ID
        
        Returns:
            str: 应用ID
        """
        return conf().get("qianfan_app_id", "")

    def _create_conversation(self) -> Tuple[Optional[str], Optional[str]]:
        """
        创建新的千帆对话
        
        Returns:
            Tuple[Optional[str], Optional[str]]: (conversation_id, error_message)
        """
        try:
            url = f"{self._get_api_base_url()}/app/conversation"
            headers = self._get_headers()
            payload = {
                "app_id": self._get_app_id()
            }
            
            logger.debug(f"[QIANFAN] 创建对话请求: {url}")
            
            response = requests.post(
                url, 
                headers=headers, 
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"创建对话失败，状态码: {response.status_code}, 响应: {response.text}"
                logger.error(f"[QIANFAN] {error_msg}")
                return None, error_msg
            
            result = response.json()
            conversation_id = result.get("conversation_id")
            
            if not conversation_id:
                error_msg = f"创建对话响应中未找到conversation_id: {result}"
                logger.error(f"[QIANFAN] {error_msg}")
                return None, error_msg
            
            logger.debug(f"[QIANFAN] 成功创建对话，conversation_id: {conversation_id}")
            return conversation_id, None
            
        except Exception as e:
            error_msg = f"创建对话时发生异常: {repr(e)}"
            logger.error(f"[QIANFAN] {error_msg}")
            return None, error_msg

    def _send_message(self, query: str, conversation_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        发送消息到千帆平台
        
        Args:
            query: 用户查询内容
            conversation_id: 对话ID
            
        Returns:
            Tuple[Optional[Dict], Optional[str]]: (回复内容字典, 错误信息)
        """
        try:
            url = f"{self._get_api_base_url()}/app/conversation/runs"
            headers = self._get_headers()
            payload = {
                "app_id": self._get_app_id(),
                "query": query,
                "conversation_id": conversation_id,
                "stream": False
            }
            
            logger.debug(f"[QIANFAN] 发送消息请求: {url}, conversation_id: {conversation_id}")
            
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                timeout=60  # 千帆响应可能较慢，设置较长超时时间
            )
            
            if response.status_code != 200:
                error_msg = f"发送消息失败，状态码: {response.status_code}, 响应: {response.text}"
                logger.error(f"[QIANFAN] {error_msg}")
                return None, error_msg
            
            result = response.json()
            logger.debug(f"[QIANFAN] 千帆API响应: {json.dumps(result, ensure_ascii=False)}")
            
            return result, None
            
        except Exception as e:
            error_msg = f"发送消息时发生异常: {repr(e)}"
            logger.error(f"[QIANFAN] {error_msg}")
            return None, error_msg

    def _extract_image_from_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        从千帆API响应中提取图片URL
        
        Args:
            response_data: 千帆API响应数据
            
        Returns:
            Optional[str]: 图片URL，如果没有找到则返回None
        """
        try:
            content_list = response_data.get("content", [])
            
            for content_item in content_list:
                # 检查是否是图片生成事件
                if (content_item.get("event_type") == "IRAG" and 
                    content_item.get("content_type") == "image" and 
                    content_item.get("event_status") == "done"):
                    
                    outputs = content_item.get("outputs", {})
                    image_url = outputs.get("image")
                    
                    if image_url:
                        logger.debug(f"[QIANFAN] 检测到生成的图片URL: {image_url}")
                        return image_url
            
            # 如果没有找到IRAG图片，尝试从answer文本中提取markdown图片链接
            answer = response_data.get("answer", "")
            import re
            markdown_img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            match = re.search(markdown_img_pattern, answer)
            if match:
                img_url = match.group(2)
                logger.debug(f"[QIANFAN] 从answer文本中提取到图片URL: {img_url}")
                return img_url
                
            return None
            
        except Exception as e:
            logger.error(f"[QIANFAN] 提取图片URL时发生异常: {repr(e)}")
            return None

    def _extract_answer_from_response(self, response_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[Dict[str, int]], Optional[str]]:
        """
        从千帆API响应中提取答案和token统计信息
        
        Args:
            response_data: 千帆API响应数据
            
        Returns:
            Tuple[Optional[str], Optional[Dict], Optional[str]]: (答案文本, token统计, 错误信息)
        """
        try:
            # 直接从响应中获取答案
            answer = response_data.get("answer")
            if not answer:
                return None, None, "响应中未找到answer字段"
            
            # 提取token使用统计
            token_usage = self._extract_token_usage(response_data)
            
            logger.debug(f"[QIANFAN] 提取到答案: {answer}")
            logger.debug(f"[QIANFAN] Token使用统计: {token_usage}")
            
            return answer, token_usage, None
            
        except Exception as e:
            error_msg = f"提取答案时发生异常: {repr(e)}"
            logger.error(f"[QIANFAN] {error_msg}")
            return None, None, error_msg

    def _extract_token_usage(self, response_data: Dict[str, Any]) -> Dict[str, int]:
        """
        从千帆响应中提取token使用统计
        
        Args:
            response_data: 千帆API响应数据
            
        Returns:
            Dict[str, int]: 包含prompt_tokens, completion_tokens, total_tokens的字典
        """
        total_prompt_tokens = 0
        total_completion_tokens = 0
        
        # 遍历content数组，累加所有usage中的token数量
        content_list = response_data.get("content", [])
        
        for content_item in content_list:
            usage = content_item.get("usage", {})
            if usage:
                total_prompt_tokens += usage.get("prompt_tokens", 0)
                total_completion_tokens += usage.get("completion_tokens", 0)
        
        total_tokens = total_prompt_tokens + total_completion_tokens
        
        return {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens
        }

    def _reply_text(self, session_id: str, session: QianfanSession, retry_count=0):
        """
        处理文本回复的核心逻辑
        
        Args:
            session_id: 会话ID
            session: 千帆会话实例
            retry_count: 重试次数
            
        Returns:
            Tuple[Optional[Dict], Optional[str]]: (回复内容字典, 错误信息)
        """
        try:
            # 获取当前用户查询（最后一条消息）
            if not session.messages or session.messages[-1]["role"] != "user":
                return None, "会话中没有找到用户消息"
            
            # 千帆平台作为独立智能体，只需要发送纯净的用户查询内容
            # 不需要包含 system 提示词，因为千帆智能体本身已有自己的人设
            query = session.messages[-1]["content"]
            
            logger.debug(f"[QIANFAN] 提取用户查询（不含system消息）: {query}")
            
            # 如果会话没有conversation_id，先创建一个
            conversation_id = session.get_conversation_id()
            if not conversation_id:
                conversation_id, err = self._create_conversation()
                if err is not None:
                    return None, f"创建对话失败: {err}"
                session.set_conversation_id(conversation_id)
            
            # 发送消息到千帆平台
            response_data, err = self._send_message(query, conversation_id)
            if err is not None:
                return None, f"发送消息失败: {err}"
            
            # 提取答案和token统计
            answer, token_usage, err = self._extract_answer_from_response(response_data)
            if err is not None:
                return None, f"提取答案失败: {err}"
            
            # 检测是否包含图片
            image_url = self._extract_image_from_response(response_data)
            
            # 构建返回结果
            result = {
                "content": answer,
                "total_tokens": token_usage.get("total_tokens", 0),
                "completion_tokens": token_usage.get("completion_tokens", 0),
                "prompt_tokens": token_usage.get("prompt_tokens", 0),
                "image_url": image_url  # 添加图片URL信息
            }
            
            if image_url:
                logger.debug(f"[QIANFAN] 响应包含图片URL: {image_url}")
            
            return result, None
            
        except Exception as e:
            # 重试逻辑
            if retry_count < 2:
                time.sleep(3)
                logger.warn(f"[QIANFAN] 异常: {repr(e)} 第{retry_count + 1}次重试")
                return self._reply_text(session_id, session, retry_count + 1)
            else:
                return None, f"[QIANFAN] 异常: {repr(e)} 超过最大重试次数"

    def reset_conversation(self, session_id: str):
        """
        重置指定会话的对话状态
        
        Args:
            session_id: 要重置的会话ID
        """
        try:
            if session_id in self.sessions.sessions:
                session = self.sessions.sessions[session_id]
                session.reset_conversation()
                logger.info(f"[QIANFAN] 已重置会话 {session_id} 的对话状态")
        except Exception as e:
            logger.error(f"[QIANFAN] 重置会话时发生异常: {repr(e)}")

    def clear_session(self, session_id: str):
        """
        清除指定会话
        
        Args:
            session_id: 要清除的会话ID
        """
        self.sessions.clear_session(session_id)

    def clear_all_sessions(self):
        """
        清除所有会话
        """
        self.sessions.clear_all_session()