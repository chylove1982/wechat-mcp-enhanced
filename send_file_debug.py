# -*- coding: utf-8 -*-
"""
发送文件给微信联系人 - 修复剪贴板问题
"""
import subprocess
import os
import time

def send_file_debug(contact, file_path):
    """调试版文件发送"""
    
    if not os.path.exists(file_path.replace('\\', '/')):
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    file_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    
    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms

# 方法1: 使用 Shell 复制文件
Write-Host "[DEBUG] Step 1: Copying file to clipboard..."
$shell = New-Object -ComObject "Shell.Application"
$folder = $shell.Namespace("{file_dir}")
$file = $folder.ParseName("{file_name}")

if ($file) {{
    Write-Host "[DEBUG] File found: {file_name}"
    $file.InvokeVerb("Copy")
    Write-Host "[DEBUG] Copy command executed"
    Start-Sleep -Milliseconds 1500
}} else {{
    Write-Host "[ERROR] Could not find file in folder"
    exit 1
}}

# 验证剪贴板内容
Write-Host "[DEBUG] Step 2: Checking clipboard..."
$clipboardFiles = [System.Windows.Forms.Clipboard]::GetFileDropList()
Write-Host "[DEBUG] Clipboard has $($clipboardFiles.Count) file(s)"
if ($clipboardFiles.Count -gt 0) {{
    Write-Host "[DEBUG] First file: $($clipboardFiles[0])"
}}

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

# 查找微信
Write-Host "[DEBUG] Step 3: Finding WeChat..."
$wechat = Get-Process | Where-Object {{ 
    ($_.MainWindowTitle -like "*微信*" -or $_.MainWindowTitle -like "*WeChat*") -and
    $_.MainWindowHandle -ne 0
}} | Select-Object -First 1

if (-not $wechat) {{
    Write-Host "[ERROR] WeChat not found"
    exit 1
}}

Write-Host "[DEBUG] Found WeChat: $($wechat.MainWindowTitle)"

# 激活窗口
Write-Host "[DEBUG] Step 4: Activating window..."
[Win32]::ShowWindow($wechat.MainWindowHandle, 9)
Start-Sleep -Milliseconds 500
[Win32]::SetForegroundWindow($wechat.MainWindowHandle)
Start-Sleep -Milliseconds 1000

# 搜索联系人
Write-Host "[DEBUG] Step 5: Searching contact '{contact}'..."
[System.Windows.Forms.SendKeys]::SendWait("^f")
Start-Sleep -Milliseconds 600
[System.Windows.Forms.SendKeys]::SendWait("{contact}")
Start-Sleep -Milliseconds 1500
[System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
Start-Sleep -Milliseconds 1500

# 粘贴
Write-Host "[DEBUG] Step 6: Pasting..."
[System.Windows.Forms.SendKeys]::SendWait("^v")
Start-Sleep -Milliseconds 1500

# 检查是否有文件预览（通过等待一小段时间观察）
Write-Host "[DEBUG] Step 7: Sending..."
[System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
Start-Sleep -Milliseconds 500

Write-Host "[OK] Done"
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
    
    print(f"[INFO] Sending '{os.path.basename(file_path)}' to {contact} (debug mode)...")
    send_file_debug(contact, file_path)
