"""
OCR安装修复脚本 - 解决权限问题
"""
import subprocess
import sys
import os
import shutil


def fix_cv2_permission():
    """修复cv2文件权限问题"""
    cv2_path = os.path.join(sys.prefix, "Lib", "site-packages", "cv2", "cv2.pyd")
    
    if os.path.exists(cv2_path):
        try:
            # 尝试重命名旧文件（解除占用）
            backup_path = cv2_path + ".backup"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            shutil.move(cv2_path, backup_path)
            print(f"✅ 已备份并移除旧文件: {cv2_path}")
            return True
        except Exception as e:
            print(f"⚠️ 无法处理文件: {e}")
            return False
    return True


def install_paddle_cpu():
    """安装PaddlePaddle CPU版本"""
    print("\n[1/2] 安装 PaddlePaddle CPU版本...")
    
    # 先卸载可能冲突的包
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "opencv-python", "opencv-contrib-python"], 
                   capture_output=True)
    
    # 安装paddlepaddle
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "paddlepaddle==2.6.1", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"⚠️ 清华源失败，尝试官方源...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "paddlepaddle==2.6.1"],
            capture_output=True,
            text=True
        )
    
    return result.returncode == 0


def install_paddleocr():
    """安装PaddleOCR"""
    print("[2/2] 安装 PaddleOCR...")
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "paddleocr==2.7.3", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"⚠️ 清华源失败，尝试官方源...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "paddleocr==2.7.3"],
            capture_output=True,
            text=True
        )
    
    return result.returncode == 0


def main():
    print("=" * 60)
    print("OCR 安装修复工具")
    print("=" * 60)
    print()
    
    print("步骤:")
    print("1. 修复文件权限")
    print("2. 安装 PaddlePaddle")
    print("3. 安装 PaddleOCR")
    print()
    
    # 步骤1: 修复权限
    print("[步骤 1/3] 修复文件权限...")
    if fix_cv2_permission():
        print("✅ 权限修复完成")
    else:
        print("⚠️ 权限修复失败，尝试继续安装...")
    
    # 步骤2: 安装Paddle
    print("\n[步骤 2/3] 安装 PaddlePaddle...")
    if install_paddle_cpu():
        print("✅ PaddlePaddle 安装成功")
    else:
        print("❌ PaddlePaddle 安装失败")
        return
    
    # 步骤3: 安装PaddleOCR
    print("\n[步骤 3/3] 安装 PaddleOCR...")
    if install_paddleocr():
        print("✅ PaddleOCR 安装成功")
    else:
        print("❌ PaddleOCR 安装失败")
        return
    
    print("\n" + "=" * 60)
    print("🎉 安装完成！")
    print("=" * 60)
    print()
    print("测试命令:")
    print("  python -c \"from paddleocr import PaddleOCR; print('✅ 成功')\"")


if __name__ == "__main__":
    main()
