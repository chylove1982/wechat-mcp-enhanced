# 微信聊天记录监听与自动回复系统 - 设计方案

## 系统架构

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   微信PC版      │────▶│  消息监听模块    │────▶│   数据库        │
│  (UI自动化)     │     │  (截图/OCR/内存) │     │  (SQLite/JSON)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                           │
                               ▼                           ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │   MCP Server     │◀────│  历史记录查询   │
                        │  (新增接口)      │     │                 │
                        └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   自动回复引擎   │
                        │  (规则/AI)      │
                        └──────────────────┘
```

## 核心功能模块

### 1. 消息监听模块 (`message_listener.py`)

**实现方式**:
- **方案A**: 定时截图 + OCR识别新消息
- **方案B**: 读取微信内存/日志（需要反向工程，难度大）
- **方案C**: 微信Windows API Hook（复杂，风险高）

**推荐方案A**（稳定可控）：
- 每2-5秒截图聊天区域
- OCR识别文字内容
- 对比历史记录检测新消息

```python
class MessageListener:
    def __init__(self, db_path="chat_history.db"):
        self.db = ChatDatabase(db_path)
        self.last_messages = {}  # 每个联系人的最后消息
        
    def start_listening(self, interval=3):
        """开始监听循环"""
        while True:
            self.check_new_messages()
            time.sleep(interval)
    
    def check_new_messages(self):
        """检查新消息"""
        # 1. 获取当前聊天窗口
        # 2. 截图消息区域
        # 3. OCR识别所有消息
        # 4. 对比数据库，找出新消息
        # 5. 存储到数据库
        # 6. 触发自动回复（如果开启）
```

### 2. 数据库设计 (`database.py`)

**SQLite 表结构**:

```sql
-- 聊天记录表
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_name TEXT NOT NULL,      -- 联系人名称
    sender TEXT NOT NULL,            -- 发送者（"me"或对方名称）
    message_type TEXT,               -- text/file/image/voice
    content TEXT,                    -- 消息内容（文本或文件路径）
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT 0,       -- 是否已读
    reply_to INTEGER,                -- 回复哪条消息（外键）
    session_id TEXT                  -- 会话ID，用于分组
);

-- 联系人表
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,       -- 联系人名称
    nickname TEXT,                   -- 昵称
    remark TEXT,                     -- 备注
    last_message_time DATETIME,      -- 最后消息时间
    unread_count INTEGER DEFAULT 0,  -- 未读消息数
    auto_reply_enabled BOOLEAN DEFAULT 0,  -- 是否开启自动回复
    auto_reply_rules TEXT            -- 自动回复规则（JSON）
);

-- 会话上下文表（用于AI对话）
CREATE TABLE chat_sessions (
    session_id TEXT PRIMARY KEY,
    contact_name TEXT NOT NULL,
    context_window INTEGER DEFAULT 10,  -- 保留最近N条消息
    system_prompt TEXT,                 -- 系统提示词
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3. MCP工具扩展

**新增Tools**:

```python
# 查询历史记录
{
    "name": "wechat_get_chat_history",
    "description": "获取与某联系人的聊天记录",
    "inputSchema": {
        "contact": "联系人名称",
        "limit": 50,           # 返回最近N条
        "offset": 0,           # 分页
        "start_time": "2026-03-01 00:00:00",  # 可选时间范围
        "end_time": "2026-03-04 23:59:59"
    }
}

# 获取未读消息
{
    "name": "wechat_get_unread_messages",
    "description": "获取所有未读消息",
    "inputSchema": {
        "contact": "可选，指定联系人",
        "mark_as_read": true   # 是否标记为已读
    }
}

# 设置自动回复规则
{
    "name": "wechat_set_auto_reply",
    "description": "为联系人设置自动回复",
    "inputSchema": {
        "contact": "联系人名称",
        "enabled": true,
        "rules": [
            {"keyword": "在吗", "response": "在的，请说"},
            {"keyword": "*", "response": "【自动回复】我现在不方便，稍后回复您"}
        ],
        "ai_mode": false,      # 是否使用AI回复
        "context_window": 5    # AI模式下的上下文窗口
    }
}

# 获取联系人列表（带未读数）
{
    "name": "wechat_get_contact_list",
    "description": "获取联系人列表及未读消息数",
    "inputSchema": {}
}

# 开始监听消息
{
    "name": "wechat_start_listener",
    "description": "开始监听新消息",
    "inputSchema": {
        "contacts": ["all"],   # 或指定联系人列表
        "auto_reply": false,   # 是否自动回复
        "interval": 3          # 检查间隔（秒）
    }
}

# 停止监听
{
    "name": "wechat_stop_listener",
    "description": "停止监听消息",
    "inputSchema": {}
}
```

### 4. 自动回复引擎 (`auto_reply.py`)

**规则模式**:
```python
class AutoReplyEngine:
    def __init__(self, db):
        self.db = db
        
    def handle_message(self, contact, message):
        """处理收到的消息"""
        # 1. 查询该联系人的自动回复规则
        rules = self.db.get_auto_reply_rules(contact)
        
        if not rules or not rules['enabled']:
            return None
            
        # 2. 规则匹配
        if rules['mode'] == 'keyword':
            for rule in rules['rules']:
                if self.match_keyword(message, rule['keyword']):
                    return rule['response']
                    
        # 3. AI模式（调用外部AI）
        elif rules['mode'] == 'ai':
            context = self.db.get_recent_context(contact, rules['context_window'])
            return self.call_ai_reply(contact, message, context)
            
        return None
```

### 5. OCR消息识别 (`message_ocr.py`)

**使用 PaddleOCR 或 Tesseract**:

```python
class MessageOCR:
    def __init__(self):
        # 初始化OCR引擎
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        
    def extract_messages(self, image_path):
        """从截图中提取消息"""
        result = self.ocr.ocr(image_path, cls=True)
        
        messages = []
        for line in result:
            text = line[1][0]  # 识别文字
            confidence = line[1][1]  # 置信度
            
            if confidence > 0.8:  # 过滤低置信度
                messages.append({
                    'text': text,
                    'position': line[0],  # 位置信息（用于区分左右，判断收发）
                    'confidence': confidence
                })
                
        return messages
```

## 关键技术点

### 1. 区分发送/接收消息
通过消息气泡位置判断：
- 左侧气泡 = 对方发送
- 右侧气泡 = 自己发送

### 2. 避免重复记录
- 使用消息内容+时间戳的哈希作为唯一键
- 或对比最后N条消息内容

### 3. 性能优化
- 只截图消息区域（而非整个窗口）
- 增量OCR（只识别变化区域）
- 数据库索引优化

### 4. 错误处理
- 微信窗口被关闭时自动重连
- OCR失败时的重试机制
- 数据库写入失败时的队列缓冲

## 实现步骤

### Phase 1: 基础数据库和MCP接口
1. 创建数据库模块
2. 实现历史记录查询接口
3. 测试数据写入/读取

### Phase 2: 消息监听
1. 实现截图功能
2. 集成OCR识别
3. 新消息检测逻辑

### Phase 3: 自动回复
1. 规则引擎实现
2. 自动回复触发
3. 上下文管理

### Phase 4: 优化
1. 性能优化
2. 错误处理完善
3. 配置界面（可选）

## 代码结构

```
wechat-mcp/
├── server.py                 # MCP服务器主入口
├── database.py              # 数据库操作
├── message_listener.py      # 消息监听
├── message_ocr.py          # OCR识别
├── auto_reply.py           # 自动回复引擎
├── chat_history.db         # SQLite数据库
└── config.json             # 配置文件
```

## 使用场景

1. **客服自动回复** - 常见问题自动应答
2. **消息记录备份** - 重要聊天记录存档
3. **智能助手** - 基于上下文的AI回复
4. **群消息监控** - 关键词提醒、自动总结

需要我开始实现这个系统吗？
