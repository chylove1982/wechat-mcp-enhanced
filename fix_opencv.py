"""
修复OpenCV冲突
"""
import subprocess
import sys
import os


def fix_opencv():
    """修复OpenCV冲突"""
    print("=" * 60)
    print("修复 OpenCV 冲突")
    print("=" * 60)
    print()
    
    # 步骤1: 完全卸载所有OpenCV包
    print("[1/3] 卸载冲突的OpenCV包...")
    packages = [
        "opencv-python",
        "opencv-contrib-python", 
        "opencv-python-headless",
        "cv2"
    ]
    
    for pkg in packages:
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", pkg], 
                      capture_output=True)
    
    print("✅ 已清理旧版本")
    
    # 步骤2: 清理缓存
    print("\n[2/3] 清理缓存...")
    cache_dirs = [
        os.path.join(sys.prefix, "Lib", "site-packages", "cv2"),
        os.path.join(sys.prefix, "Lib", "site-packages", "opencv_python-"),
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                import shutil
                shutil.rmtree(cache_dir)
                print(f"  清理: {cache_dir}")
            except:
                pass
    
    print("✅ 缓存清理完成")
    
    # 步骤3: 重新安装兼容版本
    print("\n[3/3] 安装兼容版本 opencv-python...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "opencv-python==4.8.1.78"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ OpenCV 安装成功")
    else:
        print(f"⚠️ 安装问题: {result.stderr[:200]}")
        print("尝试备选版本...")
        subprocess.run([sys.executable, "-m", "pip", "install", "opencv-python"])
    
    print("\n" + "=" * 60)
    print("测试 OpenCV...")
    print("=" * 60)
    
    try:
        import cv2
        print(f"✅ OpenCV 版本: {cv2.__version__}")
        
        # 测试导入pyautogui
        import pyautogui
        print("✅ PyAutoGUI 导入成功")
        
        print("\n🎉 修复完成！")
        
    except Exception as e:
        print(f"❌ 仍有问题: {e}")
        print("\n请尝试重启PowerShell后再次运行")


if __name__ == "__main__":
    fix_opencv()
