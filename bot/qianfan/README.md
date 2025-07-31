# 百度千帆聊天机器人

## 功能说明

本模块实现了与百度千帆平台的集成，提供AI聊天机器人功能。支持多轮对话、会话管理和错误重试等特性。

## 文件结构

- `qianfan_bot.py` - 千帆机器人主实现类
- `qianfan_session.py` - 会话管理类
- `__init__.py` - 模块初始化文件
- `README.md` - 使用说明文档

## 配置参数

在 `config.json` 中需要配置以下参数：

```json
{
  "bot_type": "qianfan",
  "qianfan_api_base": "https://qianfan.baidubce.com/v2",
  "qianfan_app_id": "你的应用ID",
  "qianfan_api_key": "你的API密钥",
  "conversation_max_tokens": 2000,
  "expires_in_seconds": 1600
}
```

### 配置说明

- `bot_type`: 设置为 "qianfan" 启用千帆机器人
- `qianfan_api_base`: 千帆API基础URL
- `qianfan_app_id`: 在千帆平台创建的应用ID
- `qianfan_api_key`: 千帆平台的API密钥
- `conversation_max_tokens`: 单次对话最大token数量（可选）
- `expires_in_seconds`: 会话过期时间（可选）

## API调用流程

### 1. 创建对话
首次对话时会调用创建对话接口：
```
POST https://qianfan.baidubce.com/v2/app/conversation
```

### 2. 发送消息
使用对话ID发送用户消息：
```
POST https://qianfan.baidubce.com/v2/app/conversation/runs
```

## 核心功能

### QianfanBot 主要方法

- `reply(query, context)` - 处理用户查询并返回AI回复
- `reset_conversation(session_id)` - 重置指定会话的对话状态
- `clear_session(session_id)` - 清除指定会话
- `clear_all_sessions()` - 清除所有会话

### QianfanSession 主要方法

- `get_conversation_id()` - 获取千帆对话ID
- `set_conversation_id(conversation_id)` - 设置千帆对话ID
- `reset_conversation()` - 重置对话状态
- `calc_tokens()` - 计算会话token使用量

## 错误处理

- 自动重试机制：API调用失败时会自动重试最多2次
- 配置验证：启动时会验证必要的配置参数
- 详细日志：记录API调用过程和错误信息

## 使用示例

在你的配置中设置千帆相关参数后，机器人会自动使用千帆平台进行对话。用户发送消息时，系统会：

1. 检查是否已有对话ID，没有则创建新对话
2. 将用户消息发送到千帆平台
3. 解析千帆返回的回复内容
4. 返回格式化的回复给用户
5. 更新会话历史记录

## 注意事项

1. 确保千帆平台的API密钥有效且有足够的调用额度
2. 千帆平台的响应时间可能较长，已设置60秒超时
3. 会话状态会在本地保存，重启后会丢失
4. Token统计基于字符数量估算，非精确计算

## 故障排除

### 常见错误

1. **配置缺失**: 检查 `config.json` 中是否包含所有必要的千帆配置参数
2. **API调用失败**: 检查网络连接和API密钥是否正确
3. **超时错误**: 千帆平台响应较慢，可以增加超时时间设置
4. **会话丢失**: 重启应用后会话会重置，这是正常现象

### 日志查看

启用 DEBUG 日志级别可以看到详细的API调用过程：
```json
{
  "log_level": "DEBUG",
  "debug": true
}
```

## 开发说明

本模块参考了 `bytedance_coze_bot.py` 的实现模式，采用相同的设计原则：

- 继承自基础 `Bot` 类
- 使用专用的会话管理器
- 实现统一的错误处理机制
- 提供详细的日志记录