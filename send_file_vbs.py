# -*- coding: utf-8 -*-
"""
发送文件给微信联系人 - 使用 Shell 复制方式
"""
import subprocess
import os

def send_file_shell(contact, file_path):
    """使用 Shell.Application 复制文件"""
    
    # 确保文件存在
    if not os.path.exists(file_path.replace('\\', '/')):
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    # 使用 VBScript 方式复制文件到剪贴板
    ps_script = f'''
# 创建 VBScript 来复制文件
$vbsScript = @"
Set objShell = CreateObject("Shell.Application")
Set objFolder = objShell.Namespace("{os.path.dirname(file_path)}")
Set objFile = objFolder.ParseName("{os.path.basename(file_path)}")
objFile.InvokeVerb("Copy")
"@

$vbsPath = "$env:TEMP\\copy_file.vbs"
$vbsScript | Out-File -FilePath $vbsPath -Encoding ASCII

# 执行 VBScript
cscript //nologo $vbsPath
Start-Sleep -Milliseconds 1000

# 删除临时文件
Remove-Item $vbsPath -ErrorAction SilentlyContinue

Add-Type -AssemblyName System.Windows.Forms

# 查找微信窗口
$wechat = Get-Process | Where-Object {{ 
    ($_.ProcessName -like "*WeChat*" -or $_.MainWindowTitle -like "*微信*") -and $_.MainWindowHandle -ne 0 
}} | Select-Object -First 1

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
    
    # 粘贴
    [System.Windows.Forms.SendKeys]::SendWait("^v")
    Start-Sleep -Milliseconds 800
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
    
    return "[OK]" in result.stdout

if __name__ == "__main__":
    contact = "肖"
    file_path = "E:\\devtools\\setenv.bat"
    
    print(f"[INFO] Sending file to {contact}...")
    send_file_shell(contact, file_path)
