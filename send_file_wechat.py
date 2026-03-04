# -*- coding: utf-8 -*-
"""
发送文件给微信联系人 - 精确匹配微信窗口
"""
import subprocess
import os

def send_file_wechat(contact, file_path):
    """使用精确方式发送文件到微信"""
    
    if not os.path.exists(file_path.replace('\\', '/')):
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    ps_script = f'''
# 复制文件到剪贴板 - 使用 VBScript
$vbs = @"
Set objShell = CreateObject("Shell.Application")
Set objFolder = objShell.Namespace("{os.path.dirname(file_path)}")
Set objFile = objFolder.ParseName("{os.path.basename(file_path)}")
objFile.InvokeVerb("Copy")
"@
$vbsPath = "$env:TEMP\\copy_file.vbs"
$vbs | Out-File -FilePath $vbsPath -Encoding ASCII -Force
cscript //nologo $vbsPath
Start-Sleep -Milliseconds 1000
Remove-Item $vbsPath -ErrorAction SilentlyContinue

Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
    using System;
    using System.Runtime.InteropServices;
    public class Win32 {{
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")]
        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        [DllImport("user32.dll")]
        public static extern bool IsWindow(IntPtr hWnd);
    }}
"@

# 精确查找微信窗口 - 通过进程名和窗口类名
$wechat = $null

# 方法1: 通过进程名查找
$processes = Get-Process | Where-Object {{ 
    ($_.ProcessName -eq "WeChat" -or $_.ProcessName -eq "wechat" -or $_.ProcessName -like "*微信*") -and 
    $_.MainWindowHandle -ne 0 -and
    $_.MainWindowTitle -notlike "*PowerShell*" -and
    $_.MainWindowTitle -notlike "*cmd*" -and
    $_.MainWindowTitle -notlike "*Command*"
}}

if ($processes) {{
    $wechat = $processes | Select-Object -First 1
    Write-Host "[INFO] Found WeChat by process name: $($wechat.ProcessName), Title: $($wechat.MainWindowTitle)"
}}

# 方法2: 如果方法1失败，遍历所有窗口查找标题包含"微信"的
if (-not $wechat) {{
    $allProcs = Get-Process | Where-Object {{ 
        $_.MainWindowHandle -ne 0 -and
        ($_.MainWindowTitle -like "*微信*" -or $_.MainWindowTitle -like "*WeChat*") -and
        $_.MainWindowTitle -notlike "*PowerShell*" -and
        $_.MainWindowTitle -notlike "*cmd*"
    }}
    if ($allProcs) {{
        $wechat = $allProcs | Select-Object -First 1
        Write-Host "[INFO] Found WeChat by window title: $($wechat.MainWindowTitle)"
    }}
}}

if ($wechat) {{
    Write-Host "[INFO] Activating WeChat window..."
    
    # 恢复并激活窗口
    [Win32]::ShowWindow($wechat.MainWindowHandle, 9)  # SW_RESTORE
    Start-Sleep -Milliseconds 300
    [Win32]::SetForegroundWindow($wechat.MainWindowHandle)
    Start-Sleep -Milliseconds 1000
    
    # 搜索联系人
    Write-Host "[INFO] Searching contact..."
    [System.Windows.Forms.SendKeys]::SendWait("^f")
    Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait("{contact}")
    Start-Sleep -Milliseconds 1200
    [System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
    Start-Sleep -Milliseconds 1200
    
    # 粘贴文件
    Write-Host "[INFO] Pasting file..."
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 1000
    [System.Windows.Forms.SendKeys]::SendWait("{{ENTER}}")
    Start-Sleep -Milliseconds 500
    
    Write-Host "[OK] File sent to WeChat"
}} else {{
    Write-Host "[ERROR] WeChat window not found. Please ensure WeChat is running."
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
    
    return "[OK]" in result.stdout

if __name__ == "__main__":
    contact = "肖"
    file_path = "E:\\devtools\\setenv.bat"
    
    print(f"[INFO] Sending file '{os.path.basename(file_path)}' to {contact}...")
    send_file_wechat(contact, file_path)
