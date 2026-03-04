# -*- coding: utf-8 -*-
"""
发送文件给微信联系人 - 使用拖拽方式
"""
import subprocess
import os

def send_file_drag(contact, file_path):
    """拖拽文件到微信聊天窗口"""
    
    if not os.path.exists(file_path.replace('\\', '/')):
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    file_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    
    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms

# 打开资源管理器并选中文件
Write-Host "[INFO] Opening Explorer with file..."
$shell = New-Object -ComObject "Shell.Application"
$shell.ShellExecute("explorer.exe", "/select,`"{file_path}`"", "", "open", 1)
Start-Sleep -Milliseconds 2000

# 获取资源管理器窗口
$explorer = Get-Process | Where-Object {{ 
    $_.ProcessName -eq "explorer" -and $_.MainWindowTitle -ne "" 
}} | Select-Object -First 1

Add-Type @"
    using System;
    using System.Runtime.InteropServices;
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
        public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, int dwExtraInfo);
        
        public struct RECT {{
            public int Left; public int Top; public int Right; public int Bottom;
        }}
        
        public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
        public const uint MOUSEEVENTF_LEFTUP = 0x0004;
    }}
"@

# 获取资源管理器窗口位置
if ($explorer) {{
    $rect = New-Object Win32+RECT
    [Win32]::GetWindowRect($explorer.MainWindowHandle, [ref]$rect)
    $fileX = $rect.Left + 100  # 文件位置（假设）
    $fileY = $rect.Top + 150
}}

# 查找微信
$wechat = Get-Process | Where-Object {{ 
    ($_.MainWindowTitle -like "*微信*") -and $_.MainWindowHandle -ne 0
}} | Select-Object -First 1

if (-not $wechat) {{
    Write-Host "[ERROR] WeChat not found"
    exit 1
}}

# 激活微信并搜索联系人
Write-Host "[INFO] Switching to WeChat..."
[Win32]::ShowWindow($wechat.MainWindowHandle, 9)
Start-Sleep -Milliseconds 500
[Win32]::SetForegroundWindow($wechat.MainWindowHandle)
Start-Sleep -Milliseconds 1000

Write-Host "[INFO] Searching contact..."
[System.Windows.Forms.SendKeys]::SendWait("^f")
Start-Sleep -Milliseconds 600
[System.Windows.Forms.SendKeys]::SendWait("{contact}")
Start-Sleep -Milliseconds 1500
[System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
Start-Sleep -Milliseconds 1500

# 获取微信窗口位置（拖拽目标）
$wRect = New-Object Win32+RECT
[Win32]::GetWindowRect($wechat.MainWindowHandle, [ref]$wRect)
$dropX = $wRect.Left + [int](($wRect.Right - $wRect.Left) / 2)
$dropY = $wRect.Top + [int](($wRect.Bottom - $wRect.Top) / 2)

# 切换到资源管理器，拖拽文件到微信
Write-Host "[INFO] Dragging file to chat window..."
[Win32]::SetForegroundWindow($explorer.MainWindowHandle)
Start-Sleep -Milliseconds 500

# 移动鼠标到文件位置
[Win32]::SetCursorPos($fileX, $fileY)
Start-Sleep -Milliseconds 300

# 按下鼠标左键
[Win32]::mouse_event(0x0002, 0, 0, 0, 0)
Start-Sleep -Milliseconds 300

# 移动鼠标到微信窗口（拖拽）
$steps = 10
$xStep = ($dropX - $fileX) / $steps
$yStep = ($dropY - $fileY) / $steps

for ($i = 1; $i -le $steps; $i++) {{
    $newX = $fileX + [int]($xStep * $i)
    $newY = $fileY + [int]($yStep * $i)
    [Win32]::SetCursorPos($newX, $newY)
    Start-Sleep -Milliseconds 50
}}

# 释放鼠标左键
[Win32]::mouse_event(0x0004, 0, 0, 0, 0)
Start-Sleep -Milliseconds 1000

# 发送（如果弹出了确认对话框）
[System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
Start-Sleep -Milliseconds 500

Write-Host "[OK] File drag completed"

# 关闭资源管理器
$explorer | Stop-Process -ErrorAction SilentlyContinue
'''
    
    result = subprocess.run(
        ["powershell.exe", "-Command", ps_script],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    print(result.stdout)
    if result.stderr:
        print(f"[WARN] {result.stderr}")
    
    return "[OK]" in result.stdout

if __name__ == "__main__":
    contact = "肖"
    file_path = "E:\\devtools\\setenv.bat"
    
    print(f"[INFO] Sending '{os.path.basename(file_path)}' to {contact} (drag mode)...")
    print("[WARNING] This will move your mouse cursor!")
    send_file_drag(contact, file_path)
