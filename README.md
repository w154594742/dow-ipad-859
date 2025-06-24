# 微信机器人项目 - 基于859协议的智能对话系统

## 项目概述

本项目是一个基于859版iPad协议的微信机器人项目，集成了dify-on-wechat聊天机器人框架，实现智能对话功能。项目支持在Windows系统本地部署，提供完整的微信消息收发、AI对话、图片识别等功能。

## 最新更新 (2025-06-23)

## 快速开始

### 1. 环境准备
```bash
# 确保Python 3.8+环境，建议使用Python 3.11以上版本
python --version

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-optional.txt
```

### 2. 配置机器人
编辑 `config.json`:
```json
{
  "dify_api_base": "https://api.dify.ai/v1",
  "dify_api_key": "your-dify-api-key",
  "channel_type": "wx859",
  "wx859_api_host": "127.0.0.1",
  "wx859_api_port": 8059
}
```

### 3. 启动机器人

#### Windows 用户
```bash
1. 进入`lib\wx859\859\redis`目录，双击`redis-server.exe`启动redis服务
2. 进入`lib\wx859\859\win`目录，双击`wxapi_win64_v1_0_5.exe`启动 WX859 协议服务
3. 进入项目根目录，右键`在终端中打开`，执行`python app.py`启动主程序
4. 保活机制：以上三个窗口均需保持开启
```
#### Linux/macOS 用户
```bash
1. 进入项目根目录：`/root/dow-ipad-859`
2. 赋予脚本执行权限：`chmod +x scripts/wx859_start.sh`
3. 执行 `./scripts/wx859_start.sh` 脚本启动 WX859 协议服务
4. 等待服务完全启动后使用 `python3 app.py` 启动主程序

5.保活机制：
tmux kill-session -t dify                  # 杀掉tmux旧进程      
tmux new -s dify                           # 启动tmux新进程                 
./scripts/wx859_start.sh                   # 后台运行脚本           
tmux attach -t dify                        # 重连时恢复(正常无需这一步)                 
pkill -f "python3 app.py"                  # 杀掉app.py旧进程     
nohup python3 app.py & tail -f nohup.out   #挂载运行app.py进程 
```
### 4. 扫码登录
- 程序第一次启动后会显示二维码
- 使用微信扫码登录
- 登录成功后自动开始消息监听

## 功能特性

### ✅ 已实现功能
- **微信登录**: 扫码登录、自动登录、唤醒登录
- **消息处理**: 文本消息、图片消息、语音消息
- **智能对话**: 基于Dify的AI对话引擎
- **群聊支持**: 群消息处理、@机器人触发
- **图片识别**: 支持图片内容识别和描述
- **语音处理**: 语音转文字、文字转语音
- **Web界面**: 基于Gradio的管理界面

### 🔧 技术特性
- **异步处理**: 基于asyncio的高性能消息处理
- **错误恢复**: 自动重连、登录状态检测
- **缓存机制**: 群信息缓存、图片缓存
- **日志系统**: 详细的运行日志和错误追踪

## 配置说明

### 核心配置项
```json
{
  "channel_type": "wx859",
  "wx859_api_host": "127.0.0.1",
  "wx859_api_port": 8059,
  "wx859_protocol_version": "859",
  "wx859_sync_interval": 5,
  "log_level": "INFO"
}
```
复制`config-template.json`为`config.json`，并修改关键配置，支持dify、coze、qwen、硅基免费模型等自定义LLM选项：

```json
{
  "dify_api_base": "https://api.dify.ai/v1",
  "dify_api_key": "app-xxxx",                     # 选填
  "dify_app_type": "chatflow",                    # 支持chatbot，agent，workflow，chatflow
  "channel_type": "wx859",
  "wx849_api_host": "127.0.0.1",                  # 微信859协议API地址
  "wx849_api_port": 8059,                         # 微信859协议API端口
  "wx849_protocol_version": "859",                # 微信859协议版本
  "log_level": "INFO",                            # 默认开启的日志级别
  "debug": true ,
  "group_chat_prefix": ["xy","晓颜","@晓颜"],     # 改成你自己的bot昵称
  "group_name_white_list": [
        "测试群1",
        "测试群2",
        "测试群3"],                               # 全开的话改成"ALL GROUP"
  "single_ignore_blacklist": ["wxid_1234567890"], # 改成你想屏蔽的私聊名单
  "image_recognition": true,
  "speech_recognition": false,
  "voice_reply_voice": false,
  "voice_to_text": "dify",
  "text_to_voice": "dify",
  "character_desc": "你是一个通用人工智能助手",   # 改成你自己的人设提示词
  "conversation_max_tokens": 500,
  "coze_api_base": "https://api.coze.cn/open_api/v2",
  "coze_api_key": "",                            # 选填
  "coze_bot_id": "",                             # 选填
  "dashscope_api_key": "",                       # 选填
  "deepseek_api_base": "https://api.deepseek.com/v1",
  "deepseek_api_key": "",                        # 选填
  "expires_in_seconds": 1600,
  "group_speech_recognition": false,
  "model": "qwen-max",                           # 改成你自己的默认模型
  "no_need_at": true,
  "siliconflow_api_base": "https://api.siliconflow.cn/v1/chat/completions",
  "siliconflow_api_key": "",                     # 选填
  "siliconflow_model": "deepseek-ai/DeepSeek-V3",
  "single_chat_prefix": [""],                    # 选填
  "single_chat_reply_prefix": "",                # 选填
  "temperature": 0.5,
  "zhipu_ai_api_base": "https://open.bigmodel.cn/api/paas/v4",
  "zhipu_ai_api_key": "",                        # 选填
  "zhipuai_model": "glm-4-flash-250414"  
}
```

