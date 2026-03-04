# -*- coding: utf-8 -*-
"""
OCR安装助手
帮助用户安装和配置PaddleOCR
"""

import subprocess
import sys
import os


def check_paddleocr():
    """检查PaddleOCR是否已安装"""
    try:
        from paddleocr import PaddleOCR
        print("✅ PaddleOCR 已安装")
        return True
    except ImportError:
        print("❌ PaddleOCR 未安装")
        return False


def install_paddleocr():
    """安装PaddleOCR"""
    print("\n正在安装 PaddleOCR...")
    print("这可能需要几分钟时间，请耐心等待...\n")
    
    # 安装paddlepaddle（CPU版本）
    print("[1/2] 安装 paddlepaddle...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "paddlepaddle", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"⚠️ 安装 paddlepaddle 时出现问题:")
        print(result.stderr)
        print("\n尝试使用默认源...")
        subprocess.run([sys.executable, "-m", "pip", "install", "paddlepaddle"])
    
    # 安装paddleocr
    print("[2/2] 安装 paddleocr...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "paddleocr", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"⚠️ 安装 paddleocr 时出现问题:")
        print(result.stderr)
        print("\n尝试使用默认源...")
        subprocess.run([sys.executable, "-m", "pip", "install", "paddleocr"])
    
    print("\n✅ 安装完成！")


def test_ocr():
    """测试OCR功能"""
    print("\n测试 OCR 功能...")
    
    try:
        from paddleocr import PaddleOCR
        
        # 初始化OCR引擎
        print("初始化 PaddleOCR 引擎...")
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            show_log=False,
            use_gpu=False
        )
        
        print("✅ OCR 引擎初始化成功！")
        
        # 创建一个测试图片
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建白色背景图片
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # 添加文字
        try:
            font = ImageFont.truetype("msyh.ttc", 24)  # 微软雅黑
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 35), "测试文字：Hello 世界", fill='black', font=font)
        
        # 保存测试图片
        test_path = "ocr_test.png"
        img.save(test_path)
        
        # OCR识别
        print(f"\n识别测试图片: {test_path}")
        result = ocr.ocr(test_path, cls=True)
        
        if result and result[0]:
            print("\n识别结果:")
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                print(f"  - {text} (置信度: {confidence:.2f})")
        
        # 清理测试文件
        os.remove(test_path)
        
        print("\n✅ OCR 测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ OCR 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("微信MCP - OCR 安装助手")
    print("=" * 60)
    
    # 检查是否已安装
    if check_paddleocr():
        print("\nPaddleOCR 已安装，进行测试...")
        test_ocr()
        return
    
    # 询问是否安装
    print("\nPaddleOCR 是微信消息监听功能的核心组件，用于识别聊天记录。")
    response = input("\n是否安装 PaddleOCR? (y/n): ")
    
    if response.lower() == 'y':
        install_paddleocr()
        
        # 再次检查
        if check_paddleocr():
            print("\n🎉 安装成功！")
            test_ocr()
        else:
            print("\n❌ 安装后仍无法导入，请检查错误信息")
    else:
        print("\n已取消安装。消息监听功能将无法使用 OCR 识别。")
        print("您可以使用 Tesseract 作为备选方案（识别率较低）:")
        print("  pip install pytesseract")
        print("  # 同时需要安装 Tesseract-OCR 软件")


if __name__ == "__main__":
    main()
