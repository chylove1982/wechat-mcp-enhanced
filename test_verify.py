"""
测试图片OCR识别 - verify.png
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ocr_engine import OCREngine
from PIL import Image

def test_image(image_path):
    """测试单张图片的OCR识别"""
    print("=" * 60)
    print(f"OCR 测试: {image_path}")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        return
    
    # 显示图片信息
    img = Image.open(image_path)
    print(f"\n图片信息:")
    print(f"  尺寸: {img.size}")
    print(f"  格式: {img.format}")
    print(f"  模式: {img.mode}")
    
    # 初始化OCR
    print(f"\n初始化OCR引擎...")
    ocr = OCREngine("auto")
    
    if not ocr.is_available():
        print("❌ OCR引擎不可用")
        return
    
    # 识别
    print(f"\n开始识别...")
    results = ocr.recognize(image_path)
    
    print(f"\n识别结果 ({len(results)}条):")
    print("-" * 60)
    
    for i, r in enumerate(results, 1):
        text = r['text']
        conf = r['confidence']
        pos = r.get('position', 'N/A')
        
        print(f"{i}. [{pos}] {text}")
        print(f"   置信度: {conf:.2f}")
        print()
    
    if len(results) == 0:
        print("⚠️ 未识别到任何文字")
        print("\n可能原因:")
        print("- 图片中没有文字")
        print("- 文字太小或模糊")
        print("- OCR引擎配置问题")
        print("- 如果是中文，需要安装chi_sim语言包")
    else:
        print(f"✅ 共识别 {len(results)} 条文字")


if __name__ == "__main__":
    # 测试 verify.png
    image_path = r"C:\mcp\winautowx\verify.png"
    
    test_image(image_path)
