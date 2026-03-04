"""
微信消息监听模块
使用截图 + OCR 识别新消息
"""
import time
import threading
from datetime import datetime
from typing import Callable, Optional, List, Dict
from dataclasses import dataclass
import pyautogui
import pygetwindow as gw
from PIL import Image

# 导入统一的OCR引擎
from ocr_engine import OCREngine, PADDLE_AVAILABLE, TESSERACT_AVAILABLE

# OCR引擎可用性提示
if not PADDLE_AVAILABLE and not TESSERACT_AVAILABLE:
    print("[警告] 没有可用的OCR引擎")
    print("请运行: python install_ocr.py")
else:
    print(f"[OCR] Paddle: {'✅' if PADDLE_AVAILABLE else '❌'}, Tesseract: {'✅' if TESSERACT_AVAILABLE else '❌'}")


@dataclass
class Message:
    """消息对象"""
    contact: str
    sender: str
    content: str
    timestamp: datetime
    message_type: str = "text"


class MessageListener:
    """消息监听器"""
    
    def __init__(self, db=None, ocr_engine: str = "auto"):
        self.db = db
        self.running = False
        self.listener_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable] = []
        self.check_interval = 3
        self.last_messages_hash = {}
        
        # 初始化OCR
        self.ocr = OCREngine(ocr_engine)
        
        # 监控的联系人
        self.monitored_contacts: set = set()
    
    def _get_chat_window(self):
        """获取聊天窗口"""
        try:
            windows = gw.getWindowsWithTitle("Dragon")
            for win in windows:
                if "Dragon" in win.title:
                    return win
        except:
            pass
        
        try:
            wins = gw.getWindowsWithTitle("微信")
            for w in wins:
                if w.width > 500:
                    return w
        except:
            pass
        
        return None
    
    def _capture_message_area(self, window) -> Optional[Image.Image]:
        """截图消息区域"""
        try:
            left = window.left + int(window.width * 0.25)
            top = window.top + int(window.height * 0.12)
            width = int(window.width * 0.7)
            height = int(window.height * 0.75)
            
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            return screenshot
            
        except Exception as e:
            print(f"[截图错误] {e}")
            return None
    
    def _get_current_contact(self) -> Optional[str]:
        """获取当前联系人"""
        try:
            window = self._get_chat_window()
            if window and "Dragon" in window.title:
                return window.title.replace(" - Dragon", "").strip()
        except:
            pass
        return None
    
    def check_new_messages(self) -> List[Message]:
        """检查新消息"""
        window = self._get_chat_window()
        if not window:
            return []
        
        contact = self._get_current_contact()
        if not contact:
            return []
        
        # 如果只监控特定联系人
        if self.monitored_contacts and contact not in self.monitored_contacts:
            return []
        
        # 截图
        screenshot = self._capture_message_area(window)
        if not screenshot:
            return []
        
        # 保存临时文件进行OCR
        temp_path = "_temp_ocr.png"
        screenshot.save(temp_path)
        
        # OCR识别
        raw_messages = self.ocr.recognize(temp_path)
        
        # 清理临时文件
        try:
            import os
            os.remove(temp_path)
        except:
            pass
        
        # 处理识别结果
        new_messages = []
        for msg in raw_messages:
            content = msg['text'].strip()
            if not content or len(content) < 2:
                continue
            
            # 根据x坐标判断发送者
            if 'position' in msg:
                center_x = msg['position'][0] if isinstance(msg['position'], tuple) else msg['position']
                # 如果x坐标在图片左半边，是对方消息；右半边是自己消息
                img_width = screenshot.width
                sender = "other" if center_x < img_width * 0.5 else "me"
            else:
                sender = "unknown"
            
            # 转换sender
            if sender == "other":
                sender_name = contact
            elif sender == "me":
                sender_name = "me"
            else:
                sender_name = "unknown"
            
            # 保存到数据库
            if self.db:
                saved = self.db.save_message(
                    contact=contact,
                    sender=sender_name,
                    content=content,
                    msg_type='text'
                )
                
                if saved:
                    message = Message(
                        contact=contact,
                        sender=sender_name,
                        content=content,
                        timestamp=datetime.now()
                    )
                    new_messages.append(message)
                    
                    # 触发回调
                    for callback in self.callbacks:
                        try:
                            callback(message)
                        except Exception as e:
                            print(f"[回调错误] {e}")
        
        return new_messages
    
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
        
        if contacts:
            self.monitored_contacts = set(contacts)
        
        if on_message:
            self.add_callback(on_message)
        
        print(f"[监听] 启动，间隔{interval}秒")
        
        def listen_loop():
            while self.running:
                try:
                    new_msgs = self.check_new_messages()
                    if new_msgs:
                        for msg in new_msgs:
                            print(f"[新消息] {msg.contact} - {msg.sender}: {msg.content[:50]}")
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    print(f"[监听错误] {e}")
                    time.sleep(interval)
        
        self.listener_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listener_thread.start()
    
    def stop_listening(self):
        """停止监听"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=5)
        print("[监听] 已停止")
    
    def start(self, interval: float = 3.0, contacts: List[str] = None):
        """旧接口"""
        self.start_listening(contacts=contacts, interval=interval)
    
    def stop(self):
        """旧接口"""
        self.stop_listening()
    
    def add_callback(self, callback: Callable[[Message], None]):
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Message], None]):
        if callback in self.callbacks:
            self.callbacks.remove(callback)


# 测试代码
if __name__ == "__main__":
    from database import ChatDatabase
    
    db = ChatDatabase("test_listener.db")
    listener = MessageListener(db)
    
    def on_new_message(msg: Message):
        print(f"\n[回调] {msg.contact}: {msg.content}")
    
    listener.add_callback(on_new_message)
    
    print("\n开始监听（按Ctrl+C停止）...")
    listener.start(interval=2.0)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止监听...")
        listener.stop()
