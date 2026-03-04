# -*- coding: utf-8 -*-
"""
WeChat MCP Enhanced Server v4.0
微信MCP增强版 - 支持文件发送、语音收发、语音通话
"""

import sys
import os
import json
import asyncio
import time
import subprocess
import tempfile
import uuid
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

import pyautogui
pyautogui.FAILSAFE = False
import pygetwindow as gw
import pyperclip


def safe_print(text):
    """安全打印（避免编码错误）"""
    try:
        print(text, flush=True)
    except:
        pass


# ==================== 窗口管理 ====================

def get_wechat_window():
    """获取微信主窗口"""
    wins = gw.getWindowsWithTitle("微信")
    for w in wins:
        if w.width > 500 and w.height > 500:
            return w
    return None


def get_chat_window():
    """获取聊天窗口"""
    windows = gw.getWindowsWithTitle("Dragon")
    for win in windows:
        if "Dragon" in win.title:
            return win
    return get_wechat_window()


def set_clipboard_text(text):
    """设置剪贴板文本"""
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        safe_print(f"[错误] 设置剪贴板失败: {e}")
        return False


# ==================== 核心功能 ====================

def find_and_open_chat(contact_name):
    """搜索并打开联系人"""
    safe_print(f"[操作] 搜索联系人: {contact_name}")
    
    win = get_wechat_window()
    if not win:
        return False, "微信未运行"
    
    try:
        win.activate()
        time.sleep(0.5)
    except Exception as e:
        return False, f"无法激活窗口: {e}"
    
    # Ctrl+F 搜索
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    
    # 清空并输入
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)
    
    if not set_clipboard_text(contact_name):
        return False, "剪贴板设置失败"
    
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.0)
    
    # 回车打开
    pyautogui.press('enter')
    time.sleep(1.0)
    
    if not get_chat_window():
        return False, "未打开聊天窗口"
    
    safe_print(f"[成功] 已打开与 {contact_name} 的聊天")
    return True, None


def input_message(message):
    """在输入框中输入消息"""
    win = get_chat_window()
    if not win:
        return False, "未找到聊天窗口"
    
    # 点击输入框（窗口底部中央）
    input_x = win.left + win.width // 2
    input_y = win.top + win.height - 60
    pyautogui.click(input_x, input_y)
    time.sleep(0.3)
    
    # 清空并输入
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)
    
    if not set_clipboard_text(message):
        return False, "剪贴板设置失败"
    
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    
    return True, None


def send_message():
    """发送消息"""
    pyautogui.press('enter')
    time.sleep(0.5)
    return True, None


def send_message_to_contact(contact_name, message):
    """发送消息给指定联系人"""
    success, err = find_and_open_chat(contact_name)
    if not success:
        return False, err
    
    success, err = input_message(message)
    if not success:
        return False, err
    
    return send_message()


# ==================== 文件发送 ====================

def send_file_to_contact(contact_name, file_path, message=""):
    """发送文件给联系人 - 使用拖拽方式（修复窗口冲突）"""
    safe_print(f"[操作] 发送文件: {file_path} -> {contact_name}")
    
    # 验证文件
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    abs_path = os.path.abspath(file_path)
    file_name = os.path.basename(abs_path)
    
    # 打开聊天窗口
    success, err = find_and_open_chat(contact_name)
    if not success:
        return False, err
    
    wechat_win = get_chat_window()
    if not wechat_win:
        return False, "未找到聊天窗口"
    
    try:
        import subprocess
        import win32gui
        import win32con
        
        # 1. 确保微信窗口不是最大化，调整大小到屏幕右侧
        screen_width, screen_height = pyautogui.size()
        safe_print(f"[信息] 屏幕分辨率: {screen_width}x{screen_height}")
        
        # 如果微信最大化，先恢复正常大小
        wechat_handle = win32gui.FindWindow(None, wechat_win.title)
        if wechat_handle:
            # 检查是否最大化
            placement = win32gui.GetWindowPlacement(wechat_handle)
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                safe_print("[信息] 微信窗口已最大化，恢复窗口大小")
                win32gui.ShowWindow(wechat_handle, win32con.SW_RESTORE)
                time.sleep(0.5)
            
            # 调整微信窗口到屏幕右侧 (占60%宽度)
            wechat_width = int(screen_width * 0.6)
            wechat_height = screen_height - 100
            wechat_x = screen_width - wechat_width
            wechat_y = 50
            
            win32gui.SetWindowPos(
                wechat_handle, win32con.HWND_TOP,
                wechat_x, wechat_y, wechat_width, wechat_height,
                win32con.SWP_SHOWWINDOW
            )
            time.sleep(0.5)
            
            # 更新窗口信息
            wechat_win = get_chat_window()
            safe_print(f"[信息] 微信窗口位置: ({wechat_win.left}, {wechat_win.top}) {wechat_win.width}x{wechat_win.height}")
        
        # 2. 打开资源管理器并选中文件
        explorer_cmd = f'explorer /select,"{abs_path}"'
        subprocess.Popen(explorer_cmd, shell=True)
        time.sleep(2.0)
        
        # 3. 找到资源管理器窗口
        explorer_win = None
        for w in gw.getAllWindows():
            if w.title and w.width > 400 and w.height > 300:
                if file_name in w.title or os.path.dirname(abs_path) in w.title:
                    explorer_win = w
                    break
        
        if not explorer_win:
            # 备选：找最近打开的不是微信的窗口
            for w in gw.getAllWindows():
                if w.isActive and w.width > 400 and "微信" not in w.title:
                    explorer_win = w
                    break
        
        if not explorer_win:
            return False, "无法找到资源管理器窗口"
        
        safe_print(f"[信息] 资源管理器: {explorer_win.title}")
        
        # 4. 调整资源管理器窗口到屏幕左侧
        explorer_handle = win32gui.FindWindow(None, explorer_win.title)
        if explorer_handle:
            explorer_width = int(screen_width * 0.35)
            explorer_height = screen_height - 100
            explorer_x = 0
            explorer_y = 50
            
            win32gui.SetWindowPos(
                explorer_handle, win32con.HWND_TOP,
                explorer_x, explorer_y, explorer_width, explorer_height,
                win32con.SWP_SHOWWINDOW
            )
            time.sleep(0.5)
            
            # 更新窗口信息
            for w in gw.getAllWindows():
                if w.title == explorer_win.title:
                    explorer_win = w
                    break
            
            safe_print(f"[信息] 资源管理器位置: ({explorer_win.left}, {explorer_win.top}) {explorer_win.width}x{explorer_win.height}")
        
        # 5. 在资源管理器中确保文件被选中
        safe_print("[信息] 选中文件...")
        
        # 先点击文件列表区域确保焦点
        list_area_x = explorer_win.left + explorer_win.width // 2
        list_area_y = explorer_win.top + 150
        pyautogui.click(list_area_x, list_area_y)
        time.sleep(0.3)
        
        # 使用 Ctrl+A 选中所有（或者选中的文件）
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('a')
        pyautogui.keyUp('a')
        pyautogui.keyUp('ctrl')
        time.sleep(0.3)
        
        # 再点击具体文件位置确保选中
        file_click_x = explorer_win.left + explorer_win.width // 2
        file_click_y = explorer_win.top + 200
        
        safe_print(f"[信息] 点击文件: ({file_click_x}, {file_click_y})")
        pyautogui.click(file_click_x, file_click_y)
        time.sleep(0.5)
        
        # 6. 拖拽到微信输入框
        # 微信输入框位置（底部中央）
        drop_x = wechat_win.left + wechat_win.width // 2
        drop_y = wechat_win.top + wechat_win.height - 150
        
        safe_print(f"[信息] 拖拽到微信: ({drop_x}, {drop_y})")
        safe_print("[信息] 开始拖拽...")
        
        # 从选中的文件位置开始拖拽
        pyautogui.moveTo(file_click_x, file_click_y, duration=0.3)
        pyautogui.mouseDown()
        time.sleep(0.5)
        
        # 缓慢移动到微信窗口
        pyautogui.moveTo(drop_x, drop_y, duration=1.0)
        time.sleep(0.5)
        
        pyautogui.mouseUp()
        time.sleep(1.5)  # 等待文件加载
        
        safe_print("[信息] 拖拽完成")
        
        # 备选方案：如果拖拽没有成功（检查文件是否在输入框）
        # 尝试使用复制粘贴方式
        time.sleep(1.0)
        
        # 重新选中文件并复制
        safe_print("[信息] 尝试备选方案: 复制粘贴")
        pyautogui.click(file_click_x, file_click_y)
        time.sleep(0.3)
        
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('c')
        pyautogui.keyUp('c')
        pyautogui.keyUp('ctrl')
        time.sleep(0.5)
        
        # 激活微信并粘贴
        wechat_win.activate()
        time.sleep(0.3)
        
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('v')
        pyautogui.keyUp('v')
        pyautogui.keyUp('ctrl')
        time.sleep(1.0)
        
        # 7. 关闭资源管理器
        try:
            explorer_win.close()
            time.sleep(0.3)
        except:
            pass
        
        # 8. 确保微信激活并发送
        wechat_win.activate()
        time.sleep(0.5)
        
        # 9. 如果有附带消息
        if message:
            safe_print("[信息] 添加附带消息")
            input_x = wechat_win.left + wechat_win.width // 2
            input_y = wechat_win.top + wechat_win.height - 60
            pyautogui.click(input_x, input_y)
            time.sleep(0.3)
            
            if not set_clipboard_text(message):
                return False, "剪贴板设置失败"
            
            time.sleep(0.2)
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('v')
            pyautogui.keyUp('v')
            pyautogui.keyUp('ctrl')
            time.sleep(0.5)
        
        # 10. 发送
        pyautogui.press('enter')
        time.sleep(1.0)
        
        safe_print(f"[成功] 文件已发送: {file_name}")
        return True, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"发送文件失败: {str(e)}"


# ==================== 语音处理 ====================

def convert_audio(input_path, output_path, output_format):
    """转换音频格式"""
    try:
        # 检查ffmpeg
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            return False, "ffmpeg不可用"
        
        # 转换
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            output_path
        ], check=True, capture_output=True)
        
        return True, None
        
    except Exception as e:
        return False, f"转换失败: {str(e)}"


def send_voice_to_contact(contact_name, audio_path):
    """发送语音消息"""
    safe_print(f"[操作] 发送语音: {audio_path} -> {contact_name}")
    
    # 验证文件
    if not os.path.exists(audio_path):
        return False, f"音频文件不存在: {audio_path}"
    
    # 打开聊天窗口
    success, err = find_and_open_chat(contact_name)
    if not success:
        return False, err
    
    try:
        # 粘贴文件
        set_clipboard_text(audio_path)
        time.sleep(0.3)
        
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('v')
        pyautogui.keyUp('v')
        pyautogui.keyUp('ctrl')
        time.sleep(1.0)
        
        pyautogui.press('enter')
        time.sleep(1.0)
        
        safe_print(f"[成功] 语音已发送")
        return True, None
        
    except Exception as e:
        return False, f"发送语音失败: {str(e)}"


# ==================== 语音通话 ====================

class CallStatus(Enum):
    IDLE = "idle"
    DIALING = "dialing"
    CONNECTED = "connected"
    ENDED = "ended"


@dataclass
class CallSession:
    call_id: str
    caller: str
    callee: str
    status: CallStatus
    start_time: float


# 全局通话管理
active_calls = {}


def start_voice_call(contact_name, timeout=30):
    """发起语音通话"""
    safe_print(f"[操作] 发起语音通话: {contact_name}")
    
    call_id = str(uuid.uuid4())[:8]
    
    # 打开聊天窗口
    success, err = find_and_open_chat(contact_name)
    if not success:
        return None, err
    
    win = get_chat_window()
    if not win:
        return None, "未找到聊天窗口"
    
    try:
        # 点击语音通话按钮（右上角区域）
        call_x = win.left + win.width - 80
        call_y = win.top + 60
        
        pyautogui.click(call_x, call_y)
        time.sleep(0.5)
        
        # 选择语音通话（向下一点）
        pyautogui.click(call_x, call_y + 40)
        time.sleep(0.5)
        
        # 记录通话
        session = CallSession(
            call_id=call_id,
            caller="me",
            callee=contact_name,
            status=CallStatus.DIALING,
            start_time=time.time()
        )
        active_calls[call_id] = session
        
        safe_print(f"[成功] 通话已发起，ID: {call_id}")
        return call_id, None
        
    except Exception as e:
        return None, f"发起通话失败: {str(e)}"


def end_voice_call(call_id):
    """结束语音通话"""
    safe_print(f"[操作] 结束通话: {call_id}")
    
    if call_id not in active_calls:
        return False, f"通话 {call_id} 不存在"
    
    try:
        # 按ESC挂断
        pyautogui.keyDown('esc')
        pyautogui.keyUp('esc')
        time.sleep(0.5)
        
        # 更新状态
        session = active_calls[call_id]
        session.status = CallStatus.ENDED
        del active_calls[call_id]
        
        safe_print(f"[成功] 通话已结束")
        return True, None
        
    except Exception as e:
        return False, f"结束通话失败: {str(e)}"


def accept_voice_call(caller):
    """接听语音通话"""
    safe_print(f"[操作] 接听来电: {caller}")
    
    call_id = str(uuid.uuid4())[:8]
    
    try:
        # 点击接听按钮（屏幕中央偏左）
        screen_width, screen_height = pyautogui.size()
        accept_x = screen_width // 2 - 60
        accept_y = screen_height // 2
        
        pyautogui.click(accept_x, accept_y)
        time.sleep(0.5)
        
        # 记录通话
        session = CallSession(
            call_id=call_id,
            caller=caller,
            callee="me",
            status=CallStatus.CONNECTED,
            start_time=time.time()
        )
        active_calls[call_id] = session
        
        return call_id, None
        
    except Exception as e:
        return None, f"接听失败: {str(e)}"


def get_call_status(call_id):
    """获取通话状态"""
    if call_id in active_calls:
        session = active_calls[call_id]
        return {
            "call_id": call_id,
            "status": session.status.value,
            "caller": session.caller,
            "callee": session.callee,
            "duration": time.time() - session.start_time
        }
    return None


# ==================== 状态查询 ====================

def get_wechat_status():
    """获取微信状态"""
    win = get_wechat_window()
    if not win:
        return {"status": "not_running", "message": "微信未运行"}
    
    chat_win = get_chat_window()
    return {
        "status": "running",
        "has_chat": chat_win is not None,
        "active_calls": len(active_calls),
        "version": "4.0.0"
    }


def get_contact_list():
    """获取联系人列表（简化版）"""
    return {
        "contacts": [
            {"name": "文件传输助手", "type": "helper"},
        ],
        "note": "请通过微信界面查看完整联系人列表"
    }


# ==================== MCP Tools 定义 ====================

TOOLS = [
    {
        "name": "wechat_get_status",
        "description": "获取微信运行状态",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "wechat_get_contacts",
        "description": "获取联系人列表",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "wechat_send_message",
        "description": "发送文本消息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "消息内容"},
                "contact": {"type": "string", "description": "联系人名称（可选）"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "wechat_send_file",
        "description": "发送文件给联系人",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "联系人名称"},
                "file_path": {"type": "string", "description": "文件路径"},
                "message": {"type": "string", "description": "附带消息（可选）"}
            },
            "required": ["contact", "file_path"]
        }
    },
    {
        "name": "wechat_send_voice",
        "description": "发送语音消息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "联系人名称"},
                "audio_path": {"type": "string", "description": "音频文件路径"}
            },
            "required": ["contact", "audio_path"]
        }
    },
    {
        "name": "wechat_convert_audio",
        "description": "转换音频格式（需要ffmpeg）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string"},
                "output_path": {"type": "string"},
                "output_format": {"type": "string"}
            },
            "required": ["input_path", "output_path", "output_format"]
        }
    },
    {
        "name": "wechat_start_call",
        "description": "发起语音通话",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "联系人名称"},
                "timeout": {"type": "integer", "default": 30}
            },
            "required": ["contact"]
        }
    },
    {
        "name": "wechat_end_call",
        "description": "结束语音通话",
        "inputSchema": {
            "type": "object",
            "properties": {
                "call_id": {"type": "string", "description": "通话ID"}
            },
            "required": ["call_id"]
        }
    },
    {
        "name": "wechat_accept_call",
        "description": "接听语音通话",
        "inputSchema": {
            "type": "object",
            "properties": {
                "caller": {"type": "string", "description": "来电者名称"}
            },
            "required": ["caller"]
        }
    },
    {
        "name": "wechat_get_call_status",
        "description": "获取通话状态",
        "inputSchema": {
            "type": "object",
            "properties": {
                "call_id": {"type": "string", "description": "通话ID"}
            },
            "required": ["call_id"]
        }
    }
]


# ==================== 工具处理函数 ====================

async def handle_tool(name, arguments):
    """处理工具调用"""
    
    safe_print(f"[工具调用] {name}")
    
    # 从参数或环境变量读取
    contact = arguments.get('contact', '') or os.environ.get('WECHAT_CONTACT', '')
    message = arguments.get('message', '') or os.environ.get('WECHAT_MESSAGE', '')
    file_path = arguments.get('file_path', '')
    audio_path = arguments.get('audio_path', '')
    call_id = arguments.get('call_id', '')
    caller = arguments.get('caller', '')
    input_path = arguments.get('input_path', '')
    output_path = arguments.get('output_path', '')
    output_format = arguments.get('output_format', 'mp3')
    timeout = arguments.get('timeout', 30)
    
    try:
        # ===== 状态查询 =====
        if name == "wechat_get_status":
            result = get_wechat_status()
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
        
        elif name == "wechat_get_contacts":
            result = get_contact_list()
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
        
        # ===== 消息发送 =====
        elif name == "wechat_send_message":
            if not message:
                return {"content": [{"type": "text", "text": "[ERROR] 需要消息内容"}]}
            
            if contact:
                success, err = send_message_to_contact(contact, message)
            else:
                success, err = input_message(message)
                if success:
                    success, err = send_message()
            
            if success:
                return {"content": [{"type": "text", "text": "[OK] 消息已发送"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        # ===== 文件发送 =====
        elif name == "wechat_send_file":
            if not contact or not file_path:
                return {"content": [{"type": "text", "text": "[ERROR] 需要联系人和文件路径"}]}
            
            success, err = send_file_to_contact(contact, file_path, message)
            
            if success:
                return {"content": [{"type": "text", "text": f"[OK] 文件已发送: {os.path.basename(file_path)}"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        # ===== 语音发送 =====
        elif name == "wechat_send_voice":
            if not contact or not audio_path:
                return {"content": [{"type": "text", "text": "[ERROR] 需要联系人和音频路径"}]}
            
            success, err = send_voice_to_contact(contact, audio_path)
            
            if success:
                return {"content": [{"type": "text", "text": "[OK] 语音已发送"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        # ===== 音频转换 =====
        elif name == "wechat_convert_audio":
            if not input_path or not output_path:
                return {"content": [{"type": "text", "text": "[ERROR] 需要输入和输出路径"}]}
            
            success, err = convert_audio(input_path, output_path, output_format)
            
            if success:
                return {"content": [{"type": "text", "text": f"[OK] 转换完成: {output_path}"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        # ===== 语音通话 =====
        elif name == "wechat_start_call":
            if not contact:
                return {"content": [{"type": "text", "text": "[ERROR] 需要联系人"}]}
            
            call_id, err = start_voice_call(contact, timeout)
            
            if call_id:
                return {"content": [{"type": "text", "text": f"[OK] 通话已发起，ID: {call_id}"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        elif name == "wechat_end_call":
            if not call_id:
                return {"content": [{"type": "text", "text": "[ERROR] 需要通话ID"}]}
            
            success, err = end_voice_call(call_id)
            
            if success:
                return {"content": [{"type": "text", "text": "[OK] 通话已结束"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        elif name == "wechat_accept_call":
            if not caller:
                return {"content": [{"type": "text", "text": "[ERROR] 需要来电者"}]}
            
            call_id, err = accept_voice_call(caller)
            
            if call_id:
                return {"content": [{"type": "text", "text": f"[OK] 已接听，ID: {call_id}"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        elif name == "wechat_get_call_status":
            if not call_id:
                return {"content": [{"type": "text", "text": "[ERROR] 需要通话ID"}]}
            
            status = get_call_status(call_id)
            
            if status:
                return {"content": [{"type": "text", "text": json.dumps(status, ensure_ascii=False)}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] 通话 {call_id} 不存在"}]}
        
        # ===== 未知命令 =====
        else:
            safe_print(f"[错误] 未知工具: {name}")
            return {"content": [{"type": "text", "text": f"[ERROR] 未知命令: {name}"}]}
    
    except Exception as e:
        import traceback
        safe_print(f"[错误] 工具调用异常: {e}")
        traceback.print_exc()
        return {"content": [{"type": "text", "text": f"[ERROR] {str(e)}"}]}


# ==================== MCP 主循环 ====================

async def main():
    """MCP 主循环"""
    safe_print("=" * 60)
    safe_print("WeChat MCP Enhanced Server v4.0.0")
    safe_print("支持功能:")
    safe_print("  - 文本消息发送")
    safe_print("  - 文件传输")
    safe_print("  - 语音消息")
    safe_print("  - 语音通话")
    safe_print("=" * 60)
    safe_print("")
    safe_print("等待MCP连接...")
    safe_print("")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            request = json.loads(line)
            method = request.get("method")
            req_id = request.get("id")
            
            # ===== 初始化 =====
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "wechat-mcp-enhanced",
                            "version": "4.0.0"
                        }
                    }
                }
                print(json.dumps(response), flush=True)
                safe_print("[MCP] 已初始化")
            
            elif method == "notifications/initialized":
                pass
            
            # ===== 工具列表 =====
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS}
                }
                print(json.dumps(response), flush=True)
                safe_print(f"[MCP] 返回工具列表 ({len(TOOLS)}个)")
            
            # ===== 工具调用 =====
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                safe_print(f"[MCP] 调用工具: {tool_name}")
                result = await handle_tool(tool_name, tool_args)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
                print(json.dumps(response, ensure_ascii=False), flush=True)
        
        except json.JSONDecodeError as e:
            safe_print(f"[错误] JSON解析失败: {e}")
            error = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"JSON解析错误: {e}"}
            }
            print(json.dumps(error), flush=True)
        
        except Exception as e:
            safe_print(f"[错误] 主循环异常: {e}")
            import traceback
            traceback.print_exc()
            error = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
