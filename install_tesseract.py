"""
Tesseract OCR 安装助手（PaddleOCR的备选方案）
"""
import subprocess
import sys
import os


def install_tesseract_python():
    """安装Python Tesseract包"""
    print("[1/2] 安装 Python 包: pytesseract...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "pytesseract", "pillow"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def download_tesseract_installer():
    """提供Tesseract下载链接"""
    print("\n" + "=" * 60)
    print("Tesseract-OCR 软件下载")
    print("=" * 60)
    print()
    print("请下载并安装 Tesseract-OCR:")
    print()
    print("  1. 访问: https://github.com/UB-Mannheim/tesseract/wiki")
    print("  2. 下载: tesseract-ocr-w64-setup-5.x.x.exe (64位)")
    print("  3. 安装时勾选 'Chinese (Simplified)' 语言包")
    print("  4. 安装路径建议: C:\\Program Files\\Tesseract-OCR")
    print()
    print("  或从国内镜像下载:")
    print("  https://digi.bib.uni-mannheim.de/tesseract/")
    print()
    
    # 尝试打开下载页面
    try:
        import webbrowser
        webbrowser.open("https://github.com/UB-Mannheim/tesseract/wiki")
        print("✅ 已打开下载页面")
    except:
        pass


def configure_tesseract_path():
    """配置Tesseract路径"""
    print("\n[2/2] 配置 Tesseract...")
    
    # 常见安装路径
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
    ]
    
    tesseract_path = None
    for path in possible_paths:
        if os.path.exists(path):
            tesseract_path = path
            break
    
    if tesseract_path:
        print(f"✅ 找到 Tesseract: {tesseract_path}")
        
        # 创建配置脚本
        config_script = f'''
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"{tesseract_path}"
'''
        with open("tesseract_config.py", "w") as f:
            f.write(config_script)
        
        print("✅ 配置已保存到: tesseract_config.py")
        return True
    else:
        print("⚠️ 未找到 Tesseract，请确认已安装")
        return False


def test_tesseract():
    """测试Tesseract"""
    print("\n" + "=" * 60)
    print("测试 Tesseract")
    print("=" * 60)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建测试图片
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 35), "Hello World 测试", fill='black', font=font)
        
        img.save("tesseract_test.png")
        
        # 测试识别
        import pytesseract
        text = pytesseract.image_to_string("tesseract_test.png", lang='chi_sim+eng')
        
        print(f"识别结果: {text.strip()}")
        
        # 清理
        os.remove("tesseract_test.png")
        
        if text.strip():
            print("✅ Tesseract 工作正常！")
            return True
        else:
            print("⚠️ 识别结果为空")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def main():
    print("=" * 60)
    print("Tesseract OCR 安装助手")
    print("=" * 60)
    print()
    print("Tesseract 是 PaddleOCR 的轻量级备选方案")
    print("优点: 安装简单，体积小")
    print("缺点: 中文识别率略低于 PaddleOCR")
    print()
    
    # 安装Python包
    if install_tesseract_python():
        print("✅ Python 包安装成功")
    else:
        print("❌ Python 包安装失败")
        return
    
    # 下载提示
    download_tesseract_installer()
    
    input("\n安装完成后按 Enter 继续...")
    
    # 配置路径
    configure_tesseract_path()
    
    # 测试
    test_tesseract()


if __name__ == "__main__":
    main()
