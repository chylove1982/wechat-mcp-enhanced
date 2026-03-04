# -*- coding: utf-8 -*-
"""
发送文件给微信联系人 - 使用鼠标点击+粘贴
"""
import subprocess
import os

def send_file_with_click(contact, file_path):
    """发送文件 - 先点击输入框再粘贴"""
    
    if not os.path.exists(file_path.replace('\\', '/')):
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    file_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    
    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms

# 复制文件到剪贴板
Write-Host "[INFO] Copying file..."
$shell = New-Object -ComObject "Shell.Application"
$folder = $shell.Namespace("{file_dir}")
$file = $folder.ParseName("{file_name}")
$file.InvokeVerb("Copy")
Start-Sleep -Milliseconds 1500

Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    using System.Drawing;
    public class Win32 {{
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")]
        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        [DllImport("user32.dll")]
        public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
        [DllImport("user32.dll")]
        public static extern bool SetCursorPos(int X, int Y);
        [DllImport("user32.dll")]
        public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtraInfo);
        
        public struct RECT {{
            public int Left; public int Top; public int Right; public int Bottom;
        }}
        
        public const int MOUSEEVENTF_LEFTDOWN = 0x02;
        public const int MOUSEEVENTF_LEFTUP = 0x04;
    }}
"@

# 查找微信
$wechat = Get-Process | Where-Object {{ 
    ($_.MainWindowTitle -like "*微信*" -or $_.MainWindowTitle -like "*WeChat*") -and
    $_.MainWindowHandle -ne 0
}} | Select-Object -First 1

if (-not $wechat) {{
    Write-Host "[ERROR] WeChat not found"
    exit 1
}}

# 激活窗口
Write-Host "[INFO] Activating WeChat..."
[Win32]::ShowWindow($wechat.MainWindowHandle, 9)
Start-Sleep -Milliseconds 500
[Win32]::SetForegroundWindow($wechat.MainWindowHandle)
Start-Sleep -Milliseconds 1000

# 搜索联系人
Write-Host "[INFO] Searching contact..."
[System.Windows.Forms.SendKeys]::SendWait("^f")
Start-Sleep -Milliseconds 600
[System.Windows.Forms.SendKeys]::SendWait("{contact}")
Start-Sleep -Milliseconds 1500
[System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
Start-Sleep -Milliseconds 1500

# 获取窗口位置并点击输入框（窗口底部中央）
$rect = New-Object Win32+RECT
[Win32]::GetWindowRect($wechat.MainWindowHandle, [ref]$rect)
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
$clickX = $rect.Left + [int]($width / 2)
$clickY = $rect.Top + $height - 80

Write-Host "[INFO] Clicking input area at ($clickX, $clickY)..."
[Win32]::SetCursorPos($clickX, $clickY)
Start-Sleep -Milliseconds 200
[Win32]::mouse_event(0x02, 0, 0, 0, 0)  # Left down
Start-Sleep -Milliseconds 100
[Win32]::mouse_event(0x04, 0, 0, 0, 0)  # Left up
Start-Sleep -Milliseconds 500

# 粘贴
Write-Host "[INFO] Pasting file..."
[System.Windows.Forms.SendKeys]::SendWait("^v")
Start-Sleep -Milliseconds 1500

# 发送
Write-Host "[INFO] Sending..."
[System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
Start-Sleep -Milliseconds 500

Write-Host "[OK] File sent"
'''
    
    result = subprocess.run(
        ["powershell.exe", "-Command", ps_script],
        capture_output=True,
        text=True,
        timeout=90
    )
    
    print(result.stdout)
    if result.stderr:
        print(f"[WARN] {result.stderr}")
    
    return "[OK]" in result.stdout

if __name__ == "__main__":
    contact = "肖"
    file_path = "E:\\devtools\\setenv.bat"
    
    print(f"[INFO] Sending '{os.path.basename(file_path)}' to {contact}...")
    send_file_with_click(contact, file_path)
