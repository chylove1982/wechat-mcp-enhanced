# 🎉 WeChat MCP Skill v5.0 发布

## 📦 发布内容

**GitHub仓库**: https://github.com/chylove1982/wechat-mcp-enhanced

**核心功能**:
- ✅ 文本消息发送
- ✅ 文件发送（已测试成功）
- ✅ 语音消息发送
- ✅ 语音通话（发起/接听/结束）
- ✅ 音频格式转换

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/chylove1982/wechat-mcp-enhanced.git
cd wechat-mcp-enhanced
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动服务器
```bash
python server.py
```

### 4. 配置MCP
在Claude Desktop配置中添加:
```json
{
  "mcpServers": {
    "wechat": {
      "command": "python",
      "args": ["C:\\path\\to\\wechat-mcp-enhanced\\server.py"]
    }
  }
}
```

## 📋 使用示例

**发送文件**:
```
使用工具 wechat_send_file
- contact: "联系人名称"
- file_path: "C:\\path\\to\\file.pdf"
- message: "请查收文件"
```

**发送语音**:
```
使用工具 wechat_send_voice
- contact: "联系人名称"  
- audio_path: "C:\\path\\to\\voice.mp3"
```

**语音通话**:
```
使用工具 wechat_start_call
- contact: "联系人名称"
```

## ⚠️ 使用注意

1. 微信PC版必须已登录
2. 发送文件时请勿操作鼠标
3. 首次使用建议先用"文件传输助手"测试

## 📁 文件结构

```
wechat-mcp-enhanced/
├── server.py           # 主程序 (v5.0)
├── SKILL.md           # 使用说明
├── requirements.txt   # 依赖列表
└── README.md          # 项目说明
```

## 🔄 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v5.0 | 2026-03-04 | 文件发送功能稳定版 |
| v4.0 | 2026-03-04 | 新增文件/语音/通话功能 |
| v3.0 | 2026-03-03 | 基础消息发送 |

## 📞 问题反馈

如有问题请在GitHub Issues中反馈。

---
**发布者**: @chylove1982  
**发布时间**: 2026-03-04
