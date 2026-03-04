"""
WeChat MCP Enhanced Server
微信MCP增强版服务器 - 支持文件发送、语音收发、语音通话
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.types import (
    TextContent,
    Tool,
    ImageContent,
    EmbeddedResource,
)
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from handlers.file_handler import FileHandler
from handlers.voice_handler import VoiceHandler
from handlers.call_handler import CallHandler
from wechat_client import WeChatClient

try:
    from config.settings import (
        MCP_SERVER_NAME,
        MCP_SERVER_VERSION,
        LOG_LEVEL,
    )
except ImportError:
    # 使用默认配置
    MCP_SERVER_NAME = "wechat-mcp-enhanced"
    MCP_SERVER_VERSION = "1.0.0"
    LOG_LEVEL = "INFO"

# 配置日志
logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)
logger.add("logs/wechat_mcp.log", rotation="10 MB", level="DEBUG")

# 创建MCP服务器
app = Server(MCP_SERVER_NAME)

# 初始化处理器
file_handler = FileHandler()
voice_handler = VoiceHandler()
call_handler = CallHandler()
wechat_client = WeChatClient()


@app.list_tools()
async def list_tools() -> List[Tool]:
    """列出所有可用的工具"""
    return [
        # 文件相关工具
        Tool(
            name="send_file",
            description="发送文件给微信用户或群聊",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_user": {
                        "type": "string",
                        "description": "目标用户昵称或备注名"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "要发送的文件路径"
                    },
                    "message": {
                        "type": "string",
                        "description": " accompanying message (optional)",
                        "default": ""
                    }
                },
                "required": ["target_user", "file_path"]
            }
        ),
        Tool(
            name="receive_file",
            description="接收文件消息并保存",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "消息ID"
                    },
                    "save_path": {
                        "type": "string",
                        "description": "保存路径"
                    }
                },
                "required": ["message_id", "save_path"]
            }
        ),
        
        # 语音相关工具
        Tool(
            name="send_voice",
            description="发送语音消息给微信用户",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_user": {
                        "type": "string",
                        "description": "目标用户昵称或备注名"
                    },
                    "audio_path": {
                        "type": "string",
                        "description": "音频文件路径（支持mp3/wav/silk格式）"
                    }
                },
                "required": ["target_user", "audio_path"]
            }
        ),
        Tool(
            name="receive_voice",
            description="接收语音消息",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "消息ID"
                    },
                    "save_path": {
                        "type": "string",
                        "description": "保存路径（可选，默认转换为mp3）"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["mp3", "wav", "silk"],
                        "description": "输出格式",
                        "default": "mp3"
                    }
                },
                "required": ["message_id"]
            }
        ),
        Tool(
            name="convert_audio",
            description="转换音频格式（支持mp3/wav/silk互转）",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "输入音频文件路径"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "输出文件路径"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["mp3", "wav", "silk"],
                        "description": "目标格式"
                    }
                },
                "required": ["input_path", "output_path", "output_format"]
            }
        ),
        
        # 通话相关工具
        Tool(
            name="start_voice_call",
            description="发起语音通话",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_user": {
                        "type": "string",
                        "description": "目标用户昵称或备注名"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "呼叫超时时间（秒）",
                        "default": 30
                    }
                },
                "required": ["target_user"]
            }
        ),
        Tool(
            name="end_voice_call",
            description="结束语音通话",
            inputSchema={
                "type": "object",
                "properties": {
                    "call_id": {
                        "type": "string",
                        "description": "通话ID"
                    }
                },
                "required": ["call_id"]
            }
        ),
        Tool(
            name="get_call_status",
            description="获取通话状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "call_id": {
                        "type": "string",
                        "description": "通话ID"
                    }
                },
                "required": ["call_id"]
            }
        ),
        Tool(
            name="accept_voice_call",
            description="接听语音通话",
            inputSchema={
                "type": "object",
                "properties": {
                    "caller": {
                        "type": "string",
                        "description": "来电者昵称"
                    }
                },
                "required": ["caller"]
            }
        ),
        
        # 微信连接工具
        Tool(
            name="check_wechat_status",
            description="检查微信连接状态",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_contact_list",
            description="获取联系人列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制",
                        "default": 100
                    }
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    logger.info(f"调用工具: {name}, 参数: {arguments}")
    
    try:
        # 文件相关
        if name == "send_file":
            result = await file_handler.send_file(
                arguments["target_user"],
                arguments["file_path"],
                arguments.get("message", "")
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        elif name == "receive_file":
            result = await file_handler.receive_file(
                arguments["message_id"],
                arguments["save_path"]
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        # 语音相关
        elif name == "send_voice":
            result = await voice_handler.send_voice(
                arguments["target_user"],
                arguments["audio_path"]
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        elif name == "receive_voice":
            result = await voice_handler.receive_voice(
                arguments["message_id"],
                arguments.get("save_path"),
                arguments.get("output_format", "mp3")
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        elif name == "convert_audio":
            result = await voice_handler.convert_audio(
                arguments["input_path"],
                arguments["output_path"],
                arguments["output_format"]
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        # 通话相关
        elif name == "start_voice_call":
            result = await call_handler.start_call(
                arguments["target_user"],
                arguments.get("timeout", 30)
            )
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        elif name == "end_voice_call":
            result = await call_handler.end_call(arguments["call_id"])
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        elif name == "get_call_status":
            result = await call_handler.get_call_status(arguments["call_id"])
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        elif name == "accept_voice_call":
            result = await call_handler.accept_call(arguments["caller"])
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        # 微信状态
        elif name == "check_wechat_status":
            result = await wechat_client.check_status()
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            
        elif name == "get_contact_list":
            result = await wechat_client.get_contacts(arguments.get("limit", 100))
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
        
        else:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": f"未知工具: {name}"
            }, ensure_ascii=False))]
            
    except Exception as e:
        logger.error(f"工具调用失败: {name}, 错误: {str(e)}")
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False))]


async def main():
    """主函数"""
    logger.info(f"启动 {MCP_SERVER_NAME} v{MCP_SERVER_VERSION}")
    
    # 初始化微信客户端
    await wechat_client.initialize()
    
    # 启动服务器
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
