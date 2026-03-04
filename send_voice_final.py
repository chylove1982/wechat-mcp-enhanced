# -*- coding: utf-8 -*-
"""
微信语音发送工具 - 拖拽方式发送文件
"""
import subprocess
import sys
import os
import time


def send_voice_drag_drop(contact, voice_file):
    """
    使用拖拽方式发送语音文件
    步骤：
    1. 打开文件资源管理器并定位到文件
    2. 激活微信窗口并打开联系人
    3. 使用 AutoHotkey 或类似工具执行拖拽
    """
    
    # 确保使用 Windows 路径格式
    voice_file_win = voice_file.replace('/', '\\')
    file_dir = os.path.dirname(voice_file_win)
    file_name = os.path.basename(voice_file_win)
    
    # PowerShell 脚本执行拖拽操作
    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms

# 步骤1: 打开文件资源管理器并选中文件
$explorer = New-Object -ComObject Shell.Application
$explorer.ShellExecute("explorer.exe", "/select,`"{voice_file_win}`"", "", "open", 1)
Start-Sleep -Milliseconds 1500

# 获取文件资源管理器窗口
$explorerWindow = Get-Process | Where-Object {{ $_.ProcessName -eq "explorer" }} | 
    Where-Object {{ $_.MainWindowTitle -ne "" }} | Select-Object -First 1

if (-not $explorerWindow) {{
    Write-Host "[ERROR] Explorer window not found"
    exit 1
}}

# 步骤2: 激活微信窗口并搜索联系人
$wechatProcesses = Get-Process | Where-Object {{ 
    $_.ProcessName -like "*WeChat*" -or $_.ProcessName -like "*微信*" 
}}

$wechat = $wechatProcesses | Where-Object {{ $_.MainWindowHandle -ne 0 }} | Select-Object -First 1

if ($wechat) {{
    # 激活微信窗口
    Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class Win32 {{
            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);
            [DllImport("user32.dll")]
            public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        }}
"@
    
    [Win32]::ShowWindow($wechat.MainWindowHandle, 9)
    [Win32]::SetForegroundWindow($wechat.MainWindowHandle)
    Start-Sleep -Milliseconds 800
    
    # 搜索联系人
    [System.Windows.Forms.SendKeys]::SendWait("^f")
    Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait("{contact}")
    Start-Sleep -Milliseconds 1000
    [System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
    Start-Sleep -Milliseconds 1000
}}

# 步骤3: 使用更简单的方法 - 直接粘贴文件
# 通过 Shell.Application 复制文件到剪贴板
$shell = New-Object -ComObject "Shell.Application"
$folder = $shell.Namespace("{file_dir}")
$file = $folder.ParseName("{file_name}")

if ($file) {{
    # 复制文件
    $file.InvokeVerb("Copy")
    Start-Sleep -Milliseconds 800
    
    # 激活微信并粘贴
    if ($wechat) {{
        [Win32]::SetForegroundWindow($wechat.MainWindowHandle)
        Start-Sleep -Milliseconds 500
    }}
    
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 800
    [System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
    
    Write-Host "[OK] Voice sent successfully"
}} else {{
    Write-Host "[ERROR] Could not access file"
}}

# 关闭资源管理器窗口 (可选)
Start-Sleep -Milliseconds 500
if ($explorerWindow) {{
    $explorerWindow | Stop-Process -ErrorAction SilentlyContinue
}}
'''
    
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"[WARN] {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("[ERROR] Timeout")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


if __name__ == "__main__":
    contact = "肖"
    voice_file = "C:\\mcp\\winautowx\\temp\\test_voice.mp3"
    
    if not os.path.exists(voice_file):
        print(f"[ERROR] File not found: {voice_file}")
        sys.exit(1)
    
    print(f"[INFO] Sending voice to {contact}...")
    success = send_voice_drag_drop(contact, voice_file)
    sys.exit(0 if success else 1)
