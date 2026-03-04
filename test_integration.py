"""
集成测试 - 验证所有模块能正确导入和初始化
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有导入"""
    print("=" * 60)
    print("测试模块导入")
    print("=" * 60)
    
    tests = [
        ("database", ["ChatDatabase", "get_database"]),
        ("ocr_engine", ["OCREngine", "PADDLE_AVAILABLE", "TESSERACT_AVAILABLE"]),
        ("auto_reply", ["AutoReplyEngine", "PRESET_RULES"]),
        ("message_listener", ["MessageListener", "Message"]),
    ]
    
    all_passed = True
    
    for module_name, expected_items in tests:
        try:
            module = __import__(module_name)
            for item in expected_items:
                if not hasattr(module, item):
                    print(f"❌ {module_name}.{item} 不存在")
                    all_passed = False
                else:
                    print(f"✅ {module_name}.{item}")
            print(f"✅ {module_name} 导入成功")
        except Exception as e:
            print(f"❌ {module_name} 导入失败: {e}")
            all_passed = False
    
    return all_passed


def test_database():
    """测试数据库"""
    print("\n" + "=" * 60)
    print("测试数据库")
    print("=" * 60)
    
    try:
        from database import get_database
        
        db = get_database("test_integration.db")
        print("✅ 数据库初始化成功")
        
        # 测试保存消息
        db.save_message("测试用户", "对方", "你好", "text")
        print("✅ 保存消息成功")
        
        # 测试查询
        history = db.get_chat_history("测试用户", limit=5)
        print(f"✅ 查询历史记录: {len(history)}条")
        
        # 测试统计
        stats = db.get_statistics()
        print(f"✅ 获取统计: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr():
    """测试OCR"""
    print("\n" + "=" * 60)
    print("测试OCR引擎")
    print("=" * 60)
    
    try:
        from ocr_engine import OCREngine, PADDLE_AVAILABLE, TESSERACT_AVAILABLE
        
        print(f"PaddleOCR: {'✅' if PADDLE_AVAILABLE else '❌'}")
        print(f"Tesseract: {'✅' if TESSERACT_AVAILABLE else '❌'}")
        
        ocr = OCREngine("auto")
        print(f"✅ OCR引擎初始化: {ocr.engine_type}")
        
        return True
    except Exception as e:
        print(f"❌ OCR测试失败: {e}")
        return False


def test_auto_reply():
    """测试自动回复"""
    print("\n" + "=" * 60)
    print("测试自动回复")
    print("=" * 60)
    
    try:
        from database import get_database
        from auto_reply import AutoReplyEngine
        
        db = get_database("test_integration.db")
        engine = AutoReplyEngine(db)
        print("✅ 自动回复引擎初始化成功")
        
        # 测试设置规则
        rules = [
            {"keyword": "在吗", "response": "在的", "priority": 10},
            {"keyword": "*", "response": "稍后回复", "priority": 0}
        ]
        engine.set_auto_reply("测试用户", True, 'keyword', rules)
        print("✅ 设置自动回复规则成功")
        
        # 测试回复
        reply = engine.get_reply("测试用户", "在吗")
        print(f"✅ 测试回复: {reply}")
        
        return True
    except Exception as e:
        print(f"❌ 自动回复测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_listener():
    """测试消息监听"""
    print("\n" + "=" * 60)
    print("测试消息监听")
    print("=" * 60)
    
    try:
        from database import get_database
        from message_listener import MessageListener
        
        db = get_database("test_integration.db")
        listener = MessageListener(db)
        print("✅ 消息监听器初始化成功")
        print(f"  - OCR引擎: {listener.ocr.engine_type}")
        print(f"  - 监听状态: {listener.is_listening}")
        
        return True
    except Exception as e:
        print(f"❌ 消息监听测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("微信MCP集成测试")
    print("=" * 60)
    
    results = []
    
    results.append(("导入测试", test_imports()))
    results.append(("数据库测试", test_database()))
    results.append(("OCR测试", test_ocr()))
    results.append(("自动回复测试", test_auto_reply()))
    results.append(("消息监听测试", test_message_listener()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    
    print(f"\n总计: {passed_count}/{total} 项测试通过")
    
    # 清理测试文件
    try:
        os.remove("test_integration.db")
        os.remove("_temp_ocr.png")
    except:
        pass


if __name__ == "__main__":
    main()
