# WeChat MCP Skill

微信MCP增强版 - 支持文件发送、语音消息、语音通话

## 功能特性

- ✅ **发送文本消息** - 给任意联系人发送文字
- ✅ **发送文件** - 支持任意类型文件传输
- ✅ **发送语音消息** - 发送音频文件（mp3/wav等）
- ✅ **语音通话** - 发起/接听/结束微信语音通话
- ✅ **音频格式转换** - 支持mp3/wav/silk互转

## 安装要求

### 系统要求
- Windows 10/11
- 微信PC版（已登录）
- Python 3.10+

### 安装依赖

```bash
pip install pyautogui pygetwindow pyperclip pywin32 Pillow
```

### 可选依赖（音频转换）
```bash
pip install ffmpeg-python
# 同时需要安装ffmpeg并添加到PATH
```

## 使用方法

### 1. 启动服务器

```bash
cd C:\mcp\winautowx
python server.py
```

### 2. MCP配置

在Claude Desktop配置文件中添加：

```json
{
  "mcpServers": {
    "wechat": {
      "command": "python",
      "args": ["C:\\mcp\\winautowx\\server.py"]
    }
  }
}
```

### 3. 使用工具

#### 发送文本消息
```json
{
  "name": "wechat_send_message",
  "arguments": {
    "contact": "联系人名称",
    "message": "消息内容"
  }
}
```

#### 发送文件
```json
{
  "name": "wechat_send_file",
  "arguments": {
    "contact": "联系人名称",
    "file_path": "C:\\path\\to\\file.pdf",
    "message": "附带消息（可选）"
  }
}
```

#### 发送语音
```json
{
  "name": "wechat_send_voice",
  "arguments": {
    "contact": "联系人名称",
    "audio_path": "C:\\path\\to\\voice.mp3"
  }
}
```

#### 发起语音通话
```json
{
  "name": "wechat_start_call",
  "arguments": {
    "contact": "联系人名称"
  }
}
```

#### 结束通话
```json
{
  "name": "wechat_end_call",
  "arguments": {
    "call_id": "通话ID"
  }
}
```

## 注意事项

1. **微信必须保持登录状态**
2. **发送文件时请勿操作鼠标** - 脚本会自动控制鼠标进行文件复制粘贴
3. **窗口可见性** - 微信窗口可以最小化，但建议保持可见以便观察
4. **文件路径** - 使用双反斜杠或原始字符串：`C:\\path\\file.txt` 或 `r"C:\path\file.txt"`

## 故障排除

### 文件发送失败
- 检查文件路径是否正确
- 确保微信窗口未被其他窗口完全遮挡
- 重新启动server.py重试

### 找不到微信窗口
- 确保微信PC版已启动并登录
- 检查微信窗口标题是否为"微信"

### 中文乱码
- 确保文件使用UTF-8编码
- 使用环境变量传递中文参数

## 技术架构

```
wechat-mcp/
├── server.py           # MCP服务器主程序
├── requirements.txt    # Python依赖
└── SKILL.md           # 本说明文档
```

## 版本历史

- **v5.0** - 文件发送功能稳定，使用复制粘贴方式
- **v4.0** - 新增文件、语音、通话功能
- **v3.0** - 基础文本消息发送

## 源码

https://github.com/chylove1982/wechat-mcp-enhanced

## License

MIT
