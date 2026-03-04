# 配置文件
# 复制此文件为 settings.py 并填入你的配置

import os
from pathlib import Path

# 基础配置
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# MCP服务器配置
MCP_SERVER_NAME = "wechat-mcp-enhanced"
MCP_SERVER_VERSION = "1.0.0"
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")  # stdio 或 sse

# 微信配置
WECHAT_INSTALL_PATH = os.getenv("WECHAT_PATH", r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe")
WECHAT_WINDOW_TITLE = "微信"

# 文件传输配置
FILE_DOWNLOAD_PATH = Path(os.getenv("FILE_DOWNLOAD_PATH", "./downloads"))
FILE_UPLOAD_MAX_SIZE = 100 * 1024 * 1024  # 100MB
FILE_ALLOWED_EXTENSIONS = [
    ".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
    ".mp3", ".wav", ".ogg", ".m4a", ".silk",
    ".mp4", ".avi", ".mov", ".mkv",
    ".zip", ".rar", ".7z", ".tar", ".gz"
]

# 语音配置
VOICE_UPLOAD_PATH = Path(os.getenv("VOICE_UPLOAD_PATH", "./voices/upload"))
VOICE_DOWNLOAD_PATH = Path(os.getenv("VOICE_DOWNLOAD_PATH", "./voices/download"))
VOICE_DEFAULT_FORMAT = "mp3"  # mp3, wav, silk
VOICE_MAX_DURATION = 60  # 秒

# 音频转换配置
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
SILK_ENCODER_PATH = os.getenv("SILK_ENCODER_PATH", "./tools/silk_v3_encoder")
SILK_DECODER_PATH = os.getenv("SILK_DECODER_PATH", "./tools/silk_v3_decoder")

# 通话配置
CALL_TIMEOUT = 30  # 呼叫超时时间（秒）
CALL_AUTO_ANSWER = os.getenv("CALL_AUTO_ANSWER", "false").lower() == "true"

# 自动化配置
AUTOIT_RETRY_COUNT = 3
AUTOIT_RETRY_DELAY = 1.0  # 秒
SCREENSHOT_PATH = Path("./screenshots")

# 确保目录存在
FILE_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
VOICE_UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
VOICE_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
SCREENSHOT_PATH.mkdir(parents=True, exist_ok=True)
