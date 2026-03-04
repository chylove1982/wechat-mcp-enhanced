# -*- coding: utf-8 -*-
"""
WeChat MCP Server - 简化版（专注修复文件发送）
"""

import sys
import os
import json
import asyncio
import time
import subprocess
import uuid
from enum import Enum
from dataclasses import dataclass

import pyautogui
pyautogui.FAILSAFE = False
import pygetwindow as gw
import pyperclip


def safe_print(text):
    try:
        print(text, flush=True)
    except:
        pass


# ==================== 窗口管理 ====================

def get_wechat_window():
    wins = gw.getWindowsWithTitle("微信")
    for w in wins:
        if w.width > 500 and w.height > 500:
            return w
    return None


def get_chat_window():
    windows = gw.getWindowsWithTitle("Dragon")
    for win in windows:
        if "Dragon" in win.title:
            return win
    return get_wechat_window()


def set_clipboard_text(text):
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        safe_print(f"[错误] 剪贴板失败: {e}")
        return False


# ==================== 核心功能 ====================

def find_and_open_chat(contact_name):
    safe_print(f"[操作] 搜索联系人: {contact_name}")
    
    win = get_wechat_window()
    if not win:
        return False, "微信未运行"
    
    try:
        win.activate()
        time.sleep(0.5)
    except Exception as e:
        return False, f"无法激活窗口: {e}"
    
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)
    
    if not set_clipboard_text(contact_name):
        return False, "剪贴板失败"
    
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.0)
    
    pyautogui.press('enter')
    time.sleep(1.0)
    
    if not get_chat_window():
        return False, "未打开聊天窗口"
    
    safe_print(f"[成功] 已打开聊天: {contact_name}")
    return True, None


# ==================== 文件发送（修复版）====================

def send_file_to_contact(contact_name, file_path, message=""):
    """发送文件 - 使用最可靠的复制粘贴方式"""
    safe_print(f"[操作] 发送文件: {file_path} -> {contact_name}")
    
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
        
        # 1. 调整微信窗口
        screen_width, screen_height = pyautogui.size()
        wechat_handle = win32gui.FindWindow(None, wechat_win.title)
        
        if wechat_handle:
            # 恢复最大化窗口
            placement = win32gui.GetWindowPlacement(wechat_handle)
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                win32gui.ShowWindow(wechat_handle, win32con.SW_RESTORE)
                time.sleep(0.3)
            
            # 窗口放右侧
            win32gui.SetWindowPos(
                wechat_handle, win32con.HWND_TOP,
                int(screen_width * 0.4), 50,
                int(screen_width * 0.58), screen_height - 100,
                win32con.SWP_SHOWWINDOW
            )
            time.sleep(0.3)
        
        # 2. 打开资源管理器并选中文件
        explorer_cmd = f'explorer /select,"{abs_path}"'
        subprocess.Popen(explorer_cmd, shell=True)
        time.sleep(3.0)  # 等待打开
        
        # 3. 找到资源管理器窗口
        explorer_win = None
        for _ in range(10):
            for w in gw.getAllWindows():
                if w.title and w.width > 400:
                    if file_name in w.title or os.path.basename(os.path.dirname(abs_path)) in w.title:
                        explorer_win = w
                        break
            if explorer_win:
                break
            time.sleep(0.5)
        
        if not explorer_win:
            return False, "找不到资源管理器窗口"
        
        safe_print(f"[信息] 资源管理器: {explorer_win.title}")
        
        # 调整资源管理器到左侧
        explorer_handle = win32gui.FindWindow("CabinetWClass", None)
        if explorer_handle:
            win32gui.SetWindowPos(
                explorer_handle, win32con.HWND_TOP,
                0, 50,
                int(screen_width * 0.38), screen_height - 100,
                win32con.SWP_SHOWWINDOW
            )
            time.sleep(0.3)
        
        # 4. 在资源管理器中选择并复制文件
        explorer_win.activate()
        time.sleep(0.5)
        
        # 点击文件区域
        file_x = explorer_win.left + explorer_win.width // 2
        file_y = explorer_win.top + 200
        pyautogui.click(file_x, file_y)
        time.sleep(0.3)
        
        # 选中所有（Ctrl+A）
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('a')
        pyautogui.keyUp('a')
        pyautogui.keyUp('ctrl')
        time.sleep(0.3)
        
        # 再次点击确保选中
        pyautogui.click(file_x, file_y)
        time.sleep(0.3)
        
        # 复制文件 (Ctrl+C)
        safe_print("[信息] 复制文件到剪贴板...")
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('c')
        pyautogui.keyUp('c')
        pyautogui.keyUp('ctrl')
        time.sleep(1.0)  # 等待复制完成
        
        # 5. 关闭资源管理器
        try:
            explorer_win.close()
            time.sleep(0.5)
        except:
            pass
        
        # 6. 激活微信并粘贴
        wechat_win.activate()
        time.sleep(0.5)
        
        # 点击输入框
        input_x = wechat_win.left + wechat_win.width // 2
        input_y = wechat_win.top + wechat_win.height - 150
        pyautogui.click(input_x, input_y)
        time.sleep(0.3)
        
        # 粘贴 (Ctrl+V)
        safe_print("[信息] 粘贴文件到微信...")
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('v')
        pyautogui.keyUp('v')
        pyautogui.keyUp('ctrl')
        
        # 关键：等待文件加载（3秒）
        safe_print("[信息] 等待文件加载...")
        time.sleep(3.0)
        
        # 7. 添加消息（如果有）
        if message:
            safe_print("[信息] 添加附带消息")
            pyautogui.click(input_x, input_y)
            time.sleep(0.3)
            
            if not set_clipboard_text(message):
                return False, "剪贴板失败"
            
            time.sleep(0.2)
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('v')
            pyautogui.keyUp('v')
            pyautogui.keyUp('ctrl')
            time.sleep(0.5)
        
        # 8. 发送（按两次Enter）
        safe_print("[信息] 发送...")
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(1.0)
        
        safe_print(f"[成功] 文件已发送: {file_name}")
        return True, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"发送失败: {str(e)}"


# ==================== 其他功能（简化）====================

def send_message_to_contact(contact_name, message):
    success, err = find_and_open_chat(contact_name)
    if not success:
        return False, err
    
    win = get_chat_window()
    if not win:
        return False, "未找到窗口"
    
    input_x = win.left + win.width // 2
    input_y = win.top + win.height - 60
    pyautogui.click(input_x, input_y)
    time.sleep(0.3)
    
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)
    
    if not set_clipboard_text(message):
        return False, "剪贴板失败"
    
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    
    return True, None


def get_wechat_status():
    win = get_wechat_window()
    if not win:
        return {"status": "not_running"}
    return {"status": "running", "has_chat": get_chat_window() is not None}


# ==================== MCP ====================

TOOLS = [
    {
        "name": "wechat_get_status",
        "description": "获取微信状态",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "wechat_send_message",
        "description": "发送消息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "contact": {"type": "string"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "wechat_send_file",
        "description": "发送文件",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string"},
                "file_path": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["contact", "file_path"]
        }
    }
]


async def handle_tool(name, arguments):
    safe_print(f"[工具] {name}")
    
    contact = arguments.get('contact', '')
    message = arguments.get('message', '')
    file_path = arguments.get('file_path', '')
    
    try:
        if name == "wechat_get_status":
            result = get_wechat_status()
            return {"content": [{"type": "text", "text": json.dumps(result)}]}
        
        elif name == "wechat_send_message":
            if not message:
                return {"content": [{"type": "text", "text": "[ERROR] 需要消息"}]}
            
            success, err = send_message_to_contact(contact, message)
            
            if success:
                return {"content": [{"type": "text", "text": "[OK] 已发送"}]}
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
        
        else:
            return {"content": [{"type": "text", "text": f"[ERROR] 未知命令: {name}"}]}
    
    except Exception as e:
        return {"content": [{"type": "text", "text": f"[ERROR] {str(e)}"}]}


async def main():
    safe_print("="*60)
    safe_print("WeChat MCP Server - 修复版")
    safe_print("="*60)
    
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
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "wechat-mcp",
                            "version": "4.1.0"
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
                result = await handle_tool(params.get("name"), params.get("arguments", {}))
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
                print(json.dumps(response, ensure_ascii=False), flush=True)
        
        except Exception as e:
            error = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
