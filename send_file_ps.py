# -*- coding: utf-8 -*-
"""
发送文件给微信联系人 - 使用文件复制粘贴方式
"""
import subprocess
import sys

def send_file(contact, file_path):
    """发送文件给微信联系人"""
    
    # PowerShell 脚本：复制文件到剪贴板，然后粘贴到微信
    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms

# 复制文件到剪贴板
$files = New-Object System.Collections.Specialized.StringCollection
$files.Add("{file_path}")
[System.Windows.Forms.Clipboard]::SetFileDropList($files)

# 等待剪贴板就绪
Start-Sleep -Milliseconds 500

# 激活微信窗口并搜索联系人
# 尝试多种方式查找微信
$wechat = Get-Process | Where-Object {{ 
    ($_.ProcessName -like "*WeChat*" -or $_.ProcessName -like "*微信*") -and $_.MainWindowHandle -ne 0 
}} | Select-Object -First 1

# 如果没找到，尝试通过窗口标题查找
if (-not $wechat) {{
    $allProcesses = Get-Process | Where-Object {{ $_.MainWindowHandle -ne 0 }}
    foreach ($proc in $allProcesses) {{
        if ($proc.MainWindowTitle -and ($proc.MainWindowTitle -like "*微信*" -or $proc.MainWindowTitle -like "*WeChat*")) {{
            $wechat = $proc
            break
        }}
    }}
}}

if ($wechat) {{
    # 激活窗口
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
    
    # 粘贴文件
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 800
    
    # 发送
    [System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
    
    Write-Host "[OK] File sent"
}} else {{
    Write-Host "[ERROR] WeChat not found"
}}
'''
    
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

if __name__ == "__main__":
    contact = "肖"
    file_path = "E:\\devtools\\setenv.bat"
    
    print(f"[INFO] Sending file to {contact}...")
    send_file(contact, file_path)
