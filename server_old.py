# -*- coding: utf-8 -*-
import sys
import os
import json
import asyncio
import time
from pathlib import Path

import pyautogui
pyautogui.FAILSAFE = False
import pygetwindow as gw
from PIL import Image, ImageGrab
import pyperclip


# 功能性联系人优先级映射
# 当用户搜索短名称时，自动映射到微信中的完整名称
FUNCTIONAL_CONTACTS = {
    "文件传输": "文件传输助手",
    "文件传输助手": "文件传输助手",
    "文件": "文件传输助手",
}


def safe_print(text):
    """安全打印"""
    try:
        print(text, flush=True)
    except:
        pass


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
    """设置剪贴板"""
    try:
        pyperclip.copy(text)
        return True
    except:
        return False


def resolve_contact_name(contact_name):
    """
    解析联系人名称
    1. 优先匹配功能性联系人
    2. 返回优化后的搜索名称
    """
    # 先检查是否匹配功能性联系人
    if contact_name in FUNCTIONAL_CONTACTS:
        resolved = FUNCTIONAL_CONTACTS[contact_name]
        safe_print(f"[解析] '{contact_name}' -> '{resolved}' (功能性联系人)")
        return resolved
    
    return contact_name


def select_search_result(contact_name, max_attempts=5):
    """
    在搜索结果中选择最佳匹配项
    使用上下键浏览结果，优先选择完全匹配的项
    """
    time.sleep(0.5)  # 等待搜索结果显示
    
    # 获取可能的搜索结果（通过截图OCR或直接尝试导航）
    # 策略：先按Tab切换到结果列表，然后使用上下键选择
    
    # 如果直接匹配，直接回车
    if contact_name in ["文件传输助手"]:
        # 对于已知的功能性联系人，直接回车（通常在最上方）
        pyautogui.press('enter')
        return True
    
    # 对于其他联系人，尝试查找最佳匹配
    # 策略：按Tab进入列表，然后遍历结果
    pyautogui.press('tab')
    time.sleep(0.2)
    
    # 尝试最多max_attempts次导航来找到正确项
    for i in range(max_attempts):
        # 回车尝试打开当前选中项
        pyautogui.press('enter')
        time.sleep(0.8)
        
        # 检查是否打开了聊天窗口
        chat_win = get_chat_window()
        if chat_win:
            safe_print(f"[搜索] 第{i+1}次尝试成功")
            return True
        
        # 如果没打开，重新搜索并尝试下一个
        if i < max_attempts - 1:
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.3)
            pyautogui.keyDown('down')
            pyautogui.keyUp('down')
            time.sleep(0.2)
    
    return False


def find_and_open_chat(contact_name):
    """搜索并打开联系人"""
    safe_print(f"[搜索] 原始名称: '{contact_name}'")
    
    # 解析联系人名称（功能性联系人优先）
    search_name = resolve_contact_name(contact_name)
    safe_print(f"[搜索] 解析后名称: '{search_name}'")
    
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
    
    # 清空并输入搜索词
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)
    
    if not set_clipboard_text(search_name):
        return False, "剪贴板失败"
    
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.0)
    
    # 使用智能选择逻辑
    success = select_search_result(search_name)
    
    if not success:
        # 备用方案：直接回车
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


def get_wechat_status():
    """获取状态"""
    win = get_wechat_window()
    if not win:
        return {"status": "not_running"}
    return {"status": "running", "has_chat": get_chat_window() is not None}


# MCP 工具
TOOLS = [
    {
        "name": "wechat_get_status",
        "description": "获取微信状态",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "wechat_send_message",
        "description": "发送消息（中文从环境变量读取）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "contact": {"type": "string"}
            },
            "required": ["message"]
        }
    }
]


async def handle_tool(name, arguments):
    """处理工具调用"""
    
    # 从环境变量读取中文参数（避免命令行编码问题）
    contact = os.environ.get('WECHAT_CONTACT', arguments.get('contact', ''))
    message = os.environ.get('WECHAT_MESSAGE', arguments.get('message', ''))
    
    # 如果环境变量有值，优先使用
    if contact:
        safe_print(f"[INFO] 使用环境变量 contact: '{contact}'")
    if message:
        safe_print(f"[INFO] 使用环境变量 message: '{message}'")
    
    if name == "wechat_get_status":
        result = get_wechat_status()
        return {"content": [{"type": "text", "text": json.dumps(result)}]}
    
    elif name == "wechat_send_message":
        if not message:
            return {"content": [{"type": "text", "text": "[ERROR] 需要消息内容"}]}
        
        if contact:
            success, err = send_message_to_contact(contact, message)
        else:
            # 发给当前聊天
            success, err = input_message(message)
            if success:
                success, err = send_message()
        
        if success:
            return {"content": [{"type": "text", "text": "[OK] 已发送"}]}
        else:
            return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
    
    return {"content": [{"type": "text", "text": "[ERROR] 未知命令"}]}


async def main():
    """MCP 主循环"""
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
                            "name": "wechat-mcp",
                            "version": "3.2.0"
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
