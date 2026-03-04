"""
自动回复引擎
支持关键词匹配和AI回复
"""
import json
import re
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from database import ChatDatabase


@dataclass
class ReplyRule:
    """回复规则"""
    keyword: str          # 关键词，支持通配符 *
    response: str         # 回复内容
    priority: int = 0     # 优先级，数字越大越优先
    match_type: str = "contains"  # contains/exact/regex


class AutoReplyEngine:
    """自动回复引擎"""
    
    def __init__(self, db: ChatDatabase):
        self.db = db
        self.ai_callback: Optional[Callable] = None
        
    def set_ai_callback(self, callback: Callable[[str, List], str]):
        """设置AI回复回调函数"""
        self.ai_callback = callback
    
    def match_keyword(self, message: str, keyword: str, match_type: str = "contains") -> bool:
        """匹配关键词"""
        message = message.lower().strip()
        keyword = keyword.lower().strip()
        
        if match_type == "exact":
            return message == keyword
        elif match_type == "regex":
            try:
                return bool(re.search(keyword, message))
            except:
                return False
        elif match_type == "contains":
            return keyword in message
        else:
            return keyword in message
    
    def get_reply(self, contact: str, message: str) -> Optional[str]:
        """获取自动回复内容"""
        # 查询该联系人的自动回复规则
        rules_config = self.db.get_auto_reply_rules(contact)
        
        if not rules_config or not rules_config.get('enabled'):
            return None
        
        rules = rules_config.get('rules', [])
        mode = rules_config.get('mode', 'keyword')
        
        # AI模式
        if mode == 'ai' and self.ai_callback:
            context_window = rules_config.get('context_window', 5)
            context = self.db.get_recent_context(contact, limit=context_window)
            
            try:
                return self.ai_callback(contact, message, context)
            except Exception as e:
                print(f"[AI回复错误] {e}")
                return None
        
        # 关键词模式
        # 按优先级排序
        sorted_rules = sorted(rules, key=lambda x: x.get('priority', 0), reverse=True)
        
        for rule in sorted_rules:
            keyword = rule.get('keyword', '')
            response = rule.get('response', '')
            match_type = rule.get('match_type', 'contains')
            
            # 特殊关键词 * 表示匹配所有
            if keyword == '*':
                return response
            
            if self.match_keyword(message, keyword, match_type):
                return response
        
        return None
    
    def handle_incoming_message(self, contact: str, sender: str, message: str) -> Optional[str]:
        """处理收到的消息，返回回复内容（如果有）"""
        # 不回复自己发送的消息
        if sender == 'me':
            return None
        
        # 获取回复
        reply = self.get_reply(contact, message)
        
        if reply:
            print(f"[自动回复] {contact} -> {reply[:50]}...")
        
        return reply
    
    def set_rules(self, contact: str, rules: List[Dict], mode: str = 'keyword'):
        """设置自动回复规则"""
        enabled = len(rules) > 0
        
        self.db.set_auto_reply(
            contact=contact,
            enabled=enabled,
            rules=rules,
            mode=mode
        )
        
        print(f"[规则设置] {contact}: {len(rules)}条规则，模式={mode}")
    
    def enable_auto_reply(self, contact: str):
        """启用自动回复"""
        rules = self.db.get_auto_reply_rules(contact)
        if rules:
            rules['enabled'] = True
            self.db.set_auto_reply(
                contact=contact, 
                enabled=True, 
                rules=rules.get('rules', []),
                mode=rules.get('mode', 'keyword')
            )
            print(f"[启用] {contact} 自动回复已开启")
    
    def disable_auto_reply(self, contact: str):
        """禁用自动回复"""
        rules = self.db.get_auto_reply_rules(contact)
        if rules:
            rules['enabled'] = False
            self.db.set_auto_reply(
                contact=contact, 
                enabled=False, 
                rules=rules.get('rules', []),
                mode=rules.get('mode', 'keyword')
            )
            print(f"[禁用] {contact} 自动回复已关闭")
    
    def set_auto_reply(self, contact: str, enabled: bool, mode: str = 'keyword', rules: List[Dict] = None):
        """设置自动回复（兼容server.py接口）"""
        if rules is None:
            rules = []
        self.set_rules(contact, rules, mode)
        if not enabled:
            self.disable_auto_reply(contact)
    
    def test_reply(self, contact: str, message: str) -> Dict:
        """测试自动回复（兼容server.py接口）"""
        reply = self.get_reply(contact, message)
        return {
            "contact": contact,
            "test_message": message,
            "would_reply": reply is not None,
            "reply_content": reply if reply else "无匹配规则"
        }


# 预设规则模板
REPLY_TEMPLATES = {
    "客服模式": [
        {"keyword": "在吗", "response": "在的，请问有什么可以帮您？", "priority": 10},
        {"keyword": "多少钱", "response": "请问您想了解哪款产品呢？", "priority": 5},
        {"keyword": "怎么联系", "response": "您可以直接在这里留言，我会尽快回复。", "priority": 5},
        {"keyword": "*", "response": "您好，我正在忙，稍后回复您。", "priority": 0}
    ],
    "忙碌模式": [
        {"keyword": "*", "response": "【自动回复】我现在不方便回复，有事请留言，稍后联系您。", "priority": 0}
    ],
    "休息模式": [
        {"keyword": "*", "response": "【自动回复】非工作时间，如有急事请电话联系。", "priority": 0}
    ]
}

# 别名，兼容server.py导入
PRESET_RULES = REPLY_TEMPLATES


def get_template(name: str) -> List[Dict]:
    """获取预设模板"""
    return REPLY_TEMPLATES.get(name, [])


# 测试代码
if __name__ == "__main__":
    from database import ChatDatabase
    from message_listener import Message
    
    db = ChatDatabase("test_reply.db")
    engine = AutoReplyEngine(db)
    
    # 设置规则
    rules = [
        {"keyword": "在吗", "response": "在的，请说", "priority": 10},
        {"keyword": "你好", "response": "你好！有什么可以帮您？", "priority": 5},
        {"keyword": "*", "response": "【自动回复】稍后回复您", "priority": 0}
    ]
    
    engine.set_rules("测试用户", rules)
    
    # 测试回复
    test_messages = [
        ("测试用户", "对方", "在吗"),
        ("测试用户", "对方", "你好啊"),
        ("测试用户", "对方", "随便说点什么"),
        ("测试用户", "me", "自己发的消息"),
    ]
    
    print("\n测试自动回复:")
    for contact, sender, msg in test_messages:
        reply = engine.handle_incoming_message(contact, sender, msg)
        if reply:
            print(f"  消息: {msg} -> 回复: {reply}")
        else:
            print(f"  消息: {msg} -> 无回复")
