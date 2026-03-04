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
import numpy as np

# 尝试导入OCR库
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    print("[警告] PaddleOCR未安装，使用备选方案")
    print("安装: pip install paddleocr paddlepaddle")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


@dataclass
class Message:
    """消息对象"""
    contact: str
    sender: str  # "me" 或 对方名称
    content: str
    timestamp: datetime
    message_type: str = "text"


class MessageListener:
    """消息监听器"""
    
    def __init__(self, db, ocr_engine: str = "paddle"):
        self.db = db
        self.running = False
        self.listener_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable] = []
        self.last_check_time = {}
        
        # 初始化OCR
        self.ocr = self._init_ocr(ocr_engine)
        
        # 当前监控的联系人
        self.monitored_contacts: set = set()
    
    def _init_ocr(self, engine: str):
        """初始化OCR引擎"""
        if engine == "paddle" and PADDLE_AVAILABLE:
            print("[OCR] 使用PaddleOCR")
            return PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                show_log=False,
                use_gpu=False
            )
        elif TESSERACT_AVAILABLE:
            print("[OCR] 使用Tesseract")
            return "tesseract"
        else:
            print("[警告] 无OCR引擎，监听功能受限")
            return None
    
    def _get_chat_window(self):
        """获取当前聊天窗口"""
        try:
            windows = gw.getWindowsWithTitle("Dragon")
            for win in windows:
                if "Dragon" in win.title:
                    return win
        except:
            pass
        
        # 回退到主窗口
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
            # 计算消息区域（窗口右侧的聊天区域）
            # 微信聊天区域大约在窗口右侧50%-95%，顶部15%-85%
            left = window.left + int(window.width * 0.25)
            top = window.top + int(window.height * 0.12)
            width = int(window.width * 0.7)
            height = int(window.height * 0.75)
            
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            return screenshot
            
        except Exception as e:
            print(f"[截图错误] {e}")
            return None
    
    def _extract_text_paddle(self, image: Image.Image) -> List[Dict]:
        """使用PaddleOCR提取文字"""
        try:
            # 转换为numpy数组
            img_array = np.array(image)
            
            # OCR识别
            result = self.ocr.ocr(img_array, cls=True)
            
            messages = []
            if result and result[0]:
                for line in result[0]:
                    if line:
                        bbox = line[0]  # 边界框
                        text = line[1][0]  # 文字内容
                        confidence = line[1][1]  # 置信度
                        
                        if confidence > 0.75 and text.strip():
                            # 根据x坐标判断左右（发送/接收）
                            # bbox: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                            center_x = (bbox[0][0] + bbox[2][0]) / 2
                            img_width = image.width
                            
                            sender = "other" if center_x < img_width * 0.5 else "me"
                            
                            messages.append({
                                'text': text,
                                'sender': sender,
                                'confidence': confidence,
                                'position': center_x
                            })
            
            return messages
            
        except Exception as e:
            print(f"[OCR错误] {e}")
            return []
    
    def _extract_text_tesseract(self, image: Image.Image) -> List[Dict]:
        """使用Tesseract提取文字（备选）"""
        try:
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            messages = []
            for line in lines:
                # Tesseract无法区分发送者，默认标记为other
                messages.append({
                    'text': line,
                    'sender': 'unknown',
                    'confidence': 0.5
                })
            
            return messages
            
        except Exception as e:
            print(f"[OCR错误] {e}")
            return []
    
    def _get_current_contact(self) -> Optional[str]:
        """获取当前聊天对象名称"""
        try:
            window = self._get_chat_window()
            if window and "Dragon" in window.title:
                # Dragon窗口标题通常是 "xxx - Dragon"
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
        
        # OCR识别
        if self.ocr == "tesseract":
            raw_messages = self._extract_text_tesseract(screenshot)
        elif self.ocr:
            raw_messages = self._extract_text_paddle(screenshot)
        else:
            return []
        
        # 处理识别结果
        new_messages = []
        for msg in raw_messages:
            content = msg['text'].strip()
            if not content or len(content) < 2:
                continue
            
            # 判断发送者
            if msg['sender'] == 'me':
                sender = 'me'
            elif msg['sender'] == 'other':
                sender = contact
            else:
                sender = 'unknown'
            
            # 保存到数据库（会自动去重）
            saved = self.db.save_message(
                contact=contact,
                sender=sender,
                content=content,
                msg_type='text'
            )
            
            if saved:
                message = Message(
                    contact=contact,
                    sender=sender,
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
    
    def start(self, interval: float = 3.0, contacts: List[str] = None):
        """开始监听"""
        if self.running:
            print("[监听] 已经在运行中")
            return
        
        self.running = True
        if contacts:
            self.monitored_contacts = set(contacts)
        
        print(f"[监听] 启动，间隔{interval}秒")
        if self.monitored_contacts:
            print(f"[监听] 监控联系人: {self.monitored_contacts}")
        else:
            print("[监听] 监控所有联系人")
        
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
    
    def stop(self):
        """停止监听"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=5)
        print("[监听] 已停止")
    
    def add_callback(self, callback: Callable[[Message], None]):
        """添加新消息回调"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Message], None]):
        """移除回调"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)


# 测试代码
if __name__ == "__main__":
    from database import ChatDatabase
    
    db = ChatDatabase("test_listener.db")
    listener = MessageListener(db)
    
    # 添加回调
    def on_new_message(msg: Message):
        print(f"\n[回调] 收到消息: {msg.contact} - {msg.content}")
    
    listener.add_callback(on_new_message)
    
    print("\n开始监听（按Ctrl+C停止）...")
    listener.start(interval=2.0)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止监听...")
        listener.stop()
