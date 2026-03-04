# -*- coding: utf-8 -*-
"""
文件发送测试脚本 - 验证文件复制粘贴功能
"""

import os
import sys
import time

# 测试文件路径
test_file = r"E:\temp\skeleton\pom.xml"

def test_clipboard_file():
    """测试文件复制到剪贴板"""
    print("="*60)
    print("测试1: 文件复制到剪贴板")
    print("="*60)
    
    if not os.path.exists(test_file):
        print(f"❌ 文件不存在: {test_file}")
        return False
    
    print(f"✅ 文件存在: {test_file}")
    print(f"   文件大小: {os.path.getsize(test_file)} bytes")
    
    try:
        import win32clipboard
        import win32con
        import struct
        
        # 构建DROPFILES结构
        abs_path = os.path.abspath(test_file)
        file_list = abs_path + "\x00\x00"  # 双null结尾
        
        # DROPFILES结构 (20 bytes)
        # pFiles = 20 (offset to file list)
        # pt.x = 0
        # pt.y = 0
        # fNC = FALSE
        # fWide = TRUE (Unicode)
        dropfiles = struct.pack("<IIIII", 20, 0, 0, 0, 1)
        
        # 文件列表 (UTF-16LE编码)
        file_list_bytes = file_list.encode('utf-16le')
        
        # 合并
        data = dropfiles + file_list_bytes
        
        print(f"   DROPFILES大小: {len(dropfiles)} bytes")
        print(f"   文件列表大小: {len(file_list_bytes)} bytes")
        print(f"   总数据大小: {len(data)} bytes")
        
        # 设置剪贴板
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
        win32clipboard.CloseClipboard()
        
        print("✅ 文件已复制到剪贴板 (CF_HDROP格式)")
        return True
        
    except Exception as e:
        print(f"❌ 复制失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_clipboard_text():
    """测试普通文本复制"""
    print("\n" + "="*60)
    print("测试2: 普通文本复制")
    print("="*60)
    
    try:
        import pyperclip
        pyperclip.copy("测试文本 - 从test_clipboard.py")
        print("✅ 文本已复制到剪贴板")
        return True
    except Exception as e:
        print(f"❌ 文本复制失败: {e}")
        return False


def test_win32clipboard_text():
    """使用win32clipboard复制文本"""
    print("\n" + "="*60)
    print("测试3: win32clipboard复制文本")
    print("="*60)
    
    try:
        import win32clipboard
        import win32con
        
        text = "测试文本 - 使用win32clipboard"
        
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text.encode('utf-16le'))
        win32clipboard.CloseClipboard()
        
        print("✅ 文本已复制到剪贴板 (CF_UNICODETEXT格式)")
        return True
        
    except Exception as e:
        print(f"❌ 复制失败: {e}")
        return False


def test_read_clipboard():
    """读取剪贴板内容"""
    print("\n" + "="*60)
    print("测试4: 读取剪贴板")
    print("="*60)
    
    try:
        import win32clipboard
        import win32con
        
        win32clipboard.OpenClipboard()
        
        # 检查可用的格式
        formats = []
        cf = win32clipboard.EnumClipboardFormats(0)
        while cf:
            formats.append(cf)
            cf = win32clipboard.EnumClipboardFormats(cf)
        
        print(f"   可用格式: {formats}")
        print(f"   CF_HDROP = {win32con.CF_HDROP}")
        print(f"   CF_TEXT = {win32con.CF_TEXT}")
        print(f"   CF_UNICODETEXT = {win32con.CF_UNICODETEXT}")
        
        # 尝试读取文本
        try:
            text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            print(f"   文本内容: {text[:100]}...")
        except:
            print("   无法读取文本格式")
        
        # 检查是否有HDROP
        if win32con.CF_HDROP in formats:
            print("   ✅ 剪贴板包含HDROP格式 (文件)")
        else:
            print("   ❌ 剪贴板没有HDROP格式")
        
        win32clipboard.CloseClipboard()
        return True
        
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("剪贴板测试工具")
    print("="*60)
    print()
    
    results = []
    
    # 运行测试
    results.append(("文件复制(CF_HDROP)", test_clipboard_file()))
    results.append(("文本复制(pyperclip)", test_clipboard_text()))
    results.append(("文本复制(win32clipboard)", test_win32clipboard_text()))
    results.append(("读取剪贴板", test_read_clipboard()))
    
    # 结果汇总
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    print("\n" + "="*60)
    print("操作指南:")
    print("="*60)
    print()
    print("如果测试2或3通过:")
    print("  1. 运行测试后，打开微信")
    print("  2. 选择一个聊天窗口")
    print("  3. 按 Ctrl+V 粘贴")
    print("  4. 检查是否粘贴了文本")
    print()
    print("如果测试1通过:")
    print("  1. 运行测试后，打开资源管理器")
    print("  2. 选择一个文件夹")
    print("  3. 按 Ctrl+V")
    print("  4. 检查是否粘贴了文件（文件应该被复制到该文件夹）")
    print()


if __name__ == "__main__":
    main()
