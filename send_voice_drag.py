# -*- coding: utf-8 -*-
"""
微信语音发送工具 - 拖拽方式（使用 PowerShell 辅助）
"""
import subprocess
import sys
import os

def send_voice_with_explorer(contact, voice_file):
    """使用 Windows 资源管理器拖拽方式发送语音"""
    
    # PowerShell 脚本：打开资源管理器，复制文件，粘贴到微信
    ps_script = f'''
# 激活微信窗口
$wechat = Get-Process | Where-Object {{ $_.ProcessName -like "*WeChat*" -or $_.ProcessName -like "*微信*" }} | Select-Object -First 1
if ($wechat) {{
    $hwnd = $wechat.MainWindowHandle
    if ($hwnd -ne 0) {{
        # 使用 User32.dll 激活窗口
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
        [Win32]::ShowWindow($hwnd, 9)  # SW_RESTORE
        [Win32]::SetForegroundWindow($hwnd)
        Start-Sleep -Milliseconds 500
    }}
}}

# 搜索联系人
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("^f")
Start-Sleep -Milliseconds 500
[System.Windows.Forms.SendKeys]::SendWait("{contact}")
Start-Sleep -Milliseconds 1000
[System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
Start-Sleep -Milliseconds 1000

# 打开文件对话框 (Alt+O 在某些版本有效，或者使用 Ctrl+V 粘贴文件)
# 方法：使用 Shell.Application 复制文件到剪贴板
$shell = New-Object -ComObject "Shell.Application"
$item = $shell.Namespace((Get-Item "{voice_file}").DirectoryName).ParseName((Get-Item "{voice_file}").Name)
$item.InvokeVerb("Copy")
Start-Sleep -Milliseconds 500

# 粘贴到微信
[System.Windows.Forms.SendKeys]::SendWait("^v")
Start-Sleep -Milliseconds 500
[System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")

Write-Host "Voice sent successfully"
'''
    
    # 执行 PowerShell 脚本
    result = subprocess.run(
        ["powershell.exe", "-Command", ps_script],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("[OK] Voice sent successfully")
        return True
    else:
        print(f"[ERROR] {result.stderr}")
        return False

if __name__ == "__main__":
    contact = "肖"
    voice_file = "C:\\mcp\\winautowx\\temp\\test_voice.mp3"
    
    if not os.path.exists(voice_file):
        print(f"[ERROR] File not found: {voice_file}")
        sys.exit(1)
    
    success = send_voice_with_explorer(contact, voice_file)
    sys.exit(0 if success else 1)
