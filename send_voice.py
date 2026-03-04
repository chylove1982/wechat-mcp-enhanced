# -*- coding: utf-8 -*-
"""
微信语音发送工具
"""
import sys
import os
import time
from pathlib import Path

import pyautogui
pyautogui.FAILSAFE = False
import pygetwindow as gw
import pyperclip
from PIL import Image


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
    """获取聊天窗口 - 使用更宽松的匹配"""
    # 尝试多种可能的窗口标题
    possible_titles = ["微信", "WeChat", "与", "肖"]
    
    for title in possible_titles:
        windows = gw.getWindowsWithTitle(title)
        for win in windows:
            if win.width > 300 and win.height > 200:
                return win
    
    # 如果没有匹配，返回任意一个足够大的窗口
    all_windows = gw.getAllWindows()
    for win in all_windows:
        if win.title and win.width > 400 and win.height > 400:
            return win
    
    return None


def find_and_open_chat(contact_name):
    """搜索并打开联系人"""
    safe_print(f"[INFO] Searching contact: {contact_name}")
    
    win = get_wechat_window()
    if not win:
        return False, "WeChat not running"
    
    try:
        win.activate()
        time.sleep(0.5)
    except Exception as e:
        return False, f"Cannot activate window: {e}"
    
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
    """发送语音文件"""
    win = get_chat_window()
    if not win:
        return False, "未找到聊天窗口"
    
    # 激活窗口
    try:
        win.activate()
        time.sleep(0.3)
    except:
        pass
    
    # 点击输入框位置（窗口底部中央）
    input_x = win.left + win.width // 2
    input_y = win.top + win.height - 80
    
    pyautogui.click(input_x, input_y)
    time.sleep(0.3)
    
    # 方式1: 直接粘贴文件路径发送
    pyperclip.copy(voice_file_path)
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    
    # 回车发送
    pyautogui.press('enter')
    time.sleep(0.5)
    
    return True, None


def main():
    # 从环境变量读取参数（避免命令行编码问题）
    contact = os.environ.get('WECHAT_CONTACT', sys.argv[1] if len(sys.argv) > 1 else '')
    voice_file = os.environ.get('WECHAT_VOICE', sys.argv[2] if len(sys.argv) > 2 else '')
    
    if not contact or not voice_file:
        print("Usage: python send_voice.py <contact> <voice_file>")
        print("   Or: set WECHAT_CONTACT and WECHAT_VOICE env vars")
        sys.exit(1)
    
    # 检查文件是否存在
    if not os.path.exists(voice_file):
        print(f"[错误] 文件不存在: {voice_file}")
        sys.exit(1)
    
    # 打开联系人
    success, err = find_and_open_chat(contact)
    if not success:
        print(f"[错误] 打开联系人失败: {err}")
        sys.exit(1)
    
    # 发送语音
    success, err = send_voice_message(voice_file)
    if not success:
        print(f"[错误] 发送语音失败: {err}")
        sys.exit(1)
    
    print("[OK] 语音已发送")


if __name__ == "__main__":
    main()
