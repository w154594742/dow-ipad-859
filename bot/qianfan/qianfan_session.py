# encoding:utf-8

from bot.session_manager import Session
from common.log import logger
from config import conf


class QianfanSession(Session):
    """
    千帆平台会话管理类
    负责管理单个会话的状态，包括消息历史和会话ID
    """
    
    def __init__(self, session_id, system_prompt=None, model="qianfan"):
        """
        初始化千帆会话
        
        Args:
            session_id: 会话唯一标识符
            system_prompt: 系统提示词（千帆平台通过app配置管理，这里忽略）
            model: 模型名称，默认为qianfan
        """
        # 不调用父类的__init__，避免添加system_prompt
        self.session_id = session_id
        self.system_prompt = ""  # 千帆平台不使用system_prompt
        self.model = model
        self.conversation_id = None  # 千帆平台的对话ID，首次调用时创建
        self.reset()
        
        logger.debug(f"[QIANFAN_SESSION] 初始化会话 {session_id}，不使用system提示词")

    def reset(self):
        """
        重置会话消息列表
        千帆平台不使用system消息，直接初始化为空列表
        """
        self.messages = []
        logger.debug(f"[QIANFAN_SESSION] 重置会话消息列表，不添加system消息")

    def get_conversation_id(self):
        """
        获取千帆平台的对话ID
        
        Returns:
            str: 千帆平台的conversation_id，如果没有则返回None
        """
        return self.conversation_id
    
    def set_conversation_id(self, conversation_id):
        """
        设置千帆平台的对话ID
        
        Args:
            conversation_id: 千帆平台返回的对话ID
        """
        self.conversation_id = conversation_id
        logger.debug(f"[QIANFAN_SESSION] 设置conversation_id: {conversation_id}")

    def discard_exceeding(self, max_tokens, cur_tokens=None):
        """
        丢弃超出最大token限制的消息
        千帆平台通过conversation_id管理历史，这里主要用于本地消息管理
        
        Args:
            max_tokens: 最大token数量
            cur_tokens: 当前token数量
            
        Returns:
            int: 处理后的token数量
        """
        precise = True
        try:
            cur_tokens = self.calc_tokens()
        except Exception as e:
            precise = False
            if cur_tokens is None:
                raise e
            logger.debug("计算token时发生异常: {}".format(e))
            
        # 当超出限制时，从最早的消息开始丢弃（保留system消息）
        while cur_tokens > max_tokens:
            if len(self.messages) > 2:
                # 移除最早的用户消息或助手回复（保留system消息）
                self.messages.pop(1)
            elif len(self.messages) == 2 and self.messages[1]["role"] == "assistant":
                self.messages.pop(1)
                if precise:
                    cur_tokens = self.calc_tokens()
                else:
                    cur_tokens = cur_tokens - max_tokens
                break
            elif len(self.messages) == 2 and self.messages[1]["role"] == "user":
                logger.warn("用户消息超出最大token限制. total_tokens={}".format(cur_tokens))
                break
            else:
                logger.debug("max_tokens={}, total_tokens={}, len(messages)={}".format(
                    max_tokens, cur_tokens, len(self.messages)))
                break
            if precise:
                cur_tokens = self.calc_tokens()
            else:
                cur_tokens = cur_tokens - max_tokens
        return cur_tokens

    def calc_tokens(self):
        """
        计算当前会话的token数量
        由于千帆平台API没有直接返回token统计，这里使用字符数量进行简单估算
        
        Returns:
            int: 估算的token数量
        """
        return self._calc_tokens_by_character()

    def _calc_tokens_by_character(self):
        """
        通过字符数量估算token数量
        中文字符大约1个字符 = 1个token，英文单词大约4个字符 = 1个token
        这里简单按字符数量计算
        
        Returns:
            int: 估算的token数量
        """
        tokens = 0
        for msg in self.messages:
            content = msg.get("content", "")
            # 简单估算：中英文字符都按1:1计算token
            tokens += len(content)
        return tokens

    def reset_conversation(self):
        """
        重置千帆对话ID，用于开始新的对话
        保留session消息历史，但清空千帆平台的conversation_id
        """
        self.conversation_id = None
        logger.debug(f"[QIANFAN_SESSION] 已重置conversation_id，开始新对话")


class QianfanSessionManager:
    """
    千帆会话管理器
    负责管理多个用户会话，提供会话的创建、查询、更新等功能
    """
    
    def __init__(self, sessioncls=QianfanSession, **session_args):
        """
        初始化会话管理器
        
        Args:
            sessioncls: 会话类，默认为QianfanSession
            **session_args: 传递给会话类的额外参数
        """
        from common.expired_dict import ExpiredDict
        
        # 根据配置决定使用带过期时间的字典还是普通字典
        if conf().get("expires_in_seconds"):
            sessions = ExpiredDict(conf().get("expires_in_seconds"))
        else:
            sessions = dict()
            
        self.sessions = sessions
        self.sessioncls = sessioncls
        self.session_args = session_args

    def _build_session(self, session_id: str, system_prompt=None):
        """
        构建或获取会话实例
        
        Args:
            session_id: 会话ID
            system_prompt: 系统提示词
            
        Returns:
            QianfanSession: 会话实例
        """
        if session_id is None:
            return self.sessioncls(session_id, system_prompt, **self.session_args)

        if session_id not in self.sessions:
            self.sessions[session_id] = self.sessioncls(session_id, system_prompt, **self.session_args)
        session = self.sessions[session_id]
        return session

    def session_query(self, query, session_id):
        """
        处理用户查询，将查询添加到会话中
        
        Args:
            query: 用户查询内容
            session_id: 会话ID
            
        Returns:
            QianfanSession: 更新后的会话实例
        """
        session = self._build_session(session_id)
        session.add_query(query)
        
        # 可选：根据配置限制对话token数量
        try:
            max_tokens = conf().get("conversation_max_tokens", 2000)
            total_tokens = session.discard_exceeding(max_tokens, None)
            logger.debug("会话token使用量={}".format(total_tokens))
        except Exception as e:
            logger.warning("计算会话token时发生异常: {}".format(str(e)))
            
        return session

    def session_reply(self, reply, session_id, total_tokens=None):
        """
        将AI回复添加到会话中
        
        Args:
            reply: AI回复内容
            session_id: 会话ID
            total_tokens: 本次对话消耗的token数量
            
        Returns:
            QianfanSession: 更新后的会话实例
        """
        session = self._build_session(session_id)
        session.add_reply(reply)
        
        try:
            max_tokens = conf().get("conversation_max_tokens", 2000)
            tokens_cnt = session.discard_exceeding(max_tokens, total_tokens)
            logger.debug("原始total_tokens={}, 会话保存tokens={}".format(total_tokens, tokens_cnt))
        except Exception as e:
            logger.warning("保存会话时计算token发生异常: {}".format(str(e)))
            
        return session

    def clear_session(self, session_id):
        """
        清除指定会话
        
        Args:
            session_id: 要清除的会话ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.debug(f"[QIANFAN_SESSION_MANAGER] 已清除会话: {session_id}")

    def clear_all_session(self):
        """
        清除所有会话
        """
        self.sessions.clear()
        logger.debug("[QIANFAN_SESSION_MANAGER] 已清除所有会话")