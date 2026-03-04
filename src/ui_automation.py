"""
Windows UI自动化模块
专门处理微信PC版的UI交互
"""

import time
import asyncio
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from loguru import logger

try:
    import win32gui
    import win32con
    import win32api
    import pyautogui
    from pywinauto import Application, Desktop, findwindows
    from pywinauto.timings import TimeoutError as PyWinAutoTimeoutError
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    logger.warning("Windows自动化模块不可用")


@dataclass
class WindowInfo:
    """窗口信息"""
    handle: int
    title: str
    class_name: str
    rect: Tuple[int, int, int, int]
    is_visible: bool
    is_enabled: bool


class WeChatUIAutomation:
    """微信UI自动化类"""
    
    # 微信窗口类名
    WECHAT_MAIN_CLASS = "WeChatMainWndForPC"
    WECHAT_LOGIN_CLASS = "WeChatLoginWndForPC"
    
    # 按钮位置（相对坐标，需要根据实际情况调整）
    BUTTON_COORDS = {
        "voice_call": (0.85, 0.05),      # 语音通话按钮
        "video_call": (0.90, 0.05),      # 视频通话按钮
        "file_transfer": (0.70, 0.05),   # 文件传输
        "send": (0.95, 0.95),            # 发送按钮
        "accept_call": (0.45, 0.60),     # 接听按钮
        "reject_call": (0.55, 0.60),     # 拒接按钮
        "end_call": (0.50, 0.90),        # 挂断按钮
    }
    
    def __init__(self):
        self.app: Optional[Application] = None
        self.main_window = None
        self.chat_window = None
        self._window_rect = None
        
    def initialize(self) -> bool:
        """初始化微信自动化"""
        if not WINDOWS_AVAILABLE:
            logger.warning("Windows环境不可用")
            return False
        
        try:
            # 查找微信主窗口
            hwnd = win32gui.FindWindow(self.WECHAT_MAIN_CLASS, None)
            if hwnd == 0:
                logger.error("未找到微信主窗口，请确保微信已登录")
                return False
            
            # 连接到微信进程
            self.app = Application(backend="uia").connect(handle=hwnd)
            self.main_window = self.app.window(handle=hwnd)
            
            # 激活窗口
            self._activate_window(hwnd)
            
            logger.info("微信自动化初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化微信自动化失败: {e}")
            return False
    
    def _activate_window(self, hwnd: int):
        """激活窗口"""
        try:
            # 如果窗口最小化，恢复它
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 将窗口带到前台
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            
        except Exception as e:
            logger.warning(f"激活窗口失败: {e}")
    
    def get_window_info(self) -> Optional[WindowInfo]:
        """获取窗口信息"""
        if not self.main_window:
            return None
        
        try:
            rect = self.main_window.rectangle()
            return WindowInfo(
                handle=self.main_window.handle,
                title=self.main_window.window_text(),
                class_name=self.main_window.class_name(),
                rect=(rect.left, rect.top, rect.right, rect.bottom),
                is_visible=self.main_window.is_visible(),
                is_enabled=self.main_window.is_enabled()
            )
        except Exception as e:
            logger.error(f"获取窗口信息失败: {e}")
            return None
    
    def search_contact(self, name: str, timeout: int = 5) -> bool:
        """搜索联系人"""
        try:
            if not self.main_window:
                return False
            
            # 点击搜索框
            search_box = self.main_window.child_window(
                control_type="Edit",
                title="搜索"
            )
            
            if search_box.exists(timeout=timeout):
                search_box.click_input()
                search_box.type_keys(name, with_spaces=True)
                time.sleep(0.5)
                
                # 按回车选择第一个结果
                pyautogui.keyDown('return')
                pyautogui.keyUp('return')
                time.sleep(0.5)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"搜索联系人失败: {e}")
            return False
    
    def click_voice_call_button(self) -> bool:
        """点击语音通话按钮"""
        try:
            # 方法1: 通过名称查找
            button = self.main_window.child_window(
                control_type="Button",
                title_re=".*语音.*"
            )
            
            if button.exists(timeout=2):
                button.click_input()
                return True
            
            # 方法2: 通过相对坐标点击
            if self._window_rect:
                x = int(self._window_rect[0] + self._window_rect[2] * self.BUTTON_COORDS["voice_call"][0])
                y = int(self._window_rect[1] + self._window_rect[3] * self.BUTTON_COORDS["voice_call"][1])
                pyautogui.click(x, y)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"点击语音通话按钮失败: {e}")
            return False
    
    def click_end_call_button(self) -> bool:
        """点击挂断按钮"""
        try:
            # 查找挂断按钮
            button = self.main_window.child_window(
                control_type="Button",
                title_re=".*挂断.*|.*结束.*"
            )
            
            if button.exists(timeout=2):
                button.click_input()
                return True
            
            # 按ESC键挂断
            pyautogui.keyDown('esc')
            pyautogui.keyUp('esc')
            return True
            
        except Exception as e:
            logger.error(f"点击挂断按钮失败: {e}")
            return False
    
    def click_accept_call_button(self) -> bool:
        """点击接听按钮"""
        try:
            button = self.main_window.child_window(
                control_type="Button",
                title_re=".*接听.*|.*接受.*"
            )
            
            if button.exists(timeout=3):
                button.click_input()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"点击接听按钮失败: {e}")
            return False
    
    def send_file_by_clipboard(self, file_path: str) -> bool:
        """通过剪贴板发送文件"""
        try:
            import pyperclip
            from pywinauto.keyboard import send_keys
            
            # 复制文件到剪贴板
            pyperclip.copy(file_path)
            
            # 粘贴到输入框
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('v')
            pyautogui.keyUp('v')
            pyautogui.keyUp('ctrl')
            
            time.sleep(0.5)
            
            # 发送
            pyautogui.keyDown('return')
            pyautogui.keyUp('return')
            
            return True
            
        except Exception as e:
            logger.error(f"通过剪贴板发送文件失败: {e}")
            return False
    
    def check_call_incoming(self) -> Optional[str]:
        """检查是否有来电"""
        try:
            # 查找来电提示窗口
            call_window = self.main_window.child_window(
                control_type="Window",
                title_re=".*来电.*|.*Calling.*"
            )
            
            if call_window.exists(timeout=1):
                # 获取来电者名称
                caller_label = call_window.child_window(control_type="Text")
                if caller_label.exists():
                    return caller_label.window_text()
                return "Unknown"
            
            return None
            
        except Exception as e:
            logger.error(f"检查来电失败: {e}")
            return None
    
    def check_call_connected(self) -> bool:
        """检查通话是否已连接"""
        try:
            # 检查通话时长标签是否存在
            duration_label = self.main_window.child_window(
                control_type="Text",
                title_re="\d{2}:\d{2}"
            )
            
            return duration_label.exists(timeout=1)
            
        except Exception as e:
            logger.error(f"检查通话状态失败: {e}")
            return False
    
    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """截图"""
        try:
            if filename is None:
                filename = f"screenshot_{int(time.time())}.png"
            
            filepath = Path("screenshots") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            logger.info(f"截图已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return ""
    
    def find_element_by_image(self, image_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """通过图像识别查找元素"""
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                return pyautogui.center(location)
            return None
            
        except Exception as e:
            logger.error(f"图像识别失败: {e}")
            return None
    
    def get_chat_messages(self, limit: int = 10) -> list:
        """获取聊天消息列表"""
        try:
            # 查找消息列表控件
            message_list = self.main_window.child_window(
                control_type="List",
                title_re=".*消息.*|.*Message.*"
            )
            
            if not message_list.exists(timeout=2):
                return []
            
            messages = []
            items = message_list.children(control_type="ListItem")
            
            for item in items[-limit:]:
                try:
                    text = item.window_text()
                    messages.append(text)
                except:
                    pass
            
            return messages
            
        except Exception as e:
            logger.error(f"获取消息列表失败: {e}")
            return []
    
    def scroll_chat_history(self, direction: str = "up", times: int = 3):
        """滚动聊天记录"""
        try:
            for _ in range(times):
                if direction == "up":
                    pyautogui.scroll(5, 960, 600)  # 向上滚动
                else:
                    pyautogui.scroll(-5, 960, 600)  # 向下滚动
                time.sleep(0.2)
                
        except Exception as e:
            logger.error(f"滚动聊天记录失败: {e}")


# 单例实例
_ui_automation: Optional[WeChatUIAutomation] = None


def get_ui_automation() -> WeChatUIAutomation:
    """获取UI自动化实例"""
    global _ui_automation
    if _ui_automation is None:
        _ui_automation = WeChatUIAutomation()
    return _ui_automation
