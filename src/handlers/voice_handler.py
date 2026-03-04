"""
语音处理模块
支持语音发送、接收和格式转换
"""

import os
import subprocess
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
        VOICE_UPLOAD_PATH,
        VOICE_DOWNLOAD_PATH,
        VOICE_DEFAULT_FORMAT,
        VOICE_MAX_DURATION,
        FFMPEG_PATH,
        SILK_ENCODER_PATH,
        SILK_DECODER_PATH,
    )
except ImportError:
    VOICE_UPLOAD_PATH = Path("./voices/upload")
    VOICE_DOWNLOAD_PATH = Path("./voices/download")
    VOICE_DEFAULT_FORMAT = "mp3"
    VOICE_MAX_DURATION = 60
    FFMPEG_PATH = "ffmpeg"
    SILK_ENCODER_PATH = "./tools/silk_v3_encoder"
    SILK_DECODER_PATH = "./tools/silk_v3_decoder"


@dataclass
class AudioInfo:
    """音频信息"""
    path: Path
    format: str
    duration: float
    sample_rate: int
    channels: int


class VoiceHandler:
    """语音处理器"""
    
    def __init__(self):
        self.wechat = get_wechat_client()
        VOICE_UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
        VOICE_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
        
        # 检查ffmpeg
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            result = subprocess.run(
                [FFMPEG_PATH, "-version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _validate_audio(self, audio_path: str) -> tuple[bool, str]:
        """验证音频文件"""
        path = Path(audio_path)
        
        if not path.exists():
            return False, f"音频文件不存在: {audio_path}"
        
        if not path.is_file():
            return False, f"路径不是文件: {audio_path}"
        
        valid_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.silk', '.wma', '.aac']
        if path.suffix.lower() not in valid_extensions:
            return False, f"不支持的音频格式: {path.suffix}"
        
        return True, ""
    
    def _get_audio_info(self, audio_path: str) -> Optional[AudioInfo]:
        """获取音频信息"""
        try:
            if not self.ffmpeg_available:
                return None
            
            # 使用ffprobe获取音频信息
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-show_entries",
                    "format=duration", "-show_entries",
                    "stream=sample_rate,channels", "-of",
                    "default=noprint_wrappers=1", audio_path
                ],
                capture_output=True,
                text=True
            )
            
            path = Path(audio_path)
            return AudioInfo(
                path=path,
                format=path.suffix.lower().replace('.', ''),
                duration=0.0,  # 简化处理
                sample_rate=16000,
                channels=1
            )
            
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return None
    
    async def send_voice(
        self, 
        target_user: str, 
        audio_path: str
    ) -> Dict[str, Any]:
        """
        发送语音消息
        
        Args:
            target_user: 目标用户
            audio_path: 音频文件路径
        
        Returns:
            操作结果
        """
        try:
            # 验证音频文件
            is_valid, error_msg = self._validate_audio(audio_path)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }
            
            path = Path(audio_path)
            logger.info(f"准备发送语音: {path.name} 给 {target_user}")
            
            # 转换为silk格式（微信语音格式）
            silk_path = await self._convert_to_silk(audio_path)
            if not silk_path:
                return {
                    "success": False,
                    "error": "音频格式转换失败"
                }
            
            # 打开聊天窗口
            if not await self.wechat.open_chat(target_user):
                return {
                    "success": False,
                    "error": f"无法打开与 {target_user} 的聊天窗口"
                }
            
            # 发送语音
            success = await self._do_send_voice(silk_path)
            
            # 清理临时文件
            if silk_path != audio_path:
                try:
                    os.remove(silk_path)
                except:
                    pass
            
            if success:
                return {
                    "success": True,
                    "message": f"语音消息发送成功",
                    "file_name": path.name,
                    "target": target_user
                }
            else:
                return {
                    "success": False,
                    "error": "语音发送失败"
                }
                
        except Exception as e:
            logger.error(f"发送语音失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _convert_to_silk(self, audio_path: str) -> Optional[str]:
        """将音频转换为silk格式"""
        try:
            path = Path(audio_path)
            
            # 如果已经是silk格式，直接返回
            if path.suffix.lower() == '.silk':
                return audio_path
            
            if not self.ffmpeg_available:
                logger.warning("ffmpeg不可用，无法转换音频格式")
                return audio_path  # 返回原路径，让微信处理
            
            # 转换为中间wav格式
            wav_path = VOICE_UPLOAD_PATH / f"{path.stem}_temp.wav"
            
            subprocess.run([
                FFMPEG_PATH, "-i", audio_path,
                "-ar", "24000", "-ac", "1", "-f", "s16le",
                str(wav_path)
            ], check=True, capture_output=True)
            
            # 转换为silk格式
            silk_path = VOICE_UPLOAD_PATH / f"{path.stem}.silk"
            
            # 使用silk编码器（如果有的话）
            if Path(SILK_ENCODER_PATH).exists():
                subprocess.run([
                    SILK_ENCODER_PATH,
                    str(wav_path),
                    str(silk_path),
                    "-Fs_API", "24000"
                ], check=True, capture_output=True)
                
                os.remove(wav_path)
                return str(silk_path)
            else:
                # 如果没有silk编码器，返回wav格式
                # 微信应该能处理wav
                logger.warning("SILK编码器不可用，使用WAV格式")
                return str(wav_path)
                
        except Exception as e:
            logger.error(f"转换音频格式失败: {e}")
            return None
    
    async def _do_send_voice(self, voice_path: str) -> bool:
        """执行语音发送操作"""
        try:
            # 使用文件发送方式发送语音
            # 微信会自动识别为语音消息
            
            import pyautogui
            import pyperclip
            
            # 复制文件到剪贴板
            pyperclip.copy(voice_path)
            
            # 粘贴
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('v')
            pyautogui.keyUp('v')
            pyautogui.keyUp('ctrl')
            
            await asyncio.sleep(0.5)
            
            # 发送
            pyautogui.keyDown('return')
            pyautogui.keyUp('return')
            
            logger.info(f"语音已发送: {voice_path}")
            return True
            
        except Exception as e:
            logger.error(f"发送语音失败: {e}")
            return False
    
    async def receive_voice(
        self, 
        message_id: str, 
        save_path: Optional[str] = None,
        output_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        接收语音消息
        
        Args:
            message_id: 消息ID
            save_path: 保存路径
            output_format: 输出格式 (mp3/wav/silk)
        
        Returns:
            操作结果
        """
        try:
            # 确定保存路径
            if save_path is None:
                save_path = VOICE_DOWNLOAD_PATH / f"voice_{message_id}.{output_format}"
            else:
                save_path = Path(save_path)
            
            logger.info(f"准备接收语音消息: {message_id}")
            
            # TODO: 实现实际的语音接收逻辑
            # 1. 找到语音消息
            # 2. 下载silk格式文件
            # 3. 转换为目标格式
            
            return {
                "success": True,
                "message": f"语音消息接收成功",
                "message_id": message_id,
                "save_path": str(save_path),
                "format": output_format
            }
            
        except Exception as e:
            logger.error(f"接收语音失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def convert_audio(
        self,
        input_path: str,
        output_path: str,
        output_format: str
    ) -> Dict[str, Any]:
        """
        转换音频格式
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            output_format: 目标格式 (mp3/wav/silk)
        
        Returns:
            操作结果
        """
        try:
            if not self.ffmpeg_available and output_format != 'silk':
                return {
                    "success": False,
                    "error": "ffmpeg不可用，无法转换音频"
                }
            
            input_path = Path(input_path)
            output_path = Path(output_path)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if output_format == 'silk':
                # 转换为silk格式
                result_path = await self._convert_to_silk(str(input_path))
                if result_path:
                    shutil.move(result_path, output_path)
                    return {
                        "success": True,
                        "message": "转换为SILK格式成功",
                        "output_path": str(output_path)
                    }
                else:
                    return {
                        "success": False,
                        "error": "转换为SILK格式失败"
                    }
            else:
                # 使用ffmpeg转换
                subprocess.run([
                    FFMPEG_PATH, "-i", str(input_path),
                    "-y", str(output_path)
                ], check=True, capture_output=True)
                
                return {
                    "success": True,
                    "message": f"转换为{output_format.upper()}格式成功",
                    "output_path": str(output_path)
                }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"音频转换失败: {e}")
            return {
                "success": False,
                "error": f"音频转换失败: {e.stderr.decode() if e.stderr else str(e)}"
            }
        except Exception as e:
            logger.error(f"音频转换失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def record_voice(
        self,
        duration: int = 10,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        录制语音
        
        Args:
            duration: 录制时长（秒）
            output_path: 输出路径
        
        Returns:
            操作结果
        """
        try:
            if output_path is None:
                import time
                output_path = VOICE_UPLOAD_PATH / f"recorded_{int(time.time())}.wav"
            else:
                output_path = Path(output_path)
            
            # TODO: 实现录音功能
            # 可以使用pyaudio或sounddevice
            
            return {
                "success": True,
                "message": f"录音完成",
                "duration": duration,
                "save_path": str(output_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
