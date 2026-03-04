# -*- coding: utf-8 -*-
"""
微信消息监听模块 - 优化版
支持微信聊天界面截图识别
"""
import time
import threading
import hashlib
from datetime import datetime
from typing import Callable, Optional, List, Dict
from dataclasses import dataclass, asdict
import pyautogui
import pygetwindow as gw
from PIL import Image, ImageDraw

from ocr_engine import OCREngine
from database import ChatDatabase


@dataclass
class ChatMessage:
    """聊天消息对象"""
    contact: str
    sender: str
    content: str
    timestamp: datetime
    message_type: str = "text"
    is_new: bool = True
    
    def to_dict(self):
        return {
            'contact': self.contact,
            'sender': self.sender,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'message_type': self.message_type,
            'is_new': self.is_new
        }


class WeChatMessageListener:
    """微信消息监听器 - 专门优化微信聊天界面"""
    
    def __init__(self, db: Optional[ChatDatabase] = None, ocr_engine: str = "auto"):
        self.db = db
        self.running = False
        self.listener_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable] = []
        self.check_interval = 3
        
        # OCR引擎
        self.ocr = OCREngine(ocr_engine)
        
        # 状态追踪
        self.last_screenshot_hash = None
        self.last_messages = []  # 上次识别的消息
        self.monitored_contacts: set = set()
        
        # 统计
        self.stats = {
            'total_checks': 0,
            'new_messages_found': 0,
            'start_time': None
        }
    
    def get_wechat_window(self):
        """获取微信窗口"""
        try:
            # 先找聊天窗口（Dragon标题）
            windows = gw.getWindowsWithTitle("Dragon")
            for win in windows:
                if "Dragon" in win.title and win.width > 500:
                    return win
            
            # 回退到主窗口
            wins = gw.getWindowsWithTitle("微信")
            for w in wins:
                if w.width > 500:
                    return w
        except:
            pass
        return None
    
    def get_current_contact(self) -> Optional[str]:
        """获取当前聊天对象 - 改进版"""
        try:
            window = self.get_wechat_window()
            if not window:
                return None
            
            title = window.title.strip()
            
            # 方法1: Dragon窗口标题格式: "联系人名称 - Dragon"
            if " - Dragon" in title:
                contact = title.replace(" - Dragon", "").strip()
                if contact and contact != "微信":
                    return contact
            
            # 方法2: 尝试截图识别顶部标题栏
            try:
                # 截图窗口顶部区域（标题栏）
                title_height = 40
                screenshot = pyautogui.screenshot(region=(
                    window.left + 100,  # 跳过左侧头像区域
                    window.top + 10,
                    min(300, window.width - 200),  # 标题区域宽度
                    title_height
                ))
                
                # 临时保存并OCR识别
                temp_path = "_temp_title.png"
                screenshot.save(temp_path)
                results = self.ocr.recognize(temp_path)
                
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                # 取第一个识别结果作为联系人名称
                if results:
                    contact = results[0].get('text', '').strip()
                    # 过滤掉常见UI文字
                    if contact and contact not in ['微信', '返回', '搜索', '']:
                        return contact
                        
            except Exception as e:
                print(f"[识别标题错误] {e}")
            
            # 方法3: 如果标题不是"微信"，直接返回标题
            if title and title != "微信":
                return title
                
        except Exception as e:
            print(f"[获取联系人错误] {e}")
            
        return None
    
    def capture_chat_area(self, window) -> Optional[Image.Image]:
        """截图聊天区域（优化微信聊天界面）"""
        try:
            # 微信聊天区域：右侧消息列表区域
            # 估算：右侧60%的宽度，中间80%的高度（去掉顶部标题和底部输入框）
            left = window.left + int(window.width * 0.25)
            top = window.top + int(window.height * 0.15)
            width = int(window.width * 0.70)
            height = int(window.height * 0.70)
            
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            return screenshot
            
        except Exception as e:
            print(f"[截图错误] {e}")
            return None
    
    def detect_sender_by_position(self, center_x: float, img_width: int) -> str:
        """根据位置判断消息发送者
        
        微信特点：
        - 左侧消息 = 对方发送
        - 右侧消息 = 自己发送
        """
        if center_x < img_width * 0.4:
            return "other"  # 对方
        elif center_x > img_width * 0.6:
            return "me"     # 自己
        else:
            return "unknown"
    
    def recognize_messages(self, image: Image.Image) -> List[Dict]:
        """识别图片中的消息"""
        # 保存临时文件
        temp_path = "_temp_chat.png"
        image.save(temp_path)
        
        # OCR识别
        results = self.ocr.recognize(temp_path)
        
        # 清理
        try:
            import os
            os.remove(temp_path)
        except:
            pass
        
        return results
    
    def filter_chat_messages(self, ocr_results: List[Dict], contact: str) -> List[ChatMessage]:
        """过滤和整理聊天消息"""
        messages = []
        
        for result in ocr_results:
            text = result.get('text', '').strip()
            if not text or len(text) < 2:
                continue
            
            # 过滤掉微信界面元素（时间、按钮等）
            if self.is_ui_element(text):
                continue
            
            # 判断发送者
            position = result.get('position', (0, 0))
            if isinstance(position, tuple):
                center_x = position[0]
            else:
                center_x = position
            
            sender_type = self.detect_sender_by_position(center_x, 1000)  # 估算宽度
            
            if sender_type == "me":
                sender = "me"
            elif sender_type == "other":
                sender = contact
            else:
                sender = "unknown"
            
            msg = ChatMessage(
                contact=contact,
                sender=sender,
                content=text,
                timestamp=datetime.now(),
                message_type="text"
            )
            messages.append(msg)
        
        return messages
    
    def is_ui_element(self, text: str) -> bool:
        """判断是否为微信UI元素（非聊天消息）"""
        # 常见的时间格式
        time_patterns = [
            '昨天', '今天', '星期', '202', ':',  # 时间相关
            '语音通话', '视频通话', '撤回了一条消息',
            '查看更多消息', '以下为新消息',
        ]
        
        for pattern in time_patterns:
            if pattern in text:
                return True
        
        # 太短的内容可能是按钮或图标
        if len(text) <= 1:
            return True
        
        return False
    
    def check_new_messages(self) -> List[ChatMessage]:
        """检查新消息 - 主逻辑"""
        # 获取微信窗口
        window = self.get_wechat_window()
        if not window:
            return []
        
        # 获取当前联系人
        contact = self.get_current_contact()
        if not contact:
            return []
        
        # 如果只监控特定联系人
        if self.monitored_contacts and contact not in self.monitored_contacts:
            return []
        
        # 截图
        screenshot = self.capture_chat_area(window)
        if not screenshot:
            return []
        
        # 计算截图哈希（用于检测变化）
        img_bytes = screenshot.tobytes()
        current_hash = hashlib.md5(img_bytes).hexdigest()
        
        # 如果和上次一样，没有新消息
        if current_hash == self.last_screenshot_hash:
            return []
        
        self.last_screenshot_hash = current_hash
        self.stats['total_checks'] += 1
        
        # OCR识别
        ocr_results = self.recognize_messages(screenshot)
        
        # 过滤和整理
        messages = self.filter_chat_messages(ocr_results, contact)
        
        # 检测新消息（对比上次）
        new_messages = self.detect_new_only(messages)
        
        # 保存到数据库
        if self.db and new_messages:
            for msg in new_messages:
                saved = self.db.save_message(
                    contact=msg.contact,
                    sender=msg.sender,
                    content=msg.content,
                    msg_type=msg.message_type
                )
                if saved:
                    self.stats['new_messages_found'] += 1
                    # 触发回调
                    for callback in self.callbacks:
                        try:
                            callback(msg)
                        except Exception as e:
                            print(f"[回调错误] {e}")
        
        self.last_messages = messages
        return new_messages
    
    def detect_new_only(self, current_messages: List[ChatMessage]) -> List[ChatMessage]:
        """只检测真正的消息"""
        if not self.last_messages:
            # 首次运行，不返回（避免大量历史消息）
            return []
        
        new_msgs = []
        current_contents = {m.content for m in current_messages}
        last_contents = {m.content for m in self.last_messages}
        
        # 找出新增的内容
        new_contents = current_contents - last_contents
        
        for msg in current_messages:
            if msg.content in new_contents:
                msg.is_new = True
                new_msgs.append(msg)
        
        return new_msgs
    
    @property
    def is_listening(self) -> bool:
        return self.running
    
    def start_listening(self, contacts=None, interval: float = 3.0, on_message=None):
        """开始监听"""
        if self.running:
            print("[监听] 已经在运行中")
            return
        
        self.running = True
        self.check_interval = interval
        self.stats['start_time'] = datetime.now()
        
        if contacts:
            self.monitored_contacts = set(contacts)
        
        if on_message:
            self.callbacks.append(on_message)
        
        print(f"[监听] 启动，间隔{interval}秒")
        print(f"[监听] 当前窗口: {self.get_current_contact() or '未找到'}")
        
        def listen_loop():
            while self.running:
                try:
                    new_msgs = self.check_new_messages()
                    
                    if new_msgs:
                        for msg in new_msgs:
                            print(f"[新消息] {msg.contact} - {msg.sender}: {msg.content[:50]}")
                            # 调用回调函数
                            for callback in self.callbacks:
                                try:
                                    callback(msg)
                                except Exception as e:
                                    print(f"[回调错误] {e}")
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    print(f"[监听错误] {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(interval)
        
        self.listener_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listener_thread.start()
    
    def stop_listening(self):
        """停止监听"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=5)
        
        duration = datetime.now() - self.stats['start_time'] if self.stats['start_time'] else None
        print("[监听] 已停止")
        print(f"[统计] 运行时长: {duration}")
        print(f"[统计] 检查次数: {self.stats['total_checks']}")
        print(f"[统计] 新消息: {self.stats['new_messages_found']}")
    
    def get_stats(self) -> Dict:
        """获取监听统计"""
        return {
            'is_running': self.running,
            'total_checks': self.stats['total_checks'],
            'new_messages_found': self.stats['new_messages_found'],
            'current_contact': self.get_current_contact(),
            'monitored_contacts': list(self.monitored_contacts)
        }


# 测试代码
if __name__ == "__main__":
    from database import get_database
    
    print("=" * 60)
    print("微信消息监听测试")
    print("=" * 60)
    print()
    print("请确保：")
    print("1. 微信PC版已打开")
    print("2. 已打开某个聊天窗口")
    print("3. 窗口不要被其他窗口完全遮挡")
    print()
    input("按 Enter 开始测试...")
    
    db = get_database("test_chat_listener.db")
    listener = WeChatMessageListener(db)
    
    # 打印当前窗口
    contact = listener.get_current_contact()
    print(f"\n当前聊天对象: {contact or '未检测到'}")
    
    if not contact:
        print("❌ 未找到微信聊天窗口，请检查微信是否打开")
        exit(1)
    
    # 添加回调
    def on_new_message(msg: ChatMessage):
        print(f"\n💬 [新消息] {msg.sender}: {msg.content}")
    
    listener.callbacks.append(on_new_message)
    
    # 开始监听
    print(f"\n开始监听 {contact} 的消息...")
    print("按 Ctrl+C 停止\n")
    
    listener.start_listening(interval=2.0)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n停止监听...")
        listener.stop_listening()
        
        # 显示统计
        stats = listener.get_stats()
        print(f"\n统计信息:")
        print(f"  检查次数: {stats['total_checks']}")
        print(f"  新消息数: {stats['new_messages_found']}")
