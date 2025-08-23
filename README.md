# 微信机器人项目 - 基于859协议

## 一、项目概述

本项目是一个基于859版iPad协议的微信机器人项目，集成了dify-on-wechat聊天机器人框架，实现智能对话功能。项目支持在Windows系统本地部署，提供完整的微信消息收发、AI对话、图片识别等功能。

### 更新日志
```bash
- **2025-08-23更新内容** 
新增支持魔搭平台的推理API，如最新的DeepSeek-V3.1/Kimi-K2-Instruct/GLM-4.5等开源模型，每天可免费对话2000次；
需更新文件：const.py、config.py、bridge.py、bot_factory.py、modelscope_bot.py这五个文件以支持模型切换；
然后在全局config.json文件中增加"modelscope_api_base"、"modelscope_model"、"modelscope_api_key"等参数配置即可
使用方法：#model deepseek-ai/DeepSeek-V3.1、#model moonshotai/Kimi-K2-Instruct、#model ZhipuAI/GLM-4.5
(想要使用以上切换指令需同步更新godcmd插件目录下的available_models.json文件)

- **2025-08-23更新内容** 
新增角色切换功能，可以在同一模型之下一键切换不同的系统提示词以应对不同对话需求

- **2025-07-31更新内容** 
新增支持百度千帆的智能体，功能与coze类似，原生支持百度搜索、百度百科、图片生成等组件；
只需在dow-ipad-859/bot/qianfan目录下上传最新的qianfan_bot.py等核心文件；
同时需更新文件：const.py、config.py、bot_factory.py这三个文件以支持模型切换；
然后在全局config.json文件中增加"qianfan_api_base"、"qianfan_app_id"、"qianfan_api_key"等参数配置即可
使用方法：#model qianfan
(想要使用以上切换指令需同步更新godcmd插件目录下的available_models.json文件)
```
- **更新示例**
- 2025-08-23
<img width="550" height="400" alt="04cb981c-1a0f-42c9-9061-c09fa3072005" src="https://github.com/user-attachments/assets/a4c3b21e-34c7-437a-9180-0b7fc3725bbc" />
<img width="480" height="400" alt="image" src="https://github.com/user-attachments/assets/4f4f4de2-40f2-4083-9848-ec1e045d20dc" />
<img width="480" height="507" alt="image" src="https://github.com/user-attachments/assets/9aadf7e0-0425-4acc-9310-6f728ebe0ede" />
<img width="480" height="440" alt="image" src="https://github.com/user-attachments/assets/1e955441-90c7-4cc3-a69c-475a12d7db6a" />

- 2025-07-31
<img width="839" height="639" alt="image" src="https://github.com/user-attachments/assets/6ee63a30-13d9-47e0-b7b1-c40d81db774e" />
<img width="839" height="590" alt="583e558a-46ff-4755-b9c7-f023d9531a80" src="https://github.com/user-attachments/assets/c3590f38-e642-4a72-9c33-5fcd9a756aea" />
   
### 功能特性

- **多协议支持**: 支持859(暂时仅支持iPad，mac、car有需求再补充)
- **多样化交互**: 支持文本、图片、语音、视频、卡片等多种消息类型
- **智能对话**: 对接dify、coze、qwen、openai、siliconflow等自定义API，提供多种智能对话服务
- **灵活配置**: 支持白名单、黑名单等多样化配置
- **高稳定性**: 基于成熟的WX859协议，连接稳定，功能丰富

### 核心配置说明

复制`config-template.json`为`config.json`，并修改关键配置，支持dify、coze、qwen、openai、siliconflow模型等自定义LLM选项：

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
  "qianfan_api_base": "https://qianfan.baidubce.com/v2",
  "qianfan_app_id": "",                          # 新增千帆智能体，需自行配置相关token
  "qianfan_api_key": "",                         # 新增千帆智能体，需自行配置相关token
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

```bash
在wx859_device_info.json中配置登录账号的wxid
(其他两样不用管，会自动生成)
```

## 二、快速开始

### 1. 下载源码

```bash
# 确保Python 3.8+环境，建议使用Python 3.11以上版本
cd root
git clone https://github.com/Lingyuzhou111/dow-ipad-859.git
cd root/dow-ipad-859
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt
```

### 3. 配置机器人
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

### 4. 启动机器人

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

5.保活机制(不懂原理的可以问问deepseek)：
sudo yum install tmux -y                   # 安装 tmux（若未安装）
tmux kill-session -t dify                  # 杀掉tmux旧进程      
tmux new -s dify                           # 启动tmux新进程                 
./scripts/wx859_start.sh                   # 后台运行脚本           
tmux attach -t dify                        # 重连时恢复(正常无需这一步)                 
pkill -f "python3 app.py"                  # 杀掉app.py旧进程     
nohup python3 app.py & tail -f nohup.out   # 挂载运行app.py进程 
```
### 5. 扫码登录
- 程序第一次启动后会显示二维码
- 使用微信扫码登录
- 登录成功后自动开始消息监听

## 三、常见问题

### 服务无法启动
- 检查Redis是否运行
- 检查端口是否被占用
- 检查授权码是否过期
- 检查协议启动文件大小(正常应为30M左右)，如出现以下情况请重新手动下载替换
  ![微信图片_2025-07-02_214250_574](https://github.com/user-attachments/assets/3c38d2ed-1cd6-47aa-8b1a-8923df382503)
  ![微信图片_2025-07-02_214323_904](https://github.com/user-attachments/assets/6b0f6972-743f-4a62-a987-1aa7aa8b0840)

### 登录问题
- 确保网络稳定
- 尝试重启服务
- 更换协议版本

### 注意事项
- WX859协议为非官方实现，可能随微信更新而需要调整
- 建议使用备用微信账号进行测试
- 避免频繁登录/登出操作，防止触发风控
- 定期更新代码以获取最新功能和修复

### 特别声明
- 本项目框架代码开源，但协议本身并未开源，由DPbot作者提供
- 新设备第一次登录自动生成缘分(授权)码 ，可免费体验30天
- 授权码过期需联系协议作者

### 详细教程
https://rq4rfacax27.feishu.cn/wiki/ULM8waMdEiVfw3kmyS4cixIBnEh?from=from_copylink

### 交流群

欢迎进入交流群共同讨论学习，若群二维码过期可以加我个微备注“BOT”拉你进群
![8ef46463c0871be01e51a3a99848b7ed](https://github.com/user-attachments/assets/e88ba6ca-9622-4144-aa50-417597a11bdf)
![0d9634a39fb17e2b0d2119f89249640f](https://github.com/user-attachments/assets/69083353-7b59-44ca-86e9-5f6e98ded3fd)






