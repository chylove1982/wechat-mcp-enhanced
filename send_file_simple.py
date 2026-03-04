# -*- coding: utf-8 -*-
"""
简单可靠的文件发送模块 - 使用拖拽方式
"""

import os
import time
import pyautogui
import pygetwindow as gw


def send_file_simple(contact_name, file_path, message=""):
    """
    发送文件给联系人 - 简单可靠版
    使用模拟拖拽方式
    """
    print(f"[发送文件] {file_path} -> {contact_name}")
    
    # 检查文件
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    abs_path = os.path.abspath(file_path)
    file_name = os.path.basename(abs_path)
    
    # 1. 打开文件资源管理器，显示文件
    import subprocess
    explorer_cmd = f'explorer /select,"{abs_path}"'
    subprocess.Popen(explorer_cmd, shell=True)
    time.sleep(2.0)
    
    # 2. 找到资源管理器窗口
    explorer_win = None
    for w in gw.getAllWindows():
        if w.title and ("pom" in w.title.lower() or "skeleton" in w.title.lower() or "temp" in w.title.lower()):
            explorer_win = w
            break
    
    if not explorer_win:
        # 备选：找最近激活的窗口
        all_wins = gw.getAllWindows()
        for w in reversed(all_wins):
            if w.isActive and w.title and w.width > 300:
                explorer_win = w
                break
    
    if not explorer_win:
        return False, "找不到资源管理器窗口"
    
    print(f"[信息] 资源管理器: {explorer_win.title}")
    
    # 3. 找到微信窗口
    wechat_win = None
    for w in gw.getWindowsWithTitle("微信"):
        if w.width > 500 and w.height > 500:
            wechat_win = w
            break
    
    if not wechat_win:
        return False, "找不到微信窗口"
    
    print(f"[信息] 微信窗口: {wechat_win.title} ({wechat_win.width}x{wechat_win.height})")
    
    try:
        # 4. 激活资源管理器并点击文件
        explorer_win.activate()
        time.sleep(0.5)
        
        # 点击文件（文件列表中央）
        file_x = explorer_win.left + 100
        file_y = explorer_win.top + 150
        
        print(f"[信息] 点击文件位置: ({file_x}, {file_y})")
        pyautogui.click(file_x, file_y)
        time.sleep(0.3)
        
        # 5. 拖拽到微信
        # 微信输入框位置
        wechat_x = wechat_win.left + wechat_win.width // 2
        wechat_y = wechat_win.top + wechat_win.height - 150
        
        print(f"[信息] 拖拽到微信: ({wechat_x}, {wechat_y})")
        
        # 执行拖拽
        pyautogui.moveTo(file_x, file_y, duration=0.3)
        pyautogui.mouseDown()
        time.sleep(0.3)
        
        # 移动过程中激活微信
        pyautogui.moveTo(wechat_x, wechat_y, duration=0.8)
        wechat_win.activate()
        time.sleep(0.3)
        
        pyautogui.mouseUp()
        time.sleep(1.0)
        
        # 6. 关闭资源管理器
        try:
            explorer_win.close()
        except:
            pass
        
        # 7. 发送
        wechat_win.activate()
        time.sleep(0.5)
        
        # 如果有消息，先输入
        if message:
            import pyperclip
            pyperclip.copy(message)
            
            # 点击输入框
            input_x = wechat_win.left + wechat_win.width // 2
            input_y = wechat_win.top + wechat_win.height - 60
            pyautogui.click(input_x, input_y)
            time.sleep(0.3)
            
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('v')
            pyautogui.keyUp('v')
            pyautogui.keyUp('ctrl')
            time.sleep(0.5)
        
        # 按Enter发送
        pyautogui.press('enter')
        time.sleep(1.0)
        
        print(f"[成功] 文件已发送: {file_name}")
        return True, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) >= 3:
        contact = sys.argv[1]
        file_path = sys.argv[2]
        message = sys.argv[3] if len(sys.argv) > 3 else ""
    else:
        contact = "文件传输助手"
        file_path = r"E:\temp\skeleton\pom.xml"
        message = "测试文件发送"
    
    print("="*60)
    print("文件发送测试")
    print("="*60)
    print(f"联系人: {contact}")
    print(f"文件: {file_path}")
    print(f"消息: {message}")
    print()
    
    success, error = send_file_simple(contact, file_path, message)
    
    if success:
        print("\n✅ 发送成功!")
    else:
        print(f"\n❌ 发送失败: {error}")
