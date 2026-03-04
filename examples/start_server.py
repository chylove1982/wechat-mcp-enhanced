#!/usr/bin/env python3
"""
MCP Server 启动示例
"""

import subprocess
import sys
from pathlib import Path


def start_server():
    """启动MCP服务器"""
    server_path = Path(__file__).parent.parent / "src" / "server.py"
    
    print("启动 WeChat MCP Server...")
    print(f"服务器路径: {server_path}")
    print()
    
    try:
        subprocess.run([sys.executable, str(server_path)], check=True)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")


if __name__ == "__main__":
    start_server()
