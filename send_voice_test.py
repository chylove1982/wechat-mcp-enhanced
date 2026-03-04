# -*- coding: utf-8 -*-
"""
微信语音发送工具 - 测试版本（硬编码联系人）
"""
import sys
import os
import time
from pathlib import Path

import pyautogui
pyautogui.FAILSAFE = False
import pygetwindow as gw
import pyperclip


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
    possible_titles = ["微信", "WeChat"]
    for title in possible_titles:
        windows = gw.getWindowsWithTitle(title)
        for win in windows:
            if win.width > 300 and win.height > 200:
                return win
    return None


def find_and_open_chat(contact_name):
    """搜索并打开联系人"""
    safe_print(f"[INFO] Searching contact...")
    
    win = get_wechat_window()
    if not win:
        return False, "WeChat not running"
    
    # 尝试激活，但不强制要求成功
    try:
        if win.isMinimized:
            win.restore()
            time.sleep(0.3)
        win.activate()
        time.sleep(0.5)
    except Exception as e:
        safe_print(f"[WARN] Activate warning: {e}")
        # 继续尝试，不终止
    
    # 确保窗口在最前
    try:
        win.topmost = True
        time.sleep(0.2)
        win.topmost = False
    except:
        pass
    
    # Ctrl+F 搜索
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    
    # 清空并输入
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.press('delete')
    time.sleep(0.1)
    
    # 输入联系人名称
    pyperclip.copy(contact_name)
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.0)
    
    # 回车打开
    pyautogui.press('enter')
    time.sleep(1.0)
    
    chat_win = get_chat_window()
    if not chat_win:
        return False, "Chat window not opened"
    
    return True, None


def send_voice_message(voice_file_path):
    """发送语音文件 - 使用拖拽方式"""
    win = get_chat_window()
    if not win:
        return False, "Chat window not found"
    
    try:
        win.activate()
        time.sleep(0.3)
    except:
        pass
    
    # 方法：打开文件选择对话框 (Ctrl+O 或点击附件按钮)
    # 先尝试使用 Alt+O 或点击文件传输按钮
    
    # 点击输入框位置获取焦点
    input_x = win.left + win.width // 2
    input_y = win.top + win.height - 80
    pyautogui.click(input_x, input_y)
    time.sleep(0.3)
    
    # 方法1: 使用剪贴板直接复制文件（Windows 资源管理器方式）
    # 需要导入必要的库来操作剪贴板文件
    try:
        import win32clipboard
        import win32con
        
        # 将文件放入剪贴板
        files = [voice_file_path.replace('/', '\\')]
        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        
        # 使用 CF_HDROP 格式
        # 构造 DROPFILES 结构
        files_str = '\x00'.join(files) + '\x00\x00'
        
        # 简单的文件列表格式 (CF_HDROP 模拟)
        # 实际应用中需要使用正确的 DROPFILES 结构
        # 这里简化处理，使用拖拽方式
        win32clipboard.CloseClipboard()
    except:
        pass
    
    # 方法2: 使用拖拽 - 打开文件资源管理器，拖拽文件到聊天窗口
    # 先打开文件资源管理器选择文件
    safe_print(f"[INFO] Opening file dialog...")
    
    # 使用 Alt+O 打开文件对话框 (部分微信版本支持)
    pyautogui.keyDown('alt')
    pyautogui.keyDown('o')
    pyautogui.keyUp('o')
    pyautogui.keyUp('alt')
    time.sleep(1.0)
    
    # 输入文件路径
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyperclip.copy(voice_file_path.replace('/', '\\'))
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    
    # 按回车选择文件
    pyautogui.press('enter')
    time.sleep(0.5)
    
    # 再次回车发送
    pyautogui.press('enter')
    time.sleep(0.5)
    
    return True, None


def main():
    # 硬编码联系人和语音文件路径
    contact = "肖"
    voice_file = "C:\\mcp\\winautowx\\temp\\test_voice.mp3"
    
    safe_print(f"[INFO] Voice file: {voice_file}")
    
    # 检查文件是否存在
    if not os.path.exists(voice_file):
        print(f"[ERROR] File not found: {voice_file}")
        sys.exit(1)
    
    # 打开联系人
    safe_print("[INFO] Opening contact...")
    success, err = find_and_open_chat(contact)
    if not success:
        print(f"[ERROR] Failed to open contact: {err}")
        sys.exit(1)
    
    # 发送语音
    safe_print("[INFO] Sending voice...")
    success, err = send_voice_message(voice_file)
    if not success:
        print(f"[ERROR] Failed to send voice: {err}")
        sys.exit(1)
    
    print("[OK] Voice sent successfully")


if __name__ == "__main__":
    main()
