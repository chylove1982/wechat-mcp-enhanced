# -*- coding: utf-8 -*-
"""
WeChat MCP Server v5.0 - 稳定版
"""

import sys
import os
import json
import asyncio
import time
import subprocess

# 设置路径，确保能找到依赖
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    import pygetwindow as gw
    import pyperclip
    import win32gui
    import win32con
except ImportError as e:
    print(f"[错误] 缺少依赖: {e}", file=sys.stderr)
    print("[提示] 请运行: pip install pyautogui pygetwindow pyperclip pywin32", file=sys.stderr)
    sys.exit(1)


def safe_print(text):
    """安全打印"""
    try:
        print(text, flush=True)
    except:
        pass


# ==================== 窗口操作 ====================

def get_wechat_window():
    """获取微信窗口"""
    try:
        wins = gw.getWindowsWithTitle("微信")
        for w in wins:
            if w.width > 500 and w.height > 500:
                return w
    except:
        pass
    return None


def get_chat_window():
    """获取聊天窗口"""
    try:
        # 尝试找Dragon窗口（聊天窗口）
        windows = gw.getWindowsWithTitle("Dragon")
        for win in windows:
            if "Dragon" in win.title:
                return win
    except:
        pass
    # 回退到主窗口
    return get_wechat_window()


def set_clipboard_text(text):
    """设置剪贴板文本"""
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        safe_print(f"[警告] 剪贴板设置失败: {e}")
        return False


# ==================== 核心功能 ====================

def find_and_open_chat(contact_name):
    """搜索并打开联系人聊天窗口"""
    safe_print(f"[1/6] 搜索联系人: {contact_name}")
    
    win = get_wechat_window()
    if not win:
        return False, "微信未运行"
    
    try:
        # 激活微信
        win.activate()
        time.sleep(0.5)
        
        # 打开搜索
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        
        # 清空并输入联系人
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('delete')
        time.sleep(0.1)
        
        # 复制联系人名到剪贴板并粘贴
        if not set_clipboard_text(contact_name):
            return False, "剪贴板操作失败"
        
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.0)
        
        # 回车打开聊天
        pyautogui.press('enter')
        time.sleep(1.5)
        
        # 验证聊天窗口是否打开
        if not get_chat_window():
            return False, "未能打开聊天窗口"
        
        safe_print(f"[2/6] 已打开聊天: {contact_name}")
        return True, None
        
    except Exception as e:
        return False, f"搜索失败: {str(e)}"


def send_file_to_contact(contact_name, file_path, message=""):
    """
    发送文件给联系人 - 使用复制粘贴方式（最稳定）
    
    步骤：
    1. 打开聊天窗口
    2. 打开资源管理器选中文件
    3. 复制文件
    4. 粘贴到微信
    5. 发送
    """
    safe_print(f"[开始] 发送文件: {os.path.basename(file_path)} -> {contact_name}")
    
    # 检查文件
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    abs_path = os.path.abspath(file_path)
    file_name = os.path.basename(abs_path)
    folder_path = os.path.dirname(abs_path)
    
    # 打开聊天
    success, err = find_and_open_chat(contact_name)
    if not success:
        return False, err
    
    wechat_win = get_chat_window()
    if not wechat_win:
        return False, "未找到聊天窗口"
    
    try:
        # 获取屏幕尺寸
        screen_width, screen_height = pyautogui.size()
        safe_print(f"[3/6] 屏幕分辨率: {screen_width}x{screen_height}")
        
        # 调整微信窗口（右侧）
        wechat_handle = win32gui.FindWindow(None, wechat_win.title)
        if wechat_handle:
            # 如果是最大化，先恢复
            placement = win32gui.GetWindowPlacement(wechat_handle)
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                win32gui.ShowWindow(wechat_handle, win32con.SW_RESTORE)
                time.sleep(0.3)
            
            # 设置窗口位置和大小
            wx = int(screen_width * 0.42)
            wy = 50
            ww = int(screen_width * 0.56)
            wh = screen_height - 100
            
            win32gui.SetWindowPos(
                wechat_handle, win32con.HWND_TOP,
                wx, wy, ww, wh,
                win32con.SWP_SHOWWINDOW
            )
            time.sleep(0.5)
            
            # 更新窗口信息
            wechat_win = get_chat_window()
            safe_print(f"[信息] 微信窗口: ({wechat_win.left}, {wechat_win.top}) {wechat_win.width}x{wechat_win.height}")
        
        # 打开资源管理器选中文件
        safe_print(f"[4/6] 打开资源管理器...")
        explorer_cmd = f'explorer /select,"{abs_path}"'
        subprocess.Popen(explorer_cmd, shell=True)
        time.sleep(2.5)
        
        # 查找资源管理器窗口
        explorer_win = None
        for _ in range(5):  # 重试5次
            for w in gw.getAllWindows():
                if w.title and w.width > 400:
                    # 检查是否包含文件夹名或文件名
                    folder_name = os.path.basename(folder_path)
                    if folder_name in w.title or file_name in w.title:
                        explorer_win = w
                        break
            if explorer_win:
                break
            time.sleep(0.5)
        
        if not explorer_win:
            safe_print("[警告] 未找到资源管理器窗口，尝试备选方案")
            # 备选：找最近打开的非微信窗口
            for w in reversed(gw.getAllWindows()):
                if w.isActive and w.width > 400 and "微信" not in w.title:
                    explorer_win = w
                    break
        
        if not explorer_win:
            return False, "无法找到资源管理器窗口"
        
        safe_print(f"[信息] 资源管理器: {explorer_win.title}")
        
        # 调整资源管理器窗口（左侧）
        explorer_handle = win32gui.FindWindow("CabinetWClass", None)
        if explorer_handle:
            win32gui.SetWindowPos(
                explorer_handle, win32con.HWND_TOP,
                0, 50,
                int(screen_width * 0.38), screen_height - 100,
                win32con.SWP_SHOWWINDOW
            )
            time.sleep(0.3)
        
        # 在资源管理器中复制文件（文件已被 /select 选中，直接Ctrl+C）
        safe_print(f"[5/6] 复制文件...")
        
        # 激活资源管理器窗口
        explorer_win.activate()
        time.sleep(0.5)
        
        # 直接复制（文件已经被 explorer /select 选中了，不需要再点击）
        safe_print("[信息] 按 Ctrl+C 复制选中文件...")
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('c')
        pyautogui.keyUp('c')
        pyautogui.keyUp('ctrl')
        time.sleep(1.0)  # 等待复制完成
        
        safe_print("[信息] 文件已复制到剪贴板")
        
        # 关闭资源管理器
        try:
            explorer_win.close()
            time.sleep(0.5)
        except:
            pass
        
        # 粘贴到微信
        safe_print(f"[6/6] 粘贴到微信...")
        
        wechat_win.activate()
        time.sleep(0.5)
        
        # 点击输入框区域
        input_x = wechat_win.left + wechat_win.width // 2
        input_y = wechat_win.top + wechat_win.height - 140
        pyautogui.click(input_x, input_y)
        time.sleep(0.3)
        
        # 粘贴
        pyautogui.keyDown('ctrl')
        pyautogui.keyDown('v')
        pyautogui.keyUp('v')
        pyautogui.keyUp('ctrl')
        
        # 关键：等待文件图标出现（3秒）
        safe_print("[信息] 等待文件加载...")
        time.sleep(3.0)
        
        # 如果有附带消息，添加到文件下方
        if message:
            safe_print("[信息] 添加附带消息...")
            
            # 点击输入框底部
            msg_x = wechat_win.left + wechat_win.width // 2
            msg_y = wechat_win.top + wechat_win.height - 60
            pyautogui.click(msg_x, msg_y)
            time.sleep(0.3)
            
            if set_clipboard_text(message):
                time.sleep(0.2)
                pyautogui.keyDown('ctrl')
                pyautogui.keyDown('v')
                pyautogui.keyUp('v')
                pyautogui.keyUp('ctrl')
                time.sleep(0.5)
        
        # 发送（按两次Enter确保）
        safe_print("[信息] 发送文件...")
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('enter')  # 第二次发送
        time.sleep(1.0)
        
        safe_print(f"[成功] 文件已发送: {file_name}")
        return True, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"发送失败: {str(e)}"


def send_message_to_contact(contact_name, message):
    """发送文本消息"""
    safe_print(f"[发送消息] -> {contact_name}")
    
    success, err = find_and_open_chat(contact_name)
    if not success:
        return False, err
    
    win = get_chat_window()
    if not win:
        return False, "未找到窗口"
    
    try:
        # 点击输入框
        input_x = win.left + win.width // 2
        input_y = win.top + win.height - 60
        pyautogui.click(input_x, input_y)
        time.sleep(0.3)
        
        # 清空并输入
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('delete')
        time.sleep(0.1)
        
        if not set_clipboard_text(message):
            return False, "剪贴板失败"
        
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        
        return True, None
        
    except Exception as e:
        return False, f"发送失败: {str(e)}"


def get_wechat_status():
    """获取微信状态"""
    win = get_wechat_window()
    if not win:
        return {"status": "not_running", "message": "微信未运行"}
    
    chat_win = get_chat_window()
    return {
        "status": "running",
        "has_chat": chat_win is not None,
        "version": "5.0.0"
    }


# ==================== MCP 协议 ====================

# 导入数据库和监听模块
from database import get_database
from message_listener import WeChatMessageListener  # 使用新的监听器
from auto_reply import AutoReplyEngine, PRESET_RULES

# 全局实例
db = get_database()
listener = WeChatMessageListener(db)  # 使用新的监听器类
auto_reply = AutoReplyEngine(db)

TOOLS = [
    {
        "name": "wechat_get_status",
        "description": "获取微信运行状态",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "wechat_send_message",
        "description": "发送文本消息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "消息内容"},
                "contact": {"type": "string", "description": "联系人名称"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "wechat_send_file",
        "description": "发送文件给联系人",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "联系人名称"},
                "file_path": {"type": "string", "description": "文件完整路径"},
                "message": {"type": "string", "description": "附带消息（可选）"}
            },
            "required": ["contact", "file_path"]
        }
    },
    # ===== 新增：聊天记录查询 =====
    {
        "name": "wechat_get_chat_history",
        "description": "获取与某联系人的聊天记录",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "联系人名称"},
                "limit": {"type": "integer", "description": "返回最近N条", "default": 50},
                "offset": {"type": "integer", "description": "分页偏移", "default": 0}
            },
            "required": ["contact"]
        }
    },
    {
        "name": "wechat_get_unread_messages",
        "description": "获取所有未读消息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "可选，指定联系人"},
                "mark_as_read": {"type": "boolean", "description": "是否标记为已读", "default": True}
            }
        }
    },
    {
        "name": "wechat_search_messages",
        "description": "搜索聊天记录",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词"},
                "contact": {"type": "string", "description": "可选，指定联系人"},
                "limit": {"type": "integer", "description": "返回数量", "default": 20}
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "wechat_get_contacts",
        "description": "获取联系人列表（带未读数）",
        "inputSchema": {"type": "object", "properties": {}}
    },
    # ===== 新增：消息监听 =====
    {
        "name": "wechat_start_listener",
        "description": "开始监听新消息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contacts": {"type": "array", "description": "要监听的联系人列表，空数组表示监听当前聊天", "default": []},
                "interval": {"type": "integer", "description": "检查间隔（秒）", "default": 3}
            }
        }
    },
    {
        "name": "wechat_stop_listener",
        "description": "停止监听消息",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "wechat_get_listener_status",
        "description": "获取监听状态",
        "inputSchema": {"type": "object", "properties": {}}
    },
    # ===== 新增：自动回复 =====
    {
        "name": "wechat_set_auto_reply",
        "description": "设置自动回复规则",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "联系人名称"},
                "enabled": {"type": "boolean", "description": "是否启用"},
                "mode": {"type": "string", "description": "模式：keyword/ai", "default": "keyword"},
                "rules": {"type": "array", "description": "关键词规则列表"},
                "preset": {"type": "string", "description": "预设模式：客服模式/简洁模式/工作时间"}
            },
            "required": ["contact", "enabled"]
        }
    },
    {
        "name": "wechat_test_auto_reply",
        "description": "测试自动回复",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact": {"type": "string", "description": "联系人名称"},
                "message": {"type": "string", "description": "测试消息"}
            },
            "required": ["contact", "message"]
        }
    },
    {
        "name": "wechat_get_statistics",
        "description": "获取聊天统计信息",
        "inputSchema": {"type": "object", "properties": {}}
    }
]


async def handle_tool(name, arguments):
    """处理MCP工具调用"""
    safe_print(f"[工具调用] {name}")
    
    # 从参数获取基础值
    contact = arguments.get('contact', '')
    message = arguments.get('message', '')
    file_path = arguments.get('file_path', '')
    
    # 如果参数值为 "from_env" 或空，从环境变量读取（支持中文）
    if contact == 'from_env' or not contact:
        contact = os.environ.get('WECHAT_CONTACT', contact)
        safe_print(f"[ENV] 联系人: {contact}")
    
    if message == 'from_env' or not message:
        message = os.environ.get('WECHAT_MESSAGE', message)
        safe_print(f"[ENV] 消息: {message}")
    
    if file_path == 'from_env' or not file_path:
        file_path = os.environ.get('WECHAT_FILE', file_path)
        safe_print(f"[ENV] 文件: {file_path}")
    
    try:
        if name == "wechat_get_status":
            result = get_wechat_status()
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
        
        elif name == "wechat_send_message":
            if not message:
                return {"content": [{"type": "text", "text": "[ERROR] 需要消息内容"}]}
            
            success, err = send_message_to_contact(contact, message)
            
            if success:
                return {"content": [{"type": "text", "text": "[OK] 消息已发送"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        elif name == "wechat_send_file":
            if not contact:
                return {"content": [{"type": "text", "text": "[ERROR] 需要联系人名称"}]}
            
            if not file_path:
                return {"content": [{"type": "text", "text": "[ERROR] 需要文件路径"}]}
            
            success, err = send_file_to_contact(contact, file_path, message)
            
            if success:
                return {"content": [{"type": "text", "text": f"[OK] 文件已发送: {os.path.basename(file_path)}"}]}
            else:
                return {"content": [{"type": "text", "text": f"[ERROR] {err}"}]}
        
        # ===== 聊天记录查询 =====
        elif name == "wechat_get_chat_history":
            contact = arguments.get('contact', '')
            limit = arguments.get('limit', 50)
            offset = arguments.get('offset', 0)
            
            if not contact:
                return {"content": [{"type": "text", "text": "[ERROR] 需要联系人名称"}]}
            
            history = db.get_chat_history(contact, limit=limit, offset=offset)
            return {"content": [{"type": "text", "text": json.dumps(history, ensure_ascii=False, indent=2)}]}
        
        elif name == "wechat_get_unread_messages":
            contact = arguments.get('contact', None)
            mark_as_read = arguments.get('mark_as_read', True)
            
            unread = db.get_unread_messages(contact, mark_as_read=mark_as_read)
            return {"content": [{"type": "text", "text": json.dumps(unread, ensure_ascii=False, indent=2)}]}
        
        elif name == "wechat_search_messages":
            keyword = arguments.get('keyword', '')
            contact = arguments.get('contact', None)
            limit = arguments.get('limit', 20)
            
            if not keyword:
                return {"content": [{"type": "text", "text": "[ERROR] 需要搜索关键词"}]}
            
            results = db.search_messages(keyword, contact, limit)
            return {"content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False, indent=2)}]}
        
        elif name == "wechat_get_contacts":
            contacts = db.get_contacts()
            return {"content": [{"type": "text", "text": json.dumps(contacts, ensure_ascii=False, indent=2)}]}
        
        # ===== 消息监听 =====
        elif name == "wechat_start_listener":
            contacts = arguments.get('contacts', [])
            interval = arguments.get('interval', 3)
            
            if listener.is_listening:
                return {"content": [{"type": "text", "text": "[警告] 已经在监听中"}]}
            
            def on_message(msg):
                safe_print(f"[监听] 新消息 [{msg.contact}]: {msg.content[:50]}...")
                # 检查自动回复
                reply = auto_reply.handle_incoming_message(msg.contact, msg.sender, msg.content)
                if reply:
                    safe_print(f"[自动回复] {reply}")
                    # 发送自动回复
                    send_message_to_contact(msg.contact, reply)
            
            listener.start_listening(
                contacts=contacts if contacts else None,
                interval=interval,
                on_message=on_message
            )
            
            return {"content": [{"type": "text", "text": f"[OK] 开始监听，间隔: {interval}秒"}]}
        
        elif name == "wechat_stop_listener":
            if not listener.is_listening:
                return {"content": [{"type": "text", "text": "[警告] 当前未在监听"}]}
            
            listener.stop_listening()
            return {"content": [{"type": "text", "text": "[OK] 已停止监听"}]}
        
        elif name == "wechat_get_listener_status":
            status = {
                "is_listening": listener.is_listening,
                "check_interval": listener.check_interval,
                "last_messages_hash": {k: v[:8] + "..." for k, v in listener.last_messages_hash.items()}
            }
            return {"content": [{"type": "text", "text": json.dumps(status, ensure_ascii=False, indent=2)}]}
        
        # ===== 自动回复 =====
        elif name == "wechat_set_auto_reply":
            contact = arguments.get('contact', '')
            enabled = arguments.get('enabled', False)
            mode = arguments.get('mode', 'keyword')
            rules = arguments.get('rules', [])
            preset = arguments.get('preset', '')
            
            if not contact:
                return {"content": [{"type": "text", "text": "[ERROR] 需要联系人名称"}]}
            
            # 如果使用预设
            if preset and preset in PRESET_RULES:
                rules = PRESET_RULES[preset]
            
            auto_reply.set_auto_reply(
                contact=contact,
                enabled=enabled,
                mode=mode,
                rules=rules
            )
            
            return {"content": [{"type": "text", "text": f"[OK] 自动回复设置成功: {contact} ({'开启' if enabled else '关闭'})"}]}
        
        elif name == "wechat_test_auto_reply":
            contact = arguments.get('contact', '')
            test_message = arguments.get('message', '')
            
            if not contact or not test_message:
                return {"content": [{"type": "text", "text": "[ERROR] 需要联系人和测试消息"}]}
            
            result = auto_reply.test_reply(contact, test_message)
            return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}
        
        elif name == "wechat_get_statistics":
            stats = db.get_statistics()
            return {"content": [{"type": "text", "text": json.dumps(stats, ensure_ascii=False, indent=2)}]}
        
        else:
            return {"content": [{"type": "text", "text": f"[ERROR] 未知工具: {name}"}]}
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"content": [{"type": "text", "text": f"[ERROR] {str(e)}"}]}


async def main():
    """MCP主循环"""
    safe_print("="*60)
    safe_print("WeChat MCP Server v5.0")
    safe_print("="*60)
    safe_print("")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            request = json.loads(line)
            method = request.get("method")
            req_id = request.get("id")
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "wechat-mcp-server",
                            "version": "5.0.0"
                        }
                    }
                }
                print(json.dumps(response), flush=True)
                safe_print("[MCP] 已初始化")
            
            elif method == "notifications/initialized":
                pass
            
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS}
                }
                print(json.dumps(response), flush=True)
            
            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                result = await handle_tool(tool_name, tool_args)
                
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
                print(json.dumps(response, ensure_ascii=False), flush=True)
        
        except json.JSONDecodeError as e:
            error = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"JSON解析错误: {e}"}
            }
            print(json.dumps(error), flush=True)
        
        except Exception as e:
            error = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
