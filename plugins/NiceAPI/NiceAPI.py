# NiceAPI.py
# encoding:utf-8

import os
import time
import random
import datetime
import requests
import plugins
import threading
import json
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from common.tmp_dir import TmpDir
from plugins import *
from config import conf
from io import BytesIO  # 确保导入BytesIO，如果需要的话
from PIL import Image

@plugins.register(
    name="NiceAPI",
    desire_priority=600,
    hidden=False,
    desc="一个输入关键词就能返回随机图片和视频的插件，支持王者英雄语音",
    version="0.2",
    author="Lingyuzhou",
)
class NiceAPI(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.config = self.load_config()
        logger.info("[NiceAPI] inited.")

    def load_config(self):
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info("[NiceAPI] Config loaded successfully.")
                return config
            else:
                logger.warning(f"[NiceAPI] Config file not found at {config_path}")
                return {"api_mapping": {}}
        except Exception as e:
            logger.error(f"[NiceAPI] Error loading config: {e}")
            return {"api_mapping": {}}

    def call_api(self, url, params=None):
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type')
                if 'audio/mpeg' in content_type or url.endswith('.mp3'):
                    logger.debug("Audio content detected")
                    # 保存音频文件到临时目录
                    tmp_dir = TmpDir().path()
                    timestamp = int(time.time())
                    random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
                    audio_name = f"nice_audio_{timestamp}_{random_str}.mp3"
                    audio_path = os.path.join(tmp_dir, audio_name)
                    
                    with open(audio_path, "wb") as f:
                        f.write(response.content)
                    
                    if os.path.getsize(audio_path) == 0:
                        logger.error("[NiceAPI] Downloaded audio file is empty")
                        os.remove(audio_path)
                        return None
                    
                    logger.info(f"[NiceAPI] Audio saved to {audio_path}")
                    return {"voice": audio_path}
                elif 'image' in content_type:
                    logger.debug("Image content detected")
                    return {"image": response.url}
                elif 'video' in content_type:
                    logger.debug("Video content detected")
                    return {"video": response.url}
                elif 'application/json' in content_type:
                    logger.debug("JSON content detected")
                    json_data = response.json()
                    if json_data.get('code') == 1 and json_data.get('data'):
                        # 随机选择一条语音
                        voice_item = random.choice(json_data['data'])
                        voice_url = voice_item.get('voice')
                        if voice_url:
                            # 下载并保存语音文件
                            voice_response = requests.get(voice_url)
                            if voice_response.status_code == 200:
                                tmp_dir = TmpDir().path()
                                timestamp = int(time.time())
                                random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
                                audio_name = f"nice_audio_{timestamp}_{random_str}.mp3"
                                audio_path = os.path.join(tmp_dir, audio_name)
                                
                                with open(audio_path, "wb") as f:
                                    f.write(voice_response.content)
                                
                                if os.path.getsize(audio_path) > 0:
                                    logger.info(f"[NiceAPI] Voice saved to {audio_path}")
                                    return {"voice": audio_path}
                                else:
                                    logger.error("[NiceAPI] Downloaded voice file is empty")
                                    os.remove(audio_path)
                    return None
                elif 'text' in content_type or 'text/plain' in content_type:
                    logger.debug("Text content detected, checking for image URL")
                    text_content = response.text.strip()
                    # 检查是否是图片URL
                    if any(text_content.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) and \
                       (text_content.startswith('http://') or text_content.startswith('https://')):
                        logger.info(f"[NiceAPI] Detected image URL in text response: {text_content}")
                        return {"image": text_content}
                else:
                    logger.error(f"[NiceAPI] Unsupported content type: {content_type}")
                    return None
            else:
                logger.error(f"[NiceAPI] 请求失败，状态码: {response.status_code}, 内容: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"[NiceAPI] 请求异常: {e}")
            return None

    def create_reply(self, reply_type, content):
        return Reply(type=reply_type, content=content)

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type != ContextType.TEXT:
            return

        content = e_context["context"].content.strip()
        logger.debug("[NiceAPI] on_handle_context. content: %s" % content)

        # 从配置文件获取API映射
        api_mapping = self.config.get("api_mapping", {})

        # 处理王者英雄语音请求
        if content.startswith("王者 "):
            hero_name = content[3:].strip()
            if hero_name:
                url = api_mapping.get("王者")
                if url:
                    reply = self.call_api(url, params={"msg": hero_name})
                    if reply and "voice" in reply:
                        e_context["reply"] = self.create_reply(ReplyType.VOICE, reply["voice"])
                        e_context.action = EventAction.BREAK_PASS
                        return

        # 处理emoji合成请求
        if content.startswith("表情合成 "):
            emoji_text = content[len("表情合成 "):].strip()
            if not emoji_text:
                e_context["reply"] = self.create_reply(ReplyType.TEXT, "请输入需要合成的表情，格式：表情1+表情2")
                e_context.action = EventAction.BREAK_PASS
                return
                
            if "+" not in emoji_text:
                e_context["reply"] = self.create_reply(ReplyType.TEXT, "表情格式错误，请使用+号分隔两个表情，例如：🐶+💩")
                e_context.action = EventAction.BREAK_PASS
                return
                
            emoji1, emoji2 = emoji_text.split("+", 1)
            emoji1 = emoji1.strip()
            emoji2 = emoji2.strip()
            
            if not emoji1 or not emoji2:
                e_context["reply"] = self.create_reply(ReplyType.TEXT, "表情不能为空，请输入两个有效的表情")
                e_context.action = EventAction.BREAK_PASS
                return
            
            url = api_mapping.get("表情合成")
            if not url:
                e_context["reply"] = self.create_reply(ReplyType.TEXT, "表情合成功能未配置，请联系管理员")
                e_context.action = EventAction.BREAK_PASS
                return
                
            try:
                # 构建完整的API URL
                full_url = f"{url}?type=text&emoji1={emoji1}&emoji2={emoji2}"
                response = requests.get(full_url)
                
                if response.status_code != 200:
                    error_msg = f"表情合成失败，错误码：{response.status_code}"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg = f"表情合成失败：{error_data['message']}"
                    except:
                        pass
                    e_context["reply"] = self.create_reply(ReplyType.TEXT, error_msg)
                    e_context.action = EventAction.BREAK_PASS
                    return
                    
                text_content = response.text.strip()
                if not text_content:
                    e_context["reply"] = self.create_reply(ReplyType.TEXT, "表情合成失败：返回内容为空")
                    e_context.action = EventAction.BREAK_PASS
                    return
                    
                # 检查是否是图片URL
                if any(text_content.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) and \
                   (text_content.startswith('http://') or text_content.startswith('https://')):                    
                    # 下载并处理图片
                    try:
                        image_response = requests.get(text_content)
                        image_response.raise_for_status()
                        
                        # 使用PIL处理图片
                        image = Image.open(BytesIO(image_response.content))
                        
                        # 确保图片是RGBA模式
                        if image.mode != 'RGBA':
                            image = image.convert('RGBA')
                        
                        # 创建一个新的RGB模式的白色背景图片
                        white_bg = Image.new('RGB', image.size, (255, 255, 255))
                        
                        # 使用alpha通道作为mask进行合成
                        white_bg.paste(image, (0, 0), image.split()[3])
                        
                        # 转换回BytesIO对象
                        output = BytesIO()
                        white_bg.convert('RGB').save(output, format='PNG')
                        output.seek(0)  # 重要：将指针移回开始位置
                        
                        logger.info(f"[NiceAPI] Image processed successfully for emoji mix")
                        e_context["reply"] = self.create_reply(ReplyType.IMAGE, output)
                        e_context.action = EventAction.BREAK_PASS
                        return
                    except Exception as e:
                        logger.error(f"[NiceAPI] Error processing emoji mix image: {e}")
                        e_context["reply"] = self.create_reply(ReplyType.TEXT, "表情合成失败：图片处理异常")
                        e_context.action = EventAction.BREAK_PASS
                        return
                    logger.info(f"[NiceAPI] Detected image URL in emoji mix response: {text_content}")
                    e_context["reply"] = self.create_reply(ReplyType.IMAGE_URL, text_content)
                    e_context.action = EventAction.BREAK_PASS
                    return
                else:
                    e_context["reply"] = self.create_reply(ReplyType.TEXT, "表情合成失败：返回内容格式错误")
                    e_context.action = EventAction.BREAK_PASS
                    return
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"[NiceAPI] 表情合成请求异常: {e}")
                e_context["reply"] = self.create_reply(ReplyType.TEXT, f"表情合成失败：网络请求异常，请稍后重试")
                e_context.action = EventAction.BREAK_PASS
                return

        # 检查内容是否包含任意关键词
        for keyword, url in api_mapping.items():
            if keyword in content:
                reply = self.call_api(url)
                if reply:
                    if "image" in reply:
                        e_context["reply"] = self.create_reply(ReplyType.IMAGE_URL, reply["image"])  # 创建图片回复
                    elif "video" in reply:
                        e_context["reply"] = self.create_reply(ReplyType.VIDEO_URL, reply["video"])  # 创建视频回复
                    elif "voice" in reply:
                        e_context["reply"] = self.create_reply(ReplyType.VOICE, reply["voice"])  # 创建语音回复
                    e_context.action = EventAction.BREAK_PASS
                    break  # 找到第一个匹配的关键词后就退出循环

    def get_video_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            content_type = response.headers.get('Content-Type')
            if 'video' in content_type:
                logger.debug("Video content detected")
                return response.url
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def is_valid_url(self, url):
        return url.startswith("http://") or url.startswith("https://")

    def download_image(self, image_url):
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = BytesIO(response.content)
            logger.info("Image downloaded successfully")
            return image_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {e}")
            return None

    def get_help_text(self, isgroup=False, isadmin=False, verbose=False):
        # 获取所有关键词并格式化为字符串
        keywords = "|".join([
            "小姐姐", "小黑子", "唱首歌", "撒个娇", "黑丝图片", "白丝图片", "黑丝视频", "白丝视频", "黑白双煞", "御姐视频",
            "吊带视频", "完美身材", "晴天视频", "音乐视频", "慢摇系列", "火车摇系", "擦玻璃系", "清纯系列", "汉服古风", "热舞视频", "美女视频",
            "手机壁纸", "电脑壁纸"
        ])
        return f"输入关键词【{keywords}】即可返回相应图片或视频。\n输入【王者 英雄名称】可获取英雄语音，如：王者 后羿。\n输入【表情合成 表情1+表情2】可获取英雄语音，如：表情合成 🐶+💩"