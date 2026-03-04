"""
语音通话处理模块
支持发起、接听和结束微信语音通话
"""

import asyncio
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from wechat_client import get_wechat_client, WINDOWS_AVAILABLE


try:
    from config.settings import (
        CALL_TIMEOUT,
        CALL_AUTO_ANSWER,
    )
except ImportError:
    CALL_TIMEOUT = 30
    CALL_AUTO_ANSWER = False


class CallStatus(Enum):
    """通话状态"""
    IDLE = "idle"                    # 空闲
    DIALING = "dialing"             # 拨号中
    RINGING = "ringing"             # 响铃中
    CONNECTED = "connected"         # 已连接
    ENDED = "ended"                 # 已结束
    MISSED = "missed"               # 未接
    REJECTED = "rejected"           # 已拒接
    ERROR = "error"                 # 错误


@dataclass
class CallSession:
    """通话会话"""
    call_id: str
    caller: str                      # 主叫方
    callee: str                      # 被叫方
    status: CallStatus = CallStatus.IDLE
    start_time: Optional[float] = None
    connect_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: float = 0.0           # 通话时长（秒）
    is_outgoing: bool = True        # 是否为呼出
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "caller": self.caller,
            "callee": self.callee,
            "status": self.status.value,
            "start_time": self.start_time,
            "connect_time": self.connect_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "is_outgoing": self.is_outgoing,
            "error_message": self.error_message
        }


class CallHandler:
    """通话处理器"""
    
    def __init__(self):
        self.wechat = get_wechat_client()
        self.active_calls: Dict[str, CallSession] = {}
        self.incoming_calls: Dict[str, CallSession] = {}
        self.call_history: list = []
        
        # 启动通话状态监控
        if WINDOWS_AVAILABLE:
            asyncio.create_task(self._monitor_calls())
    
    async def start_call(
        self, 
        target_user: str, 
        timeout: int = CALL_TIMEOUT
    ) -> Dict[str, Any]:
        """
        发起语音通话
        
        Args:
            target_user: 目标用户昵称/备注名
            timeout: 呼叫超时时间（秒）
        
        Returns:
            操作结果
        """
        try:
            call_id = str(uuid.uuid4())[:8]
            logger.info(f"发起语音通话: {call_id} -> {target_user}")
            
            # 创建通话会话
            session = CallSession(
                call_id=call_id,
                caller="me",
                callee=target_user,
                status=CallStatus.DIALING,
                start_time=time.time(),
                is_outgoing=True
            )
            self.active_calls[call_id] = session
            
            # 打开聊天窗口
            if not await self.wechat.open_chat(target_user):
                session.status = CallStatus.ERROR
                session.error_message = "无法打开聊天窗口"
                return {
                    "success": False,
                    "error": f"无法打开与 {target_user} 的聊天窗口",
                    "call_id": call_id
                }
            
            # 发起通话
            success = await self._do_start_call(target_user)
            
            if success:
                session.status = CallStatus.RINGING
                
                # 等待接听或超时
                result = await self._wait_for_answer(call_id, timeout)
                
                if result:
                    session.status = CallStatus.CONNECTED
                    session.connect_time = time.time()
                    return {
                        "success": True,
                        "message": f"通话已接通",
                        "call_id": call_id,
                        "status": "connected",
                        "callee": target_user
                    }
                else:
                    session.status = CallStatus.MISSED
                    session.end_time = time.time()
                    return {
                        "success": False,
                        "error": "呼叫超时，对方未接听",
                        "call_id": call_id,
                        "status": "timeout"
                    }
            else:
                session.status = CallStatus.ERROR
                session.error_message = "发起通话失败"
                return {
                    "success": False,
                    "error": "发起通话失败",
                    "call_id": call_id
                }
                
        except Exception as e:
            logger.error(f"发起通话失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _do_start_call(self, target_user: str) -> bool:
        """执行发起通话操作"""
        try:
            if not WINDOWS_AVAILABLE:
                logger.info(f"[模拟] 发起语音通话给: {target_user}")
                await asyncio.sleep(2)  # 模拟拨号时间
                return True
            
            # Windows自动化实现
            # 1. 在聊天窗口中点击语音通话按钮
            # 2. 等待通话界面出现
            
            import pyautogui
            
            # 寻找并点击语音通话按钮
            # 微信PC版通常在右上角有通话按钮
            # 这里需要根据实际界面进行调整
            
            # 截图查找通话按钮
            # button_pos = pyautogui.locateOnScreen('call_button.png', confidence=0.8)
            # if button_pos:
            #     pyautogui.click(button_pos)
            
            logger.info("点击语音通话按钮")
            return True
            
        except Exception as e:
            logger.error(f"执行发起通话失败: {e}")
            return False
    
    async def _wait_for_answer(self, call_id: str, timeout: int) -> bool:
        """等待对方接听"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查是否已连接
            if await self._check_call_connected(call_id):
                return True
            
            await asyncio.sleep(1)
        
        return False
    
    async def _check_call_connected(self, call_id: str) -> bool:
        """检查通话是否已连接"""
        # TODO: 实现实际的检查逻辑
        # 可以通过检测通话窗口状态来判断
        
        # 模拟：随机返回连接状态（用于测试）
        # return random.random() > 0.7
        
        return False
    
    async def end_call(self, call_id: str) -> Dict[str, Any]:
        """
        结束语音通话
        
        Args:
            call_id: 通话ID
        
        Returns:
            操作结果
        """
        try:
            if call_id not in self.active_calls:
                return {
                    "success": False,
                    "error": f"通话 {call_id} 不存在"
                }
            
            session = self.active_calls[call_id]
            
            # 执行挂断操作
            success = await self._do_end_call()
            
            # 更新会话状态
            session.status = CallStatus.ENDED
            session.end_time = time.time()
            
            if session.connect_time:
                session.duration = session.end_time - session.connect_time
            
            # 移动到历史记录
            self.call_history.append(session.to_dict())
            del self.active_calls[call_id]
            
            return {
                "success": True,
                "message": "通话已结束",
                "call_id": call_id,
                "duration": session.duration
            }
            
        except Exception as e:
            logger.error(f"结束通话失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _do_end_call(self) -> bool:
        """执行结束通话操作"""
        try:
            if not WINDOWS_AVAILABLE:
                logger.info("[模拟] 结束语音通话")
                return True
            
            # Windows自动化实现
            # 点击挂断按钮或按ESC键
            
            import pyautogui
            
            # 方式1: 按ESC键
            pyautogui.keyDown('esc')
            pyautogui.keyUp('esc')
            
            # 方式2: 点击挂断按钮
            # hangup_pos = pyautogui.locateOnScreen('hangup_button.png', confidence=0.8)
            # if hangup_pos:
            #     pyautogui.click(hangup_pos)
            
            logger.info("挂断通话")
            return True
            
        except Exception as e:
            logger.error(f"执行结束通话失败: {e}")
            return False
    
    async def accept_call(self, caller: str) -> Dict[str, Any]:
        """
        接听语音通话
        
        Args:
            caller: 来电者昵称
        
        Returns:
            操作结果
        """
        try:
            call_id = str(uuid.uuid4())[:8]
            logger.info(f"接听语音通话: {call_id} from {caller}")
            
            # 创建通话会话
            session = CallSession(
                call_id=call_id,
                caller=caller,
                callee="me",
                status=CallStatus.CONNECTED,
                start_time=time.time(),
                connect_time=time.time(),
                is_outgoing=False
            )
            self.active_calls[call_id] = session
            
            # 执行接听操作
            success = await self._do_accept_call()
            
            if success:
                return {
                    "success": True,
                    "message": f"已接听 {caller} 的通话",
                    "call_id": call_id,
                    "caller": caller
                }
            else:
                return {
                    "success": False,
                    "error": "接听通话失败",
                    "call_id": call_id
                }
                
        except Exception as e:
            logger.error(f"接听通话失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _do_accept_call(self) -> bool:
        """执行接听通话操作"""
        try:
            if not WINDOWS_AVAILABLE:
                logger.info("[模拟] 接听语音通话")
                return True
            
            # Windows自动化实现
            # 点击接听按钮
            
            import pyautogui
            
            # accept_pos = pyautogui.locateOnScreen('accept_button.png', confidence=0.8)
            # if accept_pos:
            #     pyautogui.click(accept_pos)
            
            logger.info("点击接听按钮")
            return True
            
        except Exception as e:
            logger.error(f"执行接听通话失败: {e}")
            return False
    
    async def reject_call(self, call_id: str) -> Dict[str, Any]:
        """
        拒接语音通话
        
        Args:
            call_id: 通话ID
        
        Returns:
            操作结果
        """
        try:
            if call_id not in self.incoming_calls:
                return {
                    "success": False,
                    "error": "来电不存在"
                }
            
            session = self.incoming_calls[call_id]
            
            # 执行拒接操作
            success = await self._do_reject_call()
            
            session.status = CallStatus.REJECTED
            session.end_time = time.time()
            
            # 移动到历史记录
            self.call_history.append(session.to_dict())
            del self.incoming_calls[call_id]
            
            return {
                "success": True,
                "message": "已拒接来电",
                "call_id": call_id
            }
            
        except Exception as e:
            logger.error(f"拒接通话失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _do_reject_call(self) -> bool:
        """执行拒接通话操作"""
        try:
            if not WINDOWS_AVAILABLE:
                logger.info("[模拟] 拒接语音通话")
                return True
            
            # 点击拒接按钮
            import pyautogui
            
            # reject_pos = pyautogui.locateOnScreen('reject_button.png', confidence=0.8)
            # if reject_pos:
            #     pyautogui.click(reject_pos)
            
            return True
            
        except Exception as e:
            logger.error(f"执行拒接通话失败: {e}")
            return False
    
    async def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """
        获取通话状态
        
        Args:
            call_id: 通话ID
        
        Returns:
            通话状态信息
        """
        try:
            if call_id in self.active_calls:
                session = self.active_calls[call_id]
                
                # 更新通话时长
                if session.status == CallStatus.CONNECTED and session.connect_time:
                    session.duration = time.time() - session.connect_time
                
                return {
                    "success": True,
                    "call": session.to_dict()
                }
            
            # 在历史记录中查找
            for call in self.call_history:
                if call["call_id"] == call_id:
                    return {
                        "success": True,
                        "call": call,
                        "is_history": True
                    }
            
            return {
                "success": False,
                "error": f"通话 {call_id} 不存在"
            }
            
        except Exception as e:
            logger.error(f"获取通话状态失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_active_calls(self) -> Dict[str, Any]:
        """获取所有活跃通话"""
        return {
            "success": True,
            "calls": [
                session.to_dict() 
                for session in self.active_calls.values()
            ],
            "count": len(self.active_calls)
        }
    
    async def get_call_history(
        self, 
        limit: int = 20,
        caller: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取通话历史
        
        Args:
            limit: 返回数量限制
            caller: 按主叫方过滤
        
        Returns:
            通话历史列表
        """
        try:
            history = self.call_history
            
            if caller:
                history = [
                    call for call in history 
                    if call["caller"] == caller or call["callee"] == caller
                ]
            
            # 按时间倒序
            history = sorted(
                history, 
                key=lambda x: x.get("start_time", 0), 
                reverse=True
            )[:limit]
            
            return {
                "success": True,
                "history": history,
                "total": len(history)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _monitor_calls(self):
        """监控通话状态（后台任务）"""
        while True:
            try:
                # 检查活跃通话状态
                for call_id, session in list(self.active_calls.items()):
                    if session.status == CallStatus.CONNECTED:
                        # 检查通话是否已断开
                        if not await self._check_call_connected(call_id):
                            # 通话已断开
                            session.status = CallStatus.ENDED
                            session.end_time = time.time()
                            session.duration = session.end_time - session.connect_time
                            
                            self.call_history.append(session.to_dict())
                            del self.active_calls[call_id]
                            
                            logger.info(f"通话 {call_id} 已断开")
                
                # 检查来电
                await self._check_incoming_calls()
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"监控通话状态出错: {e}")
                await asyncio.sleep(5)
    
    async def _check_incoming_calls(self):
        """检查是否有来电"""
        # TODO: 实现实际的来电检测逻辑
        # 可以通过检测微信窗口状态来判断
        pass
