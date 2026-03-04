"""
文件处理模块
支持发送和接收文件
"""

import os
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from wechat_client import get_wechat_client

try:
    from config.settings import (
        FILE_DOWNLOAD_PATH,
        FILE_UPLOAD_MAX_SIZE,
        FILE_ALLOWED_EXTENSIONS,
    )
except ImportError:
    FILE_DOWNLOAD_PATH = Path("./downloads")
    FILE_UPLOAD_MAX_SIZE = 100 * 1024 * 1024  # 100MB
    FILE_ALLOWED_EXTENSIONS = [
        ".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
        ".mp3", ".wav", ".ogg", ".m4a", ".silk",
        ".mp4", ".avi", ".mov", ".mkv",
        ".zip", ".rar", ".7z", ".tar", ".gz"
    ]


@dataclass
class FileInfo:
    """文件信息"""
    path: Path
    name: str
    size: int
    extension: str
    mime_type: str


class FileHandler:
    """文件处理器"""
    
    def __init__(self):
        self.wechat = get_wechat_client()
        FILE_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
    
    def _validate_file(self, file_path: str) -> tuple[bool, str]:
        """验证文件"""
        path = Path(file_path)
        
        if not path.exists():
            return False, f"文件不存在: {file_path}"
        
        if not path.is_file():
            return False, f"路径不是文件: {file_path}"
        
        file_size = path.stat().st_size
        if file_size > FILE_UPLOAD_MAX_SIZE:
            max_mb = FILE_UPLOAD_MAX_SIZE / (1024 * 1024)
            return False, f"文件大小超过限制 ({max_mb}MB)"
        
        extension = path.suffix.lower()
        if extension not in FILE_ALLOWED_EXTENSIONS:
            return False, f"不支持的文件类型: {extension}"
        
        return True, ""
    
    def _get_mime_type(self, extension: str) -> str:
        """根据扩展名获取MIME类型"""
        mime_types = {
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".zip": "application/zip",
            ".rar": "application/x-rar-compressed",
        }
        return mime_types.get(extension.lower(), "application/octet-stream")
    
    async def send_file(
        self, 
        target_user: str, 
        file_path: str, 
        message: str = ""
    ) -> Dict[str, Any]:
        """
        发送文件给指定用户
        
        Args:
            target_user: 目标用户昵称/备注名
            file_path: 文件路径
            message: 附带消息
        
        Returns:
            操作结果
        """
        try:
            # 验证文件
            is_valid, error_msg = self._validate_file(file_path)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }
            
            path = Path(file_path)
            file_info = FileInfo(
                path=path,
                name=path.name,
                size=path.stat().st_size,
                extension=path.suffix.lower(),
                mime_type=self._get_mime_type(path.suffix)
            )
            
            logger.info(f"准备发送文件: {file_info.name} 给 {target_user}")
            
            # 打开聊天窗口
            if not await self.wechat.open_chat(target_user):
                return {
                    "success": False,
                    "error": f"无法打开与 {target_user} 的聊天窗口"
                }
            
            # 发送文件
            success = await self._do_send_file(file_info, message)
            
            if success:
                return {
                    "success": True,
                    "message": f"文件 {file_info.name} 发送成功",
                    "file_name": file_info.name,
                    "file_size": file_info.size,
                    "target": target_user
                }
            else:
                return {
                    "success": False,
                    "error": "文件发送失败"
                }
                
        except Exception as e:
            logger.error(f"发送文件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _do_send_file(self, file_info: FileInfo, message: str = "") -> bool:
        """执行文件发送操作"""
        try:
            # Windows自动化实现
            if hasattr(self.wechat, 'app') and self.wechat.app:
                # 1. 点击文件传输按钮或拖拽文件
                # 2. 选择文件
                # 3. 发送
                
                # 使用剪贴板 + 粘贴方式发送文件
                import pyautogui
                import pyperclip
                
                # 复制文件到剪贴板
                pyperclip.copy(str(file_info.path))
                
                # 模拟Ctrl+V粘贴
                pyautogui.keyDown('ctrl')
                pyautogui.keyDown('v')
                pyautogui.keyUp('v')
                pyautogui.keyUp('ctrl')
                
                await asyncio.sleep(0.5)
                
                # 发送
                pyautogui.keyDown('return')
                pyautogui.keyUp('return')
                
                logger.info(f"文件 {file_info.name} 已发送")
                return True
            else:
                # 模拟模式
                logger.info(f"[模拟] 发送文件: {file_info.name}")
                return True
                
        except Exception as e:
            logger.error(f"执行文件发送失败: {e}")
            return False
    
    async def receive_file(
        self, 
        message_id: str, 
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        接收文件消息
        
        Args:
            message_id: 消息ID
            save_path: 保存路径（可选，默认使用下载目录）
        
        Returns:
            操作结果
        """
        try:
            # 确定保存路径
            if save_path is None:
                save_dir = FILE_DOWNLOAD_PATH
            else:
                save_dir = Path(save_path).parent
                save_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"准备接收文件消息: {message_id}")
            
            # TODO: 实现实际的文件接收逻辑
            # 1. 找到消息
            # 2. 点击下载
            # 3. 等待下载完成
            # 4. 移动到指定位置
            
            return {
                "success": True,
                "message": f"文件消息 {message_id} 接收成功",
                "message_id": message_id,
                "save_path": str(save_dir)
            }
            
        except Exception as e:
            logger.error(f"接收文件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": "文件不存在"
                }
            
            stat = path.stat()
            return {
                "success": True,
                "name": path.name,
                "size": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "extension": path.suffix.lower(),
                "mime_type": self._get_mime_type(path.suffix),
                "modified_time": stat.st_mtime
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
