# -*- coding: utf-8 -*-
import sys
import os

# 设置环境变量来传递参数（避免命令行编码问题）
os.environ['WECHAT_CONTACT'] = '肖'
os.environ['WECHAT_VOICE'] = 'C:\\mcp\\winautowx\\temp\\test_voice.mp3'

# 导入并调用 server 中的函数
sys.path.insert(0, r'C:\mcp\winautowx')

# 直接执行发送逻辑
import subprocess
result = subprocess.run(
    ['python', '-c', '''
import sys
sys.path.insert(0, r"C:\\mcp\\winautowx")
exec(open(r"C:\\mcp\\winautowx\\server.py", "r", encoding="utf-8").read())
import asyncio

async def main():
    result = await handle_tool("wechat_send_voice", {
        "contact": "肖",
        "audio_path": "C:\\\\mcp\\\\winautowx\\\\temp\\\\test_voice.mp3"
    })
    print(result["content"][0]["text"])

asyncio.run(main())
    '''],
    capture_output=True,
    text=True,
    encoding='utf-8'
)

print(result.stdout)
if result.stderr:
    print("[STDERR]", result.stderr)
