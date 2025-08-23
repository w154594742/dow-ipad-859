# encoding:utf-8

import json
import os
import random
import string
import logging
from typing import Tuple

import bridge.bridge
import plugins
from bridge.bridge import Bridge
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common import const
from config import conf, load_config, global_config
from plugins import *

# 定义指令集
COMMANDS = {
    "help": {
        "alias": ["help", "帮助", "功能列表"],
        "args": ["[插件名]"],
        "desc": "回复此帮助，或指定插件名查看插件帮助",
    },
    "auth": {
        "alias": ["auth", "认证"],
        "args": ["口令"],
        "desc": "管理员认证",
    },
    "role": {
        "alias": ["role", "角色", "角色切换"],
        "args": ["角色名称"],
        "desc": "切换机器人角色设定，使用#role 角色名称 或 #人设 角色名称",
    },
    "rolelist": {
        "alias": ["rolelist", "角色列表", "人设列表"],
        "desc": "显示按序号排列的可用角色列表",
    },
    "reset_role": {
        "alias": ["reset_role", "重置角色", "默认角色"],
        "desc": "重置为默认角色设定（来自config.json）",
    },
    "model": {
        "alias": ["model", "模型"],
        "desc": "查看和设置全局模型",
    },
    "set_openai_api_key": {
        "alias": ["set_openai_api_key"],
        "args": ["api_key"],
        "desc": "设置你的OpenAI私有api_key",
    },
    "reset_openai_api_key": {
        "alias": ["reset_openai_api_key"],
        "desc": "重置为默认的api_key",
    },
    "set_gpt_model": {
        "alias": ["set_gpt_model"],
        "desc": "设置你的私有模型",
    },
    "reset_gpt_model": {
        "alias": ["reset_gpt_model"],
        "desc": "重置你的私有模型",
    },
    "gpt_model": {
        "alias": ["gpt_model"],
        "desc": "查询你使用的模型",
    },
    "id": {
        "alias": ["id", "用户"],
        "desc": "获取用户id",  # wechaty和wechatmp的用户id不会变化，可用于绑定管理员
    },
    "reset": {
        "alias": ["reset", "重置会话"],
        "desc": "重置会话",
    },
    "modellist": {
        "alias": ["modellist", "模型列表"],
        "desc": "显示可用的AI模型列表",
    }
}

ADMIN_COMMANDS = {
    "resume": {
        "alias": ["resume", "恢复服务"],
        "desc": "恢复服务",
    },
    "stop": {
        "alias": ["stop", "暂停服务"],
        "desc": "暂停服务",
    },
    "reconf": {
        "alias": ["reconf", "重载配置"],
        "desc": "重载配置(不包含插件配置)",
    },
    "resetall": {
        "alias": ["resetall", "重置所有会话"],
        "desc": "重置所有会话",
    },
    "scanp": {
        "alias": ["scanp", "扫描插件"],
        "desc": "扫描插件目录是否有新插件",
    },
    "plist": {
        "alias": ["plist", "插件"],
        "desc": "打印当前插件列表",
    },
    "setpri": {
        "alias": ["setpri", "设置插件优先级"],
        "args": ["插件名", "优先级"],
        "desc": "设置指定插件的优先级，越大越优先",
    },
    "reloadp": {
        "alias": ["reloadp", "重载插件"],
        "args": ["插件名"],
        "desc": "重载指定插件配置",
    },
    "enablep": {
        "alias": ["enablep", "启用插件"],
        "args": ["插件名"],
        "desc": "启用指定插件",
    },
    "disablep": {
        "alias": ["disablep", "禁用插件"],
        "args": ["插件名"],
        "desc": "禁用指定插件",
    },
    "installp": {
        "alias": ["installp", "安装插件"],
        "args": ["仓库地址或插件名"],
        "desc": "安装指定插件",
    },
    "uninstallp": {
        "alias": ["uninstallp", "卸载插件"],
        "args": ["插件名"],
        "desc": "卸载指定插件",
    },
    "updatep": {
        "alias": ["updatep", "更新插件"],
        "args": ["插件名"],
        "desc": "更新指定插件",
    },
    "ahelp": {
        "alias": ["ahelp"],
        "desc": "显示管理员专属指令列表",
    },
    "debug": {
        "alias": ["debug", "调试模式", "DEBUG"],
        "desc": "开启机器调试日志",
    },
}

def generate_temporary_password(length=12):
    """
    根据设置生成临时密码。
    确保生成的密码至少包含一个小写字母、大写字母、数字和特殊字符。
    
    参数:
    length (int): 密码的长度，默认为12。
    
    返回:
    str: 生成的临时密码。
    """
    # 定义大写字母集合
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    # 定义小写字母集合
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    # 定义数字集合
    digits = "0123456789"
    # 定义特殊字符集合
    special_chars = "!@#$%&?"  
    # 合并所有字符集合
    all_chars = uppercase + lowercase + digits + special_chars
    
    # 循环生成密码，直到满足包含所有类型字符的条件
    while True:
        # 随机选择字符生成密码
        password = ''.join(random.choice(all_chars) for _ in range(length))
        # 检查密码是否包含所有类型字符
        if (any(c in uppercase for c in password)
                and any(c in lowercase for c in password)
                and any(c in digits for c in password)
                and any(c in special_chars for c in password)):
            break

    # 返回生成的密码
    return password


# 定义帮助函数
def get_help_text(isadmin, isgroup):
    help_text = "通用指令\n"
    for cmd, info in COMMANDS.items():
        if cmd in ["auth", "set_openai_api_key", "reset_openai_api_key", "set_gpt_model", "reset_gpt_model", "gpt_model"]:  # 不显示帮助指令
            continue
        if cmd == "id" and conf().get("channel_type", "wx") not in ["wxy", "wechatmp"]:
            continue
        alias = ["#" + a for a in info["alias"][:1]]
        help_text += f"{','.join(alias)} "
        if "args" in info:
            args = [a for a in info["args"]]
            help_text += f"{' '.join(args)}"
        help_text += f": {info['desc']}\n"

    # 插件指令
    plugins = PluginManager().list_plugins()
    help_text += "\n可用插件"
    for plugin in plugins:
        if plugins[plugin].enabled and not plugins[plugin].hidden:
            namecn = plugins[plugin].namecn
            help_text += "\n%s:" % namecn
            help_text += PluginManager().instances[plugin].get_help_text(verbose=False).strip()

    if ADMIN_COMMANDS and isadmin:
        help_text += "\n\n管理员指令：\n"
        for cmd, info in ADMIN_COMMANDS.items():
            alias = ["#" + a for a in info["alias"][:1]]
            help_text += f"{','.join(alias)} "
            if "args" in info:
                args = [a for a in info["args"]]
                help_text += f"{' '.join(args)}"
            help_text += f": {info['desc']}\n"
    return help_text


@plugins.register(
    name="Godcmd",
    desire_priority=999,
    hidden=True,
    desc="为你的机器人添加指令集，有用户和管理员两种角色，加载顺序请放在首位，初次运行后插件目录会生成配置文件, 填充管理员密码后即可认证",
    version="1.0",
    author="lanvent",
)
class Godcmd(Plugin):
    def __init__(self):
        super().__init__()

        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        gconf = super().load_config()
        if not gconf: # If config file is missing or empty
            if not os.path.exists(config_path):
                # Define a default structure for a new config file (without fixed_help_content)
                default_gconf = {
                    "password": "", 
                    "admin_users": []
                }
                with open(config_path, "w", encoding='utf-8') as f:
                    json.dump(default_gconf, f, indent=4, ensure_ascii=False)
                gconf = default_gconf # Use default if a new file was created
            else:
                # Config file exists but might be empty or invalid JSON, treat as minimal config
                gconf = {"password": "", "admin_users": []}
        
        # Load fixed help text from fixed_help_content.txt
        help_text_filepath = os.path.join(os.path.dirname(__file__), "fixed_help_content.txt")
        DEFAULT_TEXT_WHEN_FILE_ISSUE = "帮助信息文件 (plugins/godcmd/fixed_help_content.txt) 未找到、为空或读取失败。\n请检查文件是否存在、内容不为空且为 UTF-8 编码。"
        try:
            with open(help_text_filepath, "r", encoding="utf-8") as f:
                self.fixed_help_text_from_file = f.read()
            if not self.fixed_help_text_from_file.strip(): # Handle empty file
                self.fixed_help_text_from_file = "帮助信息文件 (plugins/godcmd/fixed_help_content.txt) 内容为空。请填充帮助信息。"
                logger.warning("[Godcmd] Fixed help file is empty: %s", help_text_filepath)
        except FileNotFoundError:
            self.fixed_help_text_from_file = DEFAULT_TEXT_WHEN_FILE_ISSUE
            logger.warning("[Godcmd] Fixed help file not found at: %s", help_text_filepath)
        except Exception as e:
            self.fixed_help_text_from_file = f"读取帮助信息文件 (plugins/godcmd/fixed_help_content.txt) 时发生错误。\n详情: {str(e)[:200]}"
            logger.error("[Godcmd] Error reading fixed help file %s: %s", help_text_filepath, e, exc_info=True)

        # Ensure self.fixed_help_text_from_file always has a value
        if not hasattr(self, 'fixed_help_text_from_file') or self.fixed_help_text_from_file is None:
             self.fixed_help_text_from_file = DEFAULT_TEXT_WHEN_FILE_ISSUE

        # Load other configurations from gconf (password, admin_users etc.)
        if gconf.get("password") == "": # Use .get for safety, though gconf should have it
            self.temp_password = generate_temporary_password()
            logger.info("[Godcmd] 因未设置口令，本次的临时口令为 === {} ===。".format(self.temp_password))
        else:
            self.temp_password = None
        
        # Ensure password and admin_users are loaded, even if gconf was initially problematic but file existed
        self.password = gconf.get("password", "") 
        self.admin_users = gconf.get("admin_users", [])
        global_config["admin_users"] = self.admin_users # Ensure admin list is in global_config

        # Load role map from role_map.json
        role_map_path = os.path.join(os.path.dirname(__file__), "role_map.json")
        try:
            with open(role_map_path, "r", encoding="utf-8") as f:
                self.role_map = json.load(f)
            logger.info("[Godcmd] Role map loaded from %s", role_map_path)
        except FileNotFoundError:
            self.role_map = {}
            logger.warning("[Godcmd] Role map file not found at %s. Role switching will not be available.", role_map_path)
        except json.JSONDecodeError:
            self.role_map = {}
            logger.error("[Godcmd] Error decoding role map file %s. Role switching will not be available.", role_map_path)
        except Exception as e:
            self.role_map = {}
            logger.error("[Godcmd] Error loading role map file %s: %s. Role switching will not be available.", role_map_path, e, exc_info=True)

        custom_commands = conf().get("clear_memory_commands", [])
        for custom_command in custom_commands:
            if custom_command and custom_command.startswith("#"):
                custom_command = custom_command[1:]
                if custom_command and custom_command not in COMMANDS["reset"]["alias"]:
                    COMMANDS["reset"]["alias"].append(custom_command)

        self.isrunning = True  # 机器人是否运行中

        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Godcmd] inited")

    def on_handle_context(self, e_context: EventContext):
        context_type = e_context["context"].type
        if context_type != ContextType.TEXT:
            if not self.isrunning:
                e_context.action = EventAction.BREAK_PASS
            return

        content = e_context["context"].content
        logger.debug("[Godcmd] on_handle_context. content: %s" % content)
        if content.startswith("#"):
            if len(content) == 1:
                reply = Reply()
                reply.type = ReplyType.ERROR
                reply.content = f"空指令，输入#help查看指令列表\n"
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            # msg = e_context['context']['msg']
            channel = e_context["channel"]
            user = e_context["context"]["receiver"]
            session_id = e_context["context"]["session_id"]
            isgroup = e_context["context"].get("isgroup", False)
            bottype = Bridge().get_bot_type("chat")
            bot = Bridge().get_bot("chat")
            # 将命令和参数分割
            command_parts = content[1:].strip().split()
            cmd = command_parts[0]
            args = command_parts[1:]
            isadmin = False
            if user in self.admin_users:
                isadmin = True
            ok = False
            result = "string"
            if any(cmd_alias in info["alias"] for info in COMMANDS.values() for cmd_alias in ([cmd] if isinstance(cmd, str) else cmd)):
                # Find the canonical command name for the given alias
                canonical_cmd = ""
                for c_name, c_info in COMMANDS.items():
                    if cmd in c_info["alias"]:
                        canonical_cmd = c_name
                        break
                
                if canonical_cmd == "help":
                    if len(args) == 0: # #help, #帮助, #功能列表 (no arguments)
                        ok, result = True, self.fixed_help_text_from_file
                    else: # #help <plugin_name>, #帮助 <plugin_name>, etc.
                        plugins_list = PluginManager().list_plugins()
                        query_name = args[0].upper()
                        found_plugin = False
                        for name, plugincls in plugins_list.items():
                            if not plugincls.enabled:
                                continue
                            # Case insensitive compare for plugin name and its Chinese name (if exists)
                            if query_name == name.upper() or \
                               (hasattr(plugincls, 'namecn') and plugincls.namecn and query_name == plugincls.namecn.upper()):
                                ok, result = True, PluginManager().instances[name].get_help_text(isgroup=isgroup, isadmin=isadmin, verbose=True)
                                found_plugin = True
                                break
                        if not found_plugin:
                            ok, result = False, "插件不存在或未启用"
                elif canonical_cmd == "auth":
                    ok, result = self.authenticate(user, args, isadmin, isgroup)
                elif canonical_cmd == "role":
                    if len(args) == 0:
                        # 显示当前角色和可用角色列表
                        current_role = self.get_current_role(session_id)
                        available_roles = list(self.role_map.get("character_desc", {}).keys())
                        
                        if current_role:
                            status_text = f"当前角色：{current_role}\n\n"
                        else:
                            status_text = "当前角色：默认角色（来自config.json）\n\n"
                        
                        if available_roles:
                            role_list = "\n".join([f"- {role}" for role in available_roles])
                            ok, result = True, f"{status_text}可用角色列表：\n{role_list}\n\n使用方法：#role 角色名称"
                        else:
                            ok, result = False, f"{status_text}没有可用的角色设定"
                    elif len(args) == 1:
                        role_name = args[0]
                        # 检查角色是否存在
                        if role_name in self.role_map.get("character_desc", {}):
                            # 获取角色设定
                            character_desc = self.role_map["character_desc"][role_name]
                            
                            # 更新当前会话的系统提示词
                            try:
                                # 获取当前会话并更新系统提示词
                                session = bot.sessions.build_session(session_id, system_prompt=character_desc)
                                ok, result = True, f"角色已切换为: {role_name}"
                                
                                # 记录日志
                                logger.info(f"[Godcmd] User {user} switched role to '{role_name}' in session {session_id}")
                                
                            except Exception as e:
                                logger.error(f"[Godcmd] Error updating session system prompt: {e}")
                                ok, result = False, f"角色切换失败: {str(e)}"
                        else:
                            # 显示可用角色列表作为提示
                            available_roles = list(self.role_map.get("character_desc", {}).keys())
                            if available_roles:
                                role_list = "\n".join([f"- {role}" for role in available_roles])
                                ok, result = False, f"角色 '{role_name}' 不存在\n\n可用角色列表：\n{role_list}"
                            else:
                                ok, result = False, "没有可用的角色设定"
                    else:
                        ok, result = False, "请只提供一个角色名称"
                elif canonical_cmd == "rolelist":
                    available_roles = list(self.role_map.get("character_desc", {}).keys())
                    if available_roles:
                        role_list_text = "可用角色列表：\n"
                        for i, role_name in enumerate(available_roles, 1):
                            role_list_text += f"{i}. {role_name}\n"
                        ok, result = True, role_list_text.strip()
                    else:
                        ok, result = False, "没有可用的角色设定"
                elif canonical_cmd == "reset_role":
                    try:
                        # 获取默认角色设定（来自config.json）
                        default_character_desc = conf().get("character_desc", "")
                        
                        # 获取当前会话并重置系统提示词
                        session = bot.sessions.build_session(session_id, system_prompt=default_character_desc)
                        ok, result = True, "角色已重置为默认角色设定"
                        
                        # 记录日志
                        logger.info(f"[Godcmd] User {user} reset role to default in session {session_id}")
                        
                    except Exception as e:
                        logger.error(f"[Godcmd] Error resetting role to default: {e}")
                        ok, result = False, f"角色重置失败: {str(e)}"
                elif canonical_cmd == "model":
                    if not isadmin and not self.is_admin_in_group(e_context["context"]):
                        ok, result = False, "需要管理员权限执行"
                    elif len(args) == 0:
                        model_val = conf().get("model") or const.GPT35 # Renamed for clarity
                        ok, result = True, "当前模型为: " + str(model_val)
                    elif len(args) == 1:
                        if args[0] not in const.MODEL_LIST:
                            ok, result = False, "模型名称不存在"
                        else:
                            conf()["model"] = self.model_mapping(args[0])
                            Bridge().reset_bot()
                            model_val = conf().get("model") or const.GPT35 # Renamed for clarity
                            ok, result = True, "模型设置为: " + str(model_val)
                elif canonical_cmd == "id":
                    ok, result = True, user
                elif canonical_cmd == "set_openai_api_key":
                    if len(args) == 1:
                        user_data = conf().get_user_data(user)
                        user_data["openai_api_key"] = args[0]
                        ok, result = True, "你的OpenAI私有api_key已设置为" + args[0]
                    else:
                        ok, result = False, "请提供一个api_key"
                elif canonical_cmd == "reset_openai_api_key":
                    try:
                        user_data = conf().get_user_data(user)
                        user_data.pop("openai_api_key")
                        ok, result = True, "你的OpenAI私有api_key已清除"
                    except Exception as e:
                        ok, result = False, "你没有设置私有api_key"
                elif canonical_cmd == "set_gpt_model":
                    if len(args) == 1:
                        user_data = conf().get_user_data(user)
                        user_data["gpt_model"] = args[0]
                        ok, result = True, "你的GPT模型已设置为" + args[0]
                    else:
                        ok, result = False, "请提供一个GPT模型"
                elif canonical_cmd == "gpt_model":
                    user_data = conf().get_user_data(user)
                    model_val = conf().get("model") # Renamed for clarity
                    if "gpt_model" in user_data:
                        model_val = user_data["gpt_model"]
                    ok, result = True, "你的GPT模型为" + str(model_val)
                elif canonical_cmd == "reset_gpt_model":
                    try:
                        user_data = conf().get_user_data(user)
                        user_data.pop("gpt_model")
                        ok, result = True, "你的GPT模型已重置"
                    except Exception as e:
                        ok, result = False, "你没有设置私有GPT模型"
                elif canonical_cmd == "reset":
                    if bottype in [const.OPEN_AI, const.CHATGPT, const.CHATGPTONAZURE, const.LINKAI, const.BAIDU, const.XUNFEI, const.QWEN, const.GEMINI, const.ZHIPU_AI, const.CLAUDEAPI, const.DIFY, const.COZE]:
                        bot.sessions.clear_session(session_id)
                        if Bridge().chat_bots.get(bottype):
                            Bridge().chat_bots.get(bottype).sessions.clear_session(session_id)
                        channel.cancel_session(session_id)
                        ok, result = True, "会话已重置"
                    else:
                        ok, result = False, "当前对话机器人不支持重置会话"
                elif canonical_cmd == "modellist":
                    try:
                        models_file_path = os.path.join(os.path.dirname(__file__), "available_models.json")
                        if not os.path.exists(models_file_path):
                            ok, result = False, "错误：available_models.json 文件未找到。"
                        else:
                            with open(models_file_path, "r", encoding="utf-8") as f:
                                models_data = json.load(f)
                            
                            reply_content = "当前可用模型列表：\n"
                            count = 1
                            for category, models in models_data.items():
                                reply_content += f"\n{count}.{category}系列\n"
                                for model_name in models:
                                    reply_content += f"{model_name}\n"
                                count += 1
                            ok, result = True, reply_content.strip()
                    except json.JSONDecodeError:
                        ok, result = False, "错误：解析 available_models.json 文件失败，请检查JSON格式。"
                    except Exception as e:
                        logger.error(f"[Godcmd] Error processing modellist: {e}")
                        ok, result = False, f"处理 #modellist 指令时发生内部错误: {str(e)[:100]}"
                logger.debug("[Godcmd] command: %s by %s" % (canonical_cmd, user))
            elif any(cmd_alias in info["alias"] for info in ADMIN_COMMANDS.values() for cmd_alias in ([cmd] if isinstance(cmd, str) else cmd)):
                if isadmin:
                    if isgroup: # All admin commands are private chat only by default
                        ok, result = False, "群聊不可执行管理员指令"
                        e_context["reply"] = Reply(ReplyType.ERROR, result)
                        e_context.action = EventAction.BREAK_PASS
                        return # Important to return to prevent further processing

                    canonical_admin_cmd = ""
                    for ac_name, ac_info in ADMIN_COMMANDS.items():
                        if cmd in ac_info["alias"]:
                            canonical_admin_cmd = ac_name
                            break
                    
                    if canonical_admin_cmd == "ahelp":
                        admin_help_items = []
                        admin_help_items.append("管理员专属指令：")
                        for acmd_key, info_val in ADMIN_COMMANDS.items():
                            alias_str = ["#" + a for a in info_val["alias"][:1]]
                            line = f"{','.join(alias_str)} "
                            if "args" in info_val:
                                args_text = [a_arg for a_arg in info_val["args"]]
                                line += f"{' '.join(args_text)}"
                            line += f": {info_val['desc']}"
                            admin_help_items.append(line)
                        ok, result = True, "\n".join(admin_help_items)
                    elif canonical_admin_cmd == "stop":
                        self.isrunning = False
                        ok, result = True, "服务已暂停"
                    elif canonical_admin_cmd == "resume":
                        self.isrunning = True
                        ok, result = True, "服务已恢复"
                    elif canonical_admin_cmd == "reconf":
                        load_config()
                        ok, result = True, "配置已重载"
                    elif canonical_admin_cmd == "resetall":
                        if bottype in [const.OPEN_AI, const.CHATGPT, const.CHATGPTONAZURE, const.LINKAI, const.DIFY, const.COZE,
                                       const.BAIDU, const.XUNFEI, const.QWEN, const.GEMINI, const.ZHIPU_AI, const.MOONSHOT,
                                       const.MODELSCOPE]:
                            channel.cancel_all_session()
                            bot.sessions.clear_all_session()
                            ok, result = True, "重置所有会话成功"
                        else:
                            ok, result = False, "当前对话机器人不支持重置会话"
                    elif canonical_admin_cmd == "debug":
                        if logger.getEffectiveLevel() == logging.DEBUG:  # 判断当前日志模式是否DEBUG
                            logger.setLevel(logging.INFO)
                            ok, result = True, "DEBUG模式已关闭"
                        else:
                            logger.setLevel(logging.DEBUG)
                            ok, result = True, "DEBUG模式已开启"
                    elif canonical_admin_cmd == "plist":
                        plugins = PluginManager().list_plugins()
                        ok = True
                        result = "插件列表：\n"
                        for name, plugincls in plugins.items():
                            result += f"{plugincls.name}_v{plugincls.version} {plugincls.priority} - "
                            if plugincls.enabled:
                                result += "已启用\n"
                            else:
                                result += "未启用\n"
                    elif canonical_admin_cmd == "scanp":
                        new_plugins = PluginManager().scan_plugins()
                        ok, result = True, "插件扫描完成"
                        PluginManager().activate_plugins()
                        if len(new_plugins) > 0:
                            result += "\n发现新插件：\n"
                            result += "\n".join([f"{p.name}_v{p.version}" for p in new_plugins])
                        else:
                            result += ", 未发现新插件"
                    elif canonical_admin_cmd == "setpri":
                        if len(args) != 2:
                            ok, result = False, "请提供插件名和优先级"
                        else:
                            ok = PluginManager().set_plugin_priority(args[0], int(args[1]))
                            if ok:
                                result = "插件" + args[0] + "优先级已设置为" + args[1]
                            else:
                                result = "插件不存在"
                    elif canonical_admin_cmd == "reloadp":
                        if len(args) != 1:
                            ok, result = False, "请提供插件名"
                        else:
                            ok = PluginManager().reload_plugin(args[0])
                            if ok:
                                result = "插件配置已重载"
                            else:
                                result = "插件不存在"
                    elif canonical_admin_cmd == "enablep":
                        if len(args) != 1:
                            ok, result = False, "请提供插件名"
                        else:
                            ok, result = PluginManager().enable_plugin(args[0])
                    elif canonical_admin_cmd == "disablep":
                        if len(args) != 1:
                            ok, result = False, "请提供插件名"
                        else:
                            ok = PluginManager().disable_plugin(args[0])
                            if ok:
                                result = "插件已禁用"
                            else:
                                result = "插件不存在"
                    elif canonical_admin_cmd == "installp":
                        if len(args) != 1:
                            ok, result = False, "请提供插件名或.git结尾的仓库地址"
                        else:
                            ok, result = PluginManager().install_plugin(args[0])
                    elif canonical_admin_cmd == "uninstallp":
                        if len(args) != 1:
                            ok, result = False, "请提供插件名"
                        else:
                            ok, result = PluginManager().uninstall_plugin(args[0])
                    elif canonical_admin_cmd == "updatep":
                        if len(args) != 1:
                            ok, result = False, "请提供插件名"
                        else:
                            ok, result = PluginManager().update_plugin(args[0])
                    logger.debug("[Godcmd] admin command: %s by %s" % (canonical_admin_cmd, user))
                else:
                    ok, result = False, "需要管理员权限才能执行该指令"
            else:
                trigger_prefix = conf().get("plugin_trigger_prefix", "$")
                if trigger_prefix == "#":  # 跟插件聊天指令前缀相同，继续递交
                    return
                ok, result = False, f"未知指令：{cmd}\n查看指令列表请输入#help \n"

            reply = Reply()
            if ok:
                reply.type = ReplyType.INFO
            else:
                reply.type = ReplyType.ERROR
            reply.content = result
            e_context["reply"] = reply

            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑
        elif not self.isrunning:
            e_context.action = EventAction.BREAK_PASS

    def authenticate(self, userid, args, isadmin, isgroup) -> Tuple[bool, str]:
        if isgroup:
            return False, "请勿在群聊中认证"

        if isadmin:
            return False, "管理员账号无需认证"

        if len(args) != 1:
            return False, "请提供口令"

        password = args[0]
        if password == self.password:
            self.admin_users.append(userid)
            global_config["admin_users"].append(userid)
            return True, "认证成功"
        elif password == self.temp_password:
            self.admin_users.append(userid)
            global_config["admin_users"].append(userid)
            return True, "认证成功，请尽快设置口令"
        else:
            return False, "认证失败"

    def get_help_text(self, isadmin=False, isgroup=False, **kwargs):
        help_text = get_help_text(isadmin, isgroup)
        
        # 添加角色切换相关的帮助信息
        if hasattr(self, 'role_map') and self.role_map.get("character_desc"):
            help_text += "\n\n角色切换功能："
            help_text += "\n#role - 显示当前角色和可用角色列表"
            help_text += "\n#rolelist - 显示按序号排列的角色列表"
            help_text += "\n#role 角色名称 - 切换到指定角色"
            help_text += "\n#reset_role - 重置为默认角色设定"
            
            # 显示可用角色列表
            available_roles = list(self.role_map["character_desc"].keys())
            if available_roles:
                help_text += f"\n\n可用角色：{', '.join(available_roles)}"
        
        return help_text

    def get_current_role(self, session_id):
        """
        获取当前会话的角色设定
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: 当前角色名称，如果没有设置则返回None
        """
        try:
            # 获取当前会话
            bot = Bridge().get_bot("chat")
            if bot and hasattr(bot, 'sessions'):
                session = bot.sessions.build_session(session_id)
                if session and session.system_prompt:
                    # 检查当前系统提示词是否匹配某个角色设定
                    for role_name, character_desc in self.role_map.get("character_desc", {}).items():
                        if session.system_prompt == character_desc:
                            return role_name
            return None
        except Exception as e:
            logger.error(f"[Godcmd] Error getting current role: {e}")
            return None

    def is_admin_in_group(self, context):
        if context["isgroup"]:
            return context.kwargs.get("msg").actual_user_id in global_config["admin_users"]
        return False


    def model_mapping(self, model) -> str:
        if model == "gpt-4-turbo":
            return const.GPT4_TURBO_PREVIEW
        return model

    def reload(self):
        gconf = pconf(self.name)
        if gconf:
            if gconf.get("password"):
                self.password = gconf["password"]
            if gconf.get("admin_users"):
                self.admin_users = gconf["admin_users"]
