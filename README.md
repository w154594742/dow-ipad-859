# 微信机器人项目 - 基于859协议的智能对话系统

## 项目概述

本项目是一个基于859版iPad协议的微信机器人项目，集成了dify-on-wechat聊天机器人框架，实现智能对话功能。项目支持在Windows系统本地部署，提供完整的微信消息收发、AI对话、图片识别等功能。

## 最新更新 (2025-06-23)

## 快速开始

### 1. 环境准备
```bash
# 确保Python 3.8+环境
python --version

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-optional.txt
```

### 2. 启动WX859协议服务
```bash
# 启动Redis服务
cd lib/wx859/859/win/redis
./redis-server.exe

# 启动WX859协议服务
cd lib/wx859/859/win
./wxapi_win64_v1_0_4.exe
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
```bash
python app.py
```

### 5. 扫码登录
- 程序启动后会显示二维码
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
