# WeChat MCP Enhanced

微信MCP增强版，支持文件发送、语音接收/发送、语音通话功能。

## 功能特性

- 📁 **文件发送** - 支持发送各类文件给微信好友/群聊
- 🎙️ **语音收发** - 支持发送和接收语音消息（自动格式转换）
- 📞 **语音通话** - 支持发起和接听微信语音通话
- 🤖 **MCP协议** - 符合Model Context Protocol标准

## 安装

```bash
# 克隆仓库
git clone https://github.com/mikewangmax/wechat-mcp-enhanced.git
cd wechat-mcp-enhanced

# 安装依赖
pip install -r requirements.txt

# Windows额外依赖（语音通话需要）
# 需要安装微信PC版并登录
```

## 配置

1. 复制配置模板：
```bash
cp config/settings.example.py config/settings.py
```

2. 编辑 `config/settings.py`，填入你的配置

## 使用

### 启动服务器

```bash
python src/server.py
```

### MCP Tools

#### 文件相关
- `send_file(target_user, file_path)` - 发送文件
- `receive_file(message_id, save_path)` - 接收文件

#### 语音相关
- `send_voice(target_user, audio_path)` - 发送语音消息
- `receive_voice(message_id, save_path)` - 接收语音消息
- `convert_audio(input_path, output_format)` - 音频格式转换

#### 通话相关
- `start_voice_call(target_user)` - 发起语音通话
- `end_voice_call(call_id)` - 结束语音通话
- `get_call_status(call_id)` - 获取通话状态

## 技术架构

```
wechat-mcp-enhanced/
├── src/
│   ├── server.py              # MCP服务器主入口
│   ├── wechat_client.py       # 微信客户端封装
│   └── handlers/
│       ├── file_handler.py    # 文件处理
│       ├── voice_handler.py   # 语音处理
│       └── call_handler.py    # 通话处理
├── config/
│   └── settings.py            # 配置文件
└── tests/                     # 测试用例
```

## 注意事项

1. **Windows环境**：语音通话功能需要Windows系统和微信PC版
2. **登录状态**：使用前需要确保微信PC版已登录
3. **权限**：部分功能可能需要管理员权限

## License

MIT License

## 贡献

欢迎提交Issue和PR！
