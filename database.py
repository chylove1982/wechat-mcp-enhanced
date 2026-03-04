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
            
            # 联系人表 - 增强版
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    display_name TEXT NOT NULL,      -- 显示名称（从窗口标题获取）
                    wechat_id TEXT,                   -- 微信ID（如果有）
                    remark_name TEXT,                 -- 备注名
                    nickname TEXT,                    -- 昵称
                    contact_type TEXT DEFAULT 'individual',  -- individual/group/official
                    avatar_path TEXT,                 -- 头像路径（可选）
                    last_message_time DATETIME,
                    unread_count INTEGER DEFAULT 0,
                    auto_reply_enabled BOOLEAN DEFAULT 0,
                    auto_reply_rules TEXT,
                    extra_data TEXT                   -- 额外JSON数据
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
    
    def set_auto_reply(self, contact: str, enabled: bool, rules: List[Dict], mode: str = 'keyword'):
        """设置自动回复规则"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 将mode存储在规则中
            rules_data = {
                'rules': rules,
                'mode': mode,
                'enabled': enabled
            }
            
            cursor.execute('''
                INSERT INTO contacts (name, auto_reply_enabled, auto_reply_rules)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                auto_reply_enabled = excluded.auto_reply_enabled,
                auto_reply_rules = excluded.auto_reply_rules
            ''', (contact, enabled, json.dumps(rules_data)))
            
            conn.commit()
    
    def save_contact(self, display_name: str, wechat_id: str = None, 
                     contact_type: str = 'individual', extra_data: dict = None):
        """保存或更新联系人信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            extra_json = json.dumps(extra_data) if extra_data else None
            
            cursor.execute('''
                INSERT INTO contacts 
                (display_name, wechat_id, contact_type, extra_data, last_message_time)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(display_name) DO UPDATE SET
                last_message_time = excluded.last_message_time,
                wechat_id = COALESCE(excluded.wechat_id, wechat_id),
                extra_data = COALESCE(excluded.extra_data, extra_data)
            ''', (display_name, wechat_id, contact_type, extra_json, 
                 datetime.now().isoformat()))
            
            conn.commit()
    
    def get_contact_info(self, display_name: str) -> Optional[Dict]:
        """获取联系人详细信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM contacts WHERE display_name = ?
            ''', (display_name,))
            
            row = cursor.fetchone()
            if row:
                info = dict(row)
                if info.get('extra_data'):
                    info['extra_data'] = json.loads(info['extra_data'])
                return info
            return None
        """获取自动回复规则"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT auto_reply_enabled, auto_reply_rules
                FROM contacts WHERE name = ?
            ''', (contact,))

            row = cursor.fetchone()
            if row:
                try:
                    rules_data = json.loads(row[1]) if row[1] else {}
                    # 兼容旧格式（纯列表）和新格式（字典）
                    if isinstance(rules_data, list):
                        return {
                            'enabled': row[0],
                            'rules': rules_data,
                            'mode': 'keyword'
                        }
                    else:
                        return {
                            'enabled': rules_data.get('enabled', row[0]),
                            'rules': rules_data.get('rules', []),
                            'mode': rules_data.get('mode', 'keyword')
                        }
                except:
                    return {
                        'enabled': row[0],
                        'rules': [],
                        'mode': 'keyword'
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
    
    def get_statistics(self) -> Dict:
        """获取聊天统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 总消息数
            cursor.execute('SELECT COUNT(*) FROM chat_messages')
            stats['total_messages'] = cursor.fetchone()[0]
            
            # 总联系人数
            cursor.execute('SELECT COUNT(*) FROM contacts')
            stats['total_contacts'] = cursor.fetchone()[0]
            
            # 未读消息数
            cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE is_read = 0')
            stats['unread_messages'] = cursor.fetchone()[0]
            
            return stats


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


def get_database(db_path: str = "chat_history.db") -> ChatDatabase:
    """获取数据库实例（单例模式）"""
    if not hasattr(get_database, '_instance'):
        get_database._instance = ChatDatabase(db_path)
    return get_database._instance
