"""
消息监听调试工具
帮助诊断为什么监听没有返回内容
"""
import time
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ocr_directly():
    """直接测试OCR功能"""
    print("=" * 60)
    print("步骤1: 测试OCR功能")
    print("=" * 60)
    
    from ocr_engine import OCREngine
    from PIL import Image, ImageDraw, ImageFont
    
    ocr = OCREngine("auto")
    
    # 创建测试图片（模拟微信聊天界面）
    print("\n创建测试图片...")
    img = Image.new('RGB', (600, 300), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # 绘制背景
    draw.rectangle([0, 0, 600, 300], fill=(240, 240, 240))
    
    # 左侧消息（对方）- 灰色背景
    draw.rounded_rectangle([20, 30, 300, 80], radius=10, fill=(255, 255, 255))
    draw.text((35, 45), "你好，在吗？", fill=(0, 0, 0))
    
    # 右侧消息（自己）- 绿色背景
    draw.rounded_rectangle([350, 100, 580, 150], radius=10, fill=(149, 236, 105))
    draw.text((365, 115), "在的，请说", fill=(0, 0, 0))
    
    # 左侧消息（对方）
    draw.rounded_rectangle([20, 180, 400, 230], radius=10, fill=(255, 255, 255))
    draw.text((35, 195), "这个文件怎么打开？", fill=(0, 0, 0))
    
    test_path = "debug_chat.png"
    img.save(test_path)
    print(f"✅ 测试图片已保存: {test_path}")
    
    # OCR识别
    print("\n进行OCR识别...")
    results = ocr.recognize(test_path)
    
    print(f"\n识别结果 ({len(results)}条):")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r.get('position', 'N/A')}] {r['text']} (置信度: {r['confidence']:.2f})")
    
    if len(results) == 0:
        print("⚠️ 警告: 没有识别到任何文字！")
        print("  可能原因:")
        print("  - Tesseract中文语言包未安装")
        print("  - 图片质量问题")
        print("  - OCR引擎配置问题")
    
    return len(results) > 0


def test_database():
    """测试数据库"""
    print("\n" + "=" * 60)
    print("步骤2: 测试数据库")
    print("=" * 60)
    
    from database import get_database
    
    db = get_database("debug_test.db")
    
    # 保存测试消息
    print("\n保存测试消息...")
    db.save_message("测试联系人", "对方", "测试消息1", "text")
    db.save_message("测试联系人", "me", "回复消息", "text")
    
    # 查询
    history = db.get_chat_history("测试联系人", limit=10)
    print(f"✅ 查询到 {len(history)} 条记录")
    
    for msg in history:
        print(f"  [{msg['timestamp']}] {msg['sender']}: {msg['content']}")
    
    # 清理
    try:
        os.remove("debug_test.db")
    except:
        pass
    
    return len(history) > 0


def test_message_listener():
    """测试消息监听（模拟模式）"""
    print("\n" + "=" * 60)
    print("步骤3: 测试消息监听")
    print("=" * 60)
    
    from database import get_database
    from message_listener import MessageListener
    
    db = get_database("debug_listener.db")
    listener = MessageListener(db)
    
    print(f"OCR引擎类型: {listener.ocr.engine_type}")
    print(f"OCR是否可用: {listener.ocr.is_available()}")
    
    # 手动触发一次检查
    print("\n手动触发消息检查...")
    
    # 由于没有真实微信窗口，这里会返回空
    # 但我们可以检查是否有错误
    try:
        messages = listener.check_new_messages()
        print(f"检查结果: {len(messages)} 条新消息")
        
        if len(messages) == 0:
            print("\n⚠️ 没有检测到消息（预期行为，如果没有打开微信聊天窗口）")
            
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 清理
    try:
        os.remove("debug_listener.db")
        os.remove("_temp_ocr.png")
    except:
        pass
    
    return True


def check_tesseract_chinese():
    """检查Tesseract中文支持"""
    print("\n" + "=" * 60)
    print("步骤4: 检查Tesseract中文支持")
    print("=" * 60)
    
    try:
        import pytesseract
        
        # 获取已安装的语言
        langs = pytesseract.get_languages()
        print(f"已安装语言: {langs}")
        
        if 'chi_sim' in langs:
            print("✅ 中文语言包已安装")
            return True
        else:
            print("❌ 中文语言包未安装！")
            print("\n请下载Tesseract中文语言包:")
            print("1. 访问: https://github.com/UB-Mannheim/tesseract/wiki")
            print("2. 重新安装Tesseract，勾选 'Chinese (Simplified)'")
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("消息监听调试工具")
    print("=" * 60)
    print()
    
    results = []
    
    # 运行所有测试
    results.append(("OCR功能", test_ocr_directly()))
    results.append(("数据库", test_database()))
    results.append(("消息监听", test_message_listener()))
    results.append(("中文支持", check_tesseract_chinese()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("调试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    print("\n" + "=" * 60)
    print("建议:")
    print("=" * 60)
    
    if not results[0][1]:  # OCR失败
        print("- OCR识别失败，建议安装Tesseract中文语言包")
    
    if not results[3][1]:  # 中文支持失败
        print("- 中文识别需要安装chi_sim语言包")
        print("- 或使用PaddleOCR（识别率更高）")
    
    if all(r[1] for r in results):
        print("✅ 所有测试通过！")
        print("\n如果消息监听仍无内容，请确保:")
        print("1. 微信PC版已打开并登录")
        print("2. 已打开某个聊天窗口")
        print("3. 窗口未被其他窗口完全遮挡")
    
    # 清理
    try:
        os.remove("debug_chat.png")
    except:
        pass


if __name__ == "__main__":
    main()
