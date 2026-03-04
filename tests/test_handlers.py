"""
测试用例
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from handlers.file_handler import FileHandler
from handlers.voice_handler import VoiceHandler
from handlers.call_handler import CallHandler, CallStatus


# ============== File Handler Tests ==============

class TestFileHandler:
    """文件处理器测试"""
    
    @pytest.fixture
    def file_handler(self):
        return FileHandler()
    
    def test_validate_file_not_exist(self, file_handler):
        """测试验证不存在的文件"""
        is_valid, error = file_handler._validate_file("/nonexistent/file.txt")
        assert is_valid is False
        assert "不存在" in error
    
    def test_validate_file_invalid_extension(self, file_handler, tmp_path):
        """测试验证无效扩展名"""
        invalid_file = tmp_path / "test.xyz"
        invalid_file.write_text("test")
        
        is_valid, error = file_handler._validate_file(str(invalid_file))
        assert is_valid is False
        assert "不支持的文件类型" in error
    
    def test_validate_file_valid(self, file_handler, tmp_path):
        """测试验证有效文件"""
        valid_file = tmp_path / "test.txt"
        valid_file.write_text("test content")
        
        is_valid, error = file_handler._validate_file(str(valid_file))
        assert is_valid is True
        assert error == ""
    
    def test_get_mime_type(self, file_handler):
        """测试MIME类型获取"""
        assert file_handler._get_mime_type(".txt") == "text/plain"
        assert file_handler._get_mime_type(".pdf") == "application/pdf"
        assert file_handler._get_mime_type(".jpg") == "image/jpeg"
        assert file_handler._get_mime_type(".xyz") == "application/octet-stream"
    
    def test_format_size(self, file_handler):
        """测试文件大小格式化"""
        assert "B" in file_handler._format_size(100)
        assert "KB" in file_handler._format_size(1024)
        assert "MB" in file_handler._format_size(1024 * 1024)


# ============== Voice Handler Tests ==============

class TestVoiceHandler:
    """语音处理器测试"""
    
    @pytest.fixture
    def voice_handler(self):
        return VoiceHandler()
    
    def test_validate_audio_not_exist(self, voice_handler):
        """测试验证不存在的音频"""
        is_valid, error = voice_handler._validate_audio("/nonexistent/audio.mp3")
        assert is_valid is False
        assert "不存在" in error
    
    def test_validate_audio_invalid_format(self, voice_handler, tmp_path):
        """测试验证无效格式"""
        invalid_file = tmp_path / "test.xyz"
        invalid_file.write_text("test")
        
        is_valid, error = voice_handler._validate_audio(str(invalid_file))
        assert is_valid is False
        assert "不支持的音频格式" in error
    
    @pytest.mark.asyncio
    async def test_send_voice_invalid_file(self, voice_handler):
        """测试发送无效语音文件"""
        result = await voice_handler.send_voice("test_user", "/nonexistent.mp3")
        assert result["success"] is False
        assert "不存在" in result["error"]


# ============== Call Handler Tests ==============

class TestCallHandler:
    """通话处理器测试"""
    
    @pytest.fixture
    def call_handler(self):
        return CallHandler()
    
    def test_call_session_creation(self, call_handler):
        """测试通话会话创建"""
        session = CallSession(
            call_id="test123",
            caller="user1",
            callee="user2",
            status=CallStatus.DIALING
        )
        
        assert session.call_id == "test123"
        assert session.status == CallStatus.DIALING
        assert session.is_outgoing is True
    
    def test_call_session_to_dict(self, call_handler):
        """测试通话会话序列化"""
        session = CallSession(
            call_id="test123",
            caller="user1",
            callee="user2",
            status=CallStatus.CONNECTED
        )
        
        data = session.to_dict()
        assert data["call_id"] == "test123"
        assert data["status"] == "connected"
    
    @pytest.mark.asyncio
    async def test_get_call_status_not_exist(self, call_handler):
        """测试获取不存在的通话状态"""
        result = await call_handler.get_call_status("nonexistent")
        assert result["success"] is False
        assert "不存在" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_active_calls_empty(self, call_handler):
        """测试获取空活跃通话列表"""
        result = await call_handler.get_active_calls()
        assert result["success"] is True
        assert result["count"] == 0
        assert result["calls"] == []


# ============== Integration Tests ==============

@pytest.mark.asyncio
async def test_file_voice_call_workflow():
    """测试完整工作流"""
    # 这里可以测试完整的用户场景
    pass


# ============== Helper Tests ==============

class TestHelpers:
    """工具函数测试"""
    
    def test_sanitize_filename(self):
        """测试文件名清理"""
        from utils.helpers import sanitize_filename
        
        assert sanitize_filename("test<file>.txt") == "test_file_.txt"
        assert sanitize_filename("test:file.txt") == "test_file.txt"
        assert sanitize_filename("test/file.txt") == "test_file.txt"
    
    def test_generate_timestamp(self):
        """测试时间戳生成"""
        from utils.helpers import generate_timestamp
        
        ts = generate_timestamp()
        assert len(ts) == 15  # YYYYMMDD_HHMMSS
        assert "_" in ts
    
    def test_format_duration(self):
        """测试时长格式化"""
        from utils.helpers import format_duration
        
        assert "秒" in format_duration(30)
        assert "分" in format_duration(120)
        assert "小时" in format_duration(3700)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
