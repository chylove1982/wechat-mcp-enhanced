"""
修复NumPy版本冲突
"""
import subprocess
import sys

print("=" * 60)
print("修复 NumPy 版本冲突")
print("=" * 60)
print()
print("当前 NumPy 版本过高，需要降级到 1.x")
print()

# 降级numpy
print("[1/2] 卸载当前 NumPy...")
result = subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "numpy"], 
                       capture_output=True, text=True)
print(result.stdout if result.stdout else "完成")

print("\n[2/2] 安装 NumPy 1.26.4 (兼容版本)...")
result = subprocess.run([sys.executable, "-m", "pip", "install", "numpy==1.26.4"],
                       capture_output=True, text=True)

if result.returncode == 0:
    print("✅ NumPy 安装成功")
else:
    print(f"⚠️ {result.stderr[:200]}")

print("\n测试导入...")
try:
    import numpy as np
    print(f"✅ NumPy 版本: {np.__version__}")
    
    # 测试pyautogui
    import pyautogui
    print("✅ PyAutoGUI 导入成功")
    
    print("\n🎉 修复完成！")
except Exception as e:
    print(f"❌ 仍有问题: {e}")
