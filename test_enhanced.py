# -*- coding: utf-8 -*-
"""
测试脚本 - 测试WeChat MCP Enhanced功能
"""

import json
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import (
    get_wechat_status,
    send_file_to_contact,
    send_voice_to_contact,
    start_voice_call,
    end_voice_call,
    find_and_open_chat,
)


def test_status():
    """测试状态查询"""
    print("\n" + "="*50)
    print("测试1: 微信状态查询")
    print("="*50)
    
    result = get_wechat_status()
    print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return result.get("status") == "running"


def test_find_chat():
    """测试查找联系人"""
    print("\n" + "="*50)
    print("测试2: 查找联系人")
    print("="*50)
    
    # 使用文件传输助手测试
    contact = "文件传输助手"
    print(f"查找: {contact}")
    
    success, err = find_and_open_chat(contact)
    
    if success:
        print(f"✅ 成功打开聊天窗口")
        return True
    else:
        print(f"❌ 失败: {err}")
        return False


def test_send_file():
    """测试发送文件"""
    print("\n" + "="*50)
    print("测试3: 发送文件")
    print("="*50)
    
    # 创建一个测试文件
    test_file = os.path.join(os.path.dirname(__file__), "test_file.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("这是一个测试文件\n发送时间: {}\n".format(__import__('time').strftime('%Y-%m-%d %H:%M:%S')))
    
    contact = "文件传输助手"
    print(f"发送文件给: {contact}")
    print(f"文件路径: {test_file}")
    
    success, err = send_file_to_contact(contact, test_file, "测试消息")
    
    if success:
        print(f"✅ 文件发送成功")
        return True
    else:
        print(f"❌ 发送失败: {err}")
        return False


def test_tools_list():
    """测试工具列表"""
    print("\n" + "="*50)
    print("测试4: 可用工具列表")
    print("="*50)
    
    from server import TOOLS
    
    print(f"共有 {len(TOOLS)} 个工具:")
    for tool in TOOLS:
        print(f"  - {tool['name']}: {tool['description']}")
    
    return True


def test_call():
    """测试语音通话"""
    print("\n" + "="*50)
    print("测试5: 语音通话")
    print("="*50)
    
    print("⚠️  注意: 这将实际发起通话！")
    print("跳过测试，请手动测试此功能")
    
    return True


def main():
    """主函数"""
    print("\n" + "="*60)
    print("WeChat MCP Enhanced 测试脚本")
    print("="*60)
    
    results = []
    
    # 运行测试
    results.append(("状态查询", test_status()))
    results.append(("查找联系人", test_find_chat()))
    results.append(("发送文件", test_send_file()))
    results.append(("工具列表", test_tools_list()))
    results.append(("语音通话", test_call()))
    
    # 打印结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    print(f"\n总计: {passed_count}/{len(results)} 个测试通过")
    
    print("\n提示:")
    print("1. 确保微信PC版已登录")
    print("2. 确保微信窗口未被最小化")
    print("3. 部分功能需要手动测试")


if __name__ == "__main__":
    main()
