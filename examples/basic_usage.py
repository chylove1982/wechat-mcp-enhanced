#!/usr/bin/env python3
"""
WeChat MCP 使用示例
演示如何使用各种功能
"""

import asyncio
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from handlers.file_handler import FileHandler
from handlers.voice_handler import VoiceHandler
from handlers.call_handler import CallHandler


async def example_send_file():
    """示例：发送文件"""
    print("=" * 50)
    print("示例1: 发送文件")
    print("=" * 50)
    
    handler = FileHandler()
    
    # 发送文件给好友
    result = await handler.send_file(
        target_user="文件传输助手",
        file_path="/path/to/your/file.txt",
        message="这是一份文档"
    )
    
    print(f"结果: {result}")
    print()


async def example_send_voice():
    """示例：发送语音"""
    print("=" * 50)
    print("示例2: 发送语音消息")
    print("=" * 50)
    
    handler = VoiceHandler()
    
    # 发送语音给好友
    result = await handler.send_voice(
        target_user="文件传输助手",
        audio_path="/path/to/your/audio.mp3"
    )
    
    print(f"结果: {result}")
    print()


async def example_convert_audio():
    """示例：转换音频格式"""
    print("=" * 50)
    print("示例3: 转换音频格式")
    print("=" * 50)
    
    handler = VoiceHandler()
    
    # MP3转SILK（微信语音格式）
    result = await handler.convert_audio(
        input_path="/path/to/input.mp3",
        output_path="/path/to/output.silk",
        output_format="silk"
    )
    
    print(f"结果: {result}")
    print()


async def example_voice_call():
    """示例：语音通话"""
    print("=" * 50)
    print("示例4: 发起语音通话")
    print("=" * 50)
    
    handler = CallHandler()
    
    # 发起通话
    result = await handler.start_call(
        target_user="好友名称",
        timeout=30
    )
    
    print(f"通话发起结果: {result}")
    
    if result["success"]:
        call_id = result["call_id"]
        print(f"通话ID: {call_id}")
        
        # 等待一段时间后结束
        print("通话中... (5秒)")
        await asyncio.sleep(5)
        
        # 结束通话
        end_result = await handler.end_call(call_id)
        print(f"结束通话结果: {end_result}")
    
    print()


async def example_check_status():
    """示例：检查状态"""
    print("=" * 50)
    print("示例5: 检查微信状态")
    print("=" * 50)
    
    from wechat_client import get_wechat_client
    
    client = get_wechat_client()
    result = await client.check_status()
    
    print(f"微信状态: {result}")
    print()


async def example_batch_send():
    """示例：批量发送"""
    print("=" * 50)
    print("示例6: 批量发送文件")
    print("=" * 50)
    
    handler = FileHandler()
    
    files = [
        "/path/to/file1.txt",
        "/path/to/file2.pdf",
        "/path/to/file3.jpg"
    ]
    
    target = "文件传输助手"
    
    for file_path in files:
        print(f"发送: {file_path}")
        result = await handler.send_file(target, file_path)
        print(f"结果: {result['success']}")
        await asyncio.sleep(1)  # 避免发送太快
    
    print()


async def main():
    """主函数"""
    print("WeChat MCP 使用示例")
    print("=" * 50)
    print()
    
    # 运行所有示例（取消注释需要的示例）
    
    # await example_check_status()
    # await example_send_file()
    # await example_send_voice()
    # await example_convert_audio()
    # await example_voice_call()
    # await example_batch_send()
    
    print("示例运行完成!")
    print()
    print("提示:")
    print("1. 确保已配置 config/settings.py")
    print("2. 确保微信PC版已登录")
    print("3. 修改示例中的文件路径和用户名")


if __name__ == "__main__":
    asyncio.run(main())
