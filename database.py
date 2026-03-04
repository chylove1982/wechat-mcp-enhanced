"""
微信聊天记录数据库模块
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib


class ChatDatabase:
    """聊天记录数据库"""
    
    def __init__(self, db_path: str = "chat_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 聊天记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_name TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    message_hash TEXT UNIQUE,
                    session_id TEXT
                )
            ''')
            
            # 联系人表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    nickname TEXT,
                    remark TEXT,
                    last_message_time DATETIME,
                    unread_count INTEGER DEFAULT 0,
                    auto_reply_enabled BOOLEAN DEFAULT 0,
                    auto_reply_rules TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_contact_time 
                ON chat_messages(contact_name, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_hash 
                ON chat_messages(message_hash)
            ''')
            
            conn.commit()
    
    def save_message(self, contact: str, sender: str, content: str, 
                     msg_type: str = "text", timestamp: str = None) -> bool:
        """保存单条消息"""
        try:
            # 生成消息哈希（用于去重）
            hash_input = f"{contact}:{sender}:{content}:{timestamp or datetime.now().isoformat()}"
            message_hash = hashlib.md5(hash_input.encode()).hexdigest()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR IGNORE INTO chat_messages 
                    (contact_name, sender, message_type, content, timestamp, message_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    contact, sender, msg_type, content, 
                    timestamp or datetime.now().isoformat(),
                    message_hash
                ))
                
                if cursor.rowcount > 0:
                    # 更新联系人最后消息时间
                    cursor.execute('''
                        INSERT INTO contacts (name, last_message_time, unread_count)
                        VALUES (?, ?, 1)
                        ON CONFLICT(name) DO UPDATE SET
                        last_message_time = excluded.last_message_time,
                        unread_count = unread_count + 1
                    ''', (contact, timestamp or datetime.now().isoformat()))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"[DB错误] 保存消息失败: {e}")
            return False
    
    def get_chat_history(self, contact: str, limit: int = 50, 
                         offset: int = 0) -> List[Dict]:
        """获取聊天记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM chat_messages 
                WHERE contact_name = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (contact, limit, offset))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_unread_messages(self, contact: Optional[str] = None,
                           mark_as_read: bool = False) -> List[Dict]:
        """获取未读消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if contact:
                cursor.execute('''
                    SELECT * FROM chat_messages 
                    WHERE contact_name = ? AND is_read = 0
                    ORDER BY timestamp ASC
                ''', (contact,))
            else:
                cursor.execute('''
                    SELECT * FROM chat_messages 
                    WHERE is_read = 0
                    ORDER BY timestamp ASC
                ''')
            
            rows = cursor.fetchall()
            messages = [dict(row) for row in rows]
            
            # 标记为已读
            if mark_as_read and messages:
                ids = [str(m['id']) for m in messages]
                cursor.execute(f'''
                    UPDATE chat_messages SET is_read = 1 
                    WHERE id IN ({','.join(ids)})
                ''')
                
                # 重置未读计数
                if contact:
                    cursor.execute('''
                        UPDATE contacts SET unread_count = 0 
                        WHERE name = ?
                    ''', (contact,))
                else:
                    cursor.execute('UPDATE contacts SET unread_count = 0')
                
                conn.commit()
            
            return messages
    
    def get_contacts(self) -> List[Dict]:
        """获取联系人列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM contacts 
                ORDER BY last_message_time DESC
            ''')
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def set_auto_reply(self, contact: str, enabled: bool, rules: List[Dict]):
        """设置自动回复规则"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO contacts (name, auto_reply_enabled, auto_reply_rules)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                auto_reply_enabled = excluded.auto_reply_enabled,
                auto_reply_rules = excluded.auto_reply_rules
            ''', (contact, enabled, json.dumps(rules)))
            
            conn.commit()
    
    def get_auto_reply_rules(self, contact: str) -> Optional[Dict]:
        """获取自动回复规则"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT auto_reply_enabled, auto_reply_rules 
                FROM contacts WHERE name = ?
            ''', (contact,))
            
            row = cursor.fetchone()
            if row and row[0]:
                return {
                    'enabled': row[0],
                    'rules': json.loads(row[1]) if row[1] else []
                }
            return None
    
    def get_recent_context(self, contact: str, limit: int = 10) -> List[Tuple[str, str]]:
        """获取最近对话上下文（用于AI回复）"""
        history = self.get_chat_history(contact, limit=limit)
        # 返回 [(sender, content), ...] 按时间正序
        return [(h['sender'], h['content']) for h in reversed(history)]
    
    def search_messages(self, keyword: str, contact: Optional[str] = None,
                       limit: int = 50) -> List[Dict]:
        """搜索消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if contact:
                cursor.execute('''
                    SELECT * FROM chat_messages 
                    WHERE contact_name = ? AND content LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (contact, f'%{keyword}%', limit))
            else:
                cursor.execute('''
                    SELECT * FROM chat_messages 
                    WHERE content LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (f'%{keyword}%', limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


# 测试代码
if __name__ == "__main__":
    db = ChatDatabase("test_chat.db")
    
    # 测试保存消息
    db.save_message("测试用户", "对方", "你好！", "text")
    db.save_message("测试用户", "me", "你好，有什么可以帮你的？", "text")
    db.save_message("测试用户", "对方", "请问这个怎么用？", "text")
    
    # 测试查询
    print("\n聊天记录:")
    history = db.get_chat_history("测试用户", limit=5)
    for msg in history:
        print(f"[{msg['timestamp']}] {msg['sender']}: {msg['content']}")
    
    print("\n联系人列表:")
    contacts = db.get_contacts()
    for c in contacts:
        print(f"{c['name']}: 未读{c['unread_count']}条")
