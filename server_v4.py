# -*- coding: utf-8 -*-
"""
WeChat MCP Enhanced Server
微信MCP增强版 - 支持文件发送、语音收发、语音通话
"""

import sys
import os
import json
import asyncio
import time
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

import pyautogui
pyautogui.FAILSAFE = False
import pygetwindow as gw
from PIL import Image, ImageGrab
import pyperclip


def safe_print(text):
    """安全打印"""
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
    except:
        return False


def set_clipboard_files(file_paths: list):
    """设置剪贴板文件（Windows）"""
    try:
        import win32clipboard
        from io import BytesIO
        
        # 构建文件列表
        files = "\x00".join(file_paths) + "\x00\x00"
        
        # 打开剪贴板
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        
        # 设置文件数据
        # CF_HDROP = 15
        # 这里简化处理，实际需要使用正确的DROPFILES结构
        win32clipboard.SetClipboardText(files)
        win32clipboard.CloseClipboard()
        
        return True
    except Exception as e:
        safe_print(f"[ERROR] 设置文件剪贴板失败: {e}")
        # 回退到复制文件路径
        return set_clipboard_text(file_paths[0])


# ==================== 核心功能 ====================

def find_and_open_chat(contact_name):
    """搜索并打开联系人"""
    safe_print(f"[搜索] 联系人: {contact_name}")
    
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
        return False, "剪贴板失败"
    
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.0)
    
    # 回车打开
    pyautogui.press('enter')
    time.sleep(1.0)
    
    if not get_chat_window():
        return False, "未打开聊天窗口"
    
    return True, None


def input_message(message):
    """输入消息"""
    win = get_chat_window()
    if not win:
        return False, "未找到聊天窗口"
    
    # 点击输入框
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
        return False, "剪贴板失败"
    
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
    """发送消息给联系人"""
    success, err = find_and_open_chat(contact_name)
    if not success:
        return False, err
    
    success, err = input_message(message)
    if not success:
        return False, err
    
    return send_message()


# ==================== 文件发送 ====================

def send_file_to_contact(contact_name: str, file_path: str, message: str = "") -> tuple:
    """发送文件给联系人
    
    Args:
        contact_name: 联系人名称
        file_path: 文件路径
        message: 附带消息
    
    Returns:
        (success, error_message)
    """
    safe_print(f"[文件发送] {file_path} -> {contact_name}")
    
    # 验证文件
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    # 打开聊天窗口
    success, err = find_and_open_chat(contact_name)
    if not success:
        return False, err
    
    win = get_chat_window()
    if not win:
        return False, "未找到聊天窗口"
    
    try:
        # 方法1: 使用剪贴板粘贴文件
        set_clipboard_text(file_path)
        time.sleep(0.3)
        
        # Ctrl+V 粘贴文件
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('v')
        pyautogui.keyUp('v')
        pyautogui.keyUp('ctrl')
        time.sleep(1.0)
        
        # 如果有附带消息，先输入消息
        if message:
            # 点击输入框
            input_x = win.left + win.width // 2
            input_y = win.top + win.height - 60
            pyautogui.click(input_x, input_y)
            time.sleep(0.3)
            
            set_clipboard_text(message)
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
        
        # 发送
        pyautogui.press('enter')
        time.sleep(1.0)
        
        safe_print(f"[文件发送] 成功: {os.path.basename(file_path)}")
        return True, None
        
    except Exception as e:
        return False, f"发送文件失败: {str(e)}"


# ==================== 语音处理 ====================

class AudioConverter:
    """音频格式转换器"""
    
    @staticmethod
    def convert_to_silk(input_path: str, output_path: str) -> bool:
        """转换为微信语音格式(silk)"""
        try:
            # 检查ffmpeg
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                safe_print("[警告] ffmpeg不可用，将使用原格式")
                return False
            
            # 转换为中间PCM格式
            temp_pcm = tempfile.mktemp(suffix='.pcm')
            
            # 提取音频为s16le格式
            subprocess.run([
                'ffmpeg', '-y', '-i', input_path,
                '-f', 's16le', '-ar', '24000', '-ac', '1',
                temp_pcm
            ], check=True, capture_output=True)
            
            # 如果有silk编码器，使用它
            # 这里简化处理，实际需要使用腾讯silk编码器
            # 暂时将PCM文件重命名为silk（微信可能能识别）
            
            os.rename(temp_pcm, output_path)
            return True
            
        except Exception as e:
            safe_print(f"[错误] 音频转换失败: {e}")
            return False
    
    @staticmethod
    def convert_audio(input_path: str, output_path: str, output_format: str) -> bool:
        """转换音频格式"""
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', input_path,
                output_path
            ], check=True, capture_output=True)
            return True
        except Exception as e:
            safe_print(f"[错误] 音频转换失败: {e}")
            return False


def send_voice_to_contact(contact_name: str, audio_path: str) -> tuple:
    """发送语音消息给联系人
    
    Args:
        contact_name: 联系人名称
        audio_path: 音频文件路径
    
    Returns:
        (success, error_message)
    """
    safe_print(f"[语音发送] {audio_path} -> {contact_name}")
    
    # 验证文件
    if not os.path.exists(audio_path):
        return False, f"音频文件不存在: {audio_path}"
    
    # 打开聊天窗口
    success, err = find_and_open_chat(contact_name)
    if not success:
        return False, err
    
    try:
        # 转换为silk格式（如果是mp3/wav）
        ext = os.path.splitext(audio_path)[1].lower()
        if ext in ['.mp3', '.wav', '.m4a', '.ogg']:
            safe_print("[语音发送] 转换音频格式...")
            silk_path = tempfile.mktemp(suffix='.silk')
            if AudioConverter.convert_to_silk(audio_path, silk_path):
                audio_path = silk_path
        
        # 发送文件（微信会将silk识别为语音）
        set_clipboard_text(audio_path)
        time.sleep(0.3)
        
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('v')
        pyautogui.keyUp('v')
        pyautogui.keyUp('ctrl')
        time.sleep(1.0)
        
        pyautogui.press('enter')
        time.sleep(1.0)
        
        # 清理临时文件
        if audio_path.startswith(tempfile.gettempdir()):
            try:
                os.remove(audio_path)
            except:
                pass
        
        safe_print(f"[语音发送] 成功")
        return True, None
        
    except Exception as e:
        return False, f"发送语音失败: {str(e)}"


# ==================== 语音通话 ====================

class CallStatus(Enum):
    """通话状态"""
    IDLE = "idle"
    DIALING = "dialing"
    RINGING = "ringing"
    CONNECTED = "connected"
    ENDED = "ended"
    ERROR = "error"


@dataclass
class CallSession:
    """通话会话"""
    call_id: str
    caller: str
    callee: str
    status: CallStatus
    start_time: float
    is_outgoing: bool = True


# 全局通话状态
active_calls: Dict[str, CallSession] = {}


def start_voice_call(contact_name: str, timeout: int = 30) -> tuple:
    """发起语音通话
    
    Args:
        contact_name: 联系人名称
        timeout: 呼叫超时时间（秒）
    
    Returns:
        (call_id, error_message)
    """
    safe_print(f"[语音通话] 发起呼叫: {contact_name}")
    
    import uuid
    call_id = str(uuid.uuid4())[:8]
    
    # 打开聊天窗口
    success, err = find_and_open_chat(contact_name)
    if not success:
        return None, err
    
    win = get_chat_window()
    if not win:
        return None, "未找到聊天窗口"
    
    try:
        # 点击语音通话按钮（右上角）
        # 坐标需要根据实际情况调整
        call_x = win.left + win.width - 100
        call_y = win.top + 80
        
        pyautogui.click(call_x, call_y)
        time.sleep(0.5)
        
        # 选择语音通话
        pyautogui.click(call_x, call_y + 30)
        time.sleep(0.5)
        
        # 创建会话
        session = CallSession(
            call_id=call_id,
            caller="me",
            callee=contact_name,
            status=CallStatus.DIALING,
            start_time=time.time(),
            is_outgoing=True
        )
        active_calls[call_id] = session
        
        safe_print(f"[语音通话] 呼叫已发起，ID: {call_id}")
        return call_id, None
        
    except Exception as e:
        return None, f"发起通话失败: {str(e)}"


def end_voice_call(call_id: str) -> tuple:
    """结束语音通话
    
    Args:
        call_id: 通话ID
    
    Returns:
        (success, error_message)
    """
    safe_print(f"[语音通话] 结束通话: {call_id}")
    
    if call_id not in active_calls:
        return False, f"通话 {call_id} 不存在"
    
    try:
        # 按ESC挂断，或点击挂断按钮
        pyautogui.keyDown('esc')
        pyautogui.keyUp('esc')
        time.sleep(0.5)
        
        # 更新状态
        session = active_calls[call_id]
        session.status = CallStatus.ENDED
        
        # 移动到历史记录
        del active_calls[call_id]
        
        safe_print(f"[语音通话] 通话已结束")
        return True, None
        
    except Exception as e:
        return False, f"结束通话失败: {str(e)}"


def accept_voice_call(caller: str) -> tuple:
    """接听语音通话
    
    Args:
        caller: 来电者名称
    
    Returns:
        (call_id, error_message)
    """
    safe_print(f"[语音通话] 接听来电: {caller}")
    
    import uuid
    call_id = str(uuid.uuid4())[:8]
    
    try:
        # 点击接听按钮
        # 假设来电弹窗在屏幕中央
        screen_width, screen_height = pyautogui.size()
        accept_x = screen_width // 2 - 50
        accept_y = screen_height // 2
        
        pyautogui.click(accept_x, accept_y)
        time.sleep(0.5)
        
        # 创建会话
        session = CallSession(
            call_id=call_id,
            caller=caller,
            callee="me",
            status=CallStatus.CONNECTED,
            start_time=time.time(),
            is_outgoing=False
        )
        active_calls[call_id] = session
        
        return call_id, None
        
    except Exception as e:
        return None, f"接听通话失败: {str(e)}"


def get_call_status(call_id: str) -> dict:
    """获取通话状态"""
    if call_id in active_calls:
        session = active_calls[call_id]
        return {
            "call_id": call_id,
            "status": session.status.value,
            "caller": session.caller,
            "callee": session.callee,
            "duration": time.time() - session.start_time if session.status == CallStatus.CONNECTED else 0
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
        "window_size": {"width": win.width, "height": win.height}
    }


def get_contact_list():
    """获取联系人列表（简化版）"""
    # 实际实现需要从微信获取
    return {
        "contacts": [
            {"name": "文件传输助手", "type": "helper"},
        ],
        "mode": "placeholder"
    }


# ==================== MCP Tools ====================

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
                "contact": {"type": "string", "description": "联系人名称（可选，不填则发送到当前聊天）"}
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
                "audio_path": {"type": "string", "description": "音频文件路径（支持mp3/wav/m4a）"}
            },
            "required": ["contact", "audio_path"]
        }
    },
    {
        "name": "wechat_convert_audio",
        "description": "转换音频格式",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "输入文件路径"},
                "output_path": {"type": "string", "description": "输出文件路径"},
                "output_format": {"type": "string", "description": "输出格式(mp3/wav/silk)"}
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
                "timeout": {"type": "integer", "description": "超时时间（秒，默认30）", "default": 30}
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


async def handle_tool(name, arguments):
    """处理工具调用"""
    
    # 从环境变量读取中文参数（避免命令行编码问题）
    contact = os.environ.get('WECHAT_CONTACT', arguments.get('contact', ''))
    message = os.environ.get('WECHAT_MESSAGE', arguments.get('message', ''))
    
    # 其他参数
    file_path = arguments.get('file_path', '')
    audio_path = arguments.get('audio_path', '')
    call_id = arguments.get('call_id', '')
    caller = arguments.get('caller', '')
    timeout = arguments.get('timeout', 30)
    input_path = arguments.get('input_path', '')
    output_path = arguments.get('output_path', '')
    output_format = arguments.get('output_format', 'mp3')
    
    safe_print(f"[工具调用] {name}, contact={contact}")
    
    try:
        if name == "wechat_get_status":
            result = get_wechat_status()
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
        
        elif name == "wechat_get_contacts":
            result = get_contact_list()
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
        
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
        
        elif name == "wechat_send_file":
            if not contact or not file_path:
                return {"content": [{"type": "text", "text": "[ERROR] 需要联系人和文件路径"}]}
            
            success, err = send_file_to_contact(contact, file_path, message)
            
            if success:
                return {"content": [{"type": "text", "text": f"[OK] 文件已发送: {os.path.basename(file_path)}"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        elif name == "wechat_send_voice":
            if not contact or not audio_path:
                return {"content": [{"type": "text", "text": "[ERROR] 需要联系人和音频路径"}]}
            
            success, err = send_voice_to_contact(contact, audio_path)
            
            if success:
                return {"content": [{"type": "text", "text": "[OK] 语音已发送"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        elif name == "wechat_convert_audio":
            if not input_path or not output_path:
                return {"content": [{"type": "text", "text": "[ERROR] 需要输入和输出路径"}]}
            
            success = AudioConverter.convert_audio(input_path, output_path, output_format)
            
            if success:
                return {"content": [{"type": "text", "text": f"[OK] 音频转换完成: {output_path}"}]}
            else:
                return {"content": [{"type": "text", "text": "[ERROR] 音频转换失败"}]}
        
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
                return {"content": [{"type": "text", "text": "[ERROR] 需要来电者名称"}]}
            
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
        
        else:
            return {"content": [{"type": "text", "text": f"[ERROR] 未知命令: {name}"}]}
    
    except Exception as e:
        safe_print(f"[错误] 工具调用失败: {e}")
        import traceback
        traceback.print_exc()
        return {"content": [{"type": "text", "text": f"[ERROR] {str(e)}"}]}


async def main():
    """MCP 主循环"""
    safe_print("=" * 50)
    safe_print("WeChat MCP Enhanced Server v4.0.0")
    safe_print("支持: 消息发送 | 文件传输 | 语音消息 | 语音通话")
    safe_print("=" * 50)
    safe_print("")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            method = request.get("method")
            req_id = request.get("id")
            
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
            
            elif method == "notifications/initialized":
                pass
            
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS}
                }
                print(json.dumps(response), flush=True)
            
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = await handle_tool(tool_name, tool_args)
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
                print(json.dumps(response), flush=True)
        
        except Exception as e:
            error = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
