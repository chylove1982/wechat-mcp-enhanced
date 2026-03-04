"""
OCR模块 - 支持多种OCR引擎
"""
import os
from typing import List, Dict, Optional
from PIL import Image

# 尝试导入OCR引擎
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class OCREngine:
    """OCR引擎封装"""
    
    def __init__(self, engine: str = "auto"):
        """
        初始化OCR引擎
        
        Args:
            engine: "auto", "paddle", "tesseract", "none"
        """
        self.engine_type = engine
        self.paddle_ocr = None
        
        if engine == "auto":
            # 自动选择最佳引擎
            if PADDLE_AVAILABLE:
                self.engine_type = "paddle"
            elif TESSERACT_AVAILABLE:
                self.engine_type = "tesseract"
            else:
                self.engine_type = "none"
        
        if self.engine_type == "paddle" and PADDLE_AVAILABLE:
            self._init_paddle()
        
        print(f"[OCR] 使用引擎: {self.engine_type}")
    
    def _init_paddle(self):
        """初始化PaddleOCR"""
        try:
            self.paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                show_log=False,
                use_gpu=False
            )
            print("[OCR] PaddleOCR 初始化成功")
        except Exception as e:
            print(f"[OCR错误] PaddleOCR初始化失败: {e}")
            self.engine_type = "none"
    
    def recognize(self, image_path: str) -> List[Dict]:
        """
        识别图片中的文字
        
        Returns:
            List[Dict]: [{"text": str, "confidence": float, "position": tuple}, ...]
        """
        if self.engine_type == "paddle":
            return self._recognize_paddle(image_path)
        elif self.engine_type == "tesseract":
            return self._recognize_tesseract(image_path)
        else:
            print("[OCR警告] 没有可用的OCR引擎")
            return []
    
    def _recognize_paddle(self, image_path: str) -> List[Dict]:
        """使用PaddleOCR识别"""
        try:
            result = self.paddle_ocr.ocr(image_path, cls=True)
            
            messages = []
            if result and result[0]:
                for line in result[0]:
                    if line:
                        bbox = line[0]  # 边界框
                        text = line[1][0]  # 文字内容
                        confidence = line[1][1]  # 置信度
                        
                        # 计算中心点位置
                        center_x = sum([p[0] for p in bbox]) / 4
                        center_y = sum([p[1] for p in bbox]) / 4
                        
                        messages.append({
                            'text': text,
                            'confidence': confidence,
                            'position': (center_x, center_y),
                            'bbox': bbox
                        })
            
            return messages
            
        except Exception as e:
            print(f"[OCR错误] PaddleOCR识别失败: {e}")
            return []
    
    def _recognize_tesseract(self, image_path: str) -> List[Dict]:
        """使用Tesseract识别"""
        try:
            img = Image.open(image_path)
            
            # 获取详细数据
            data = pytesseract.image_to_data(img, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)
            
            messages = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                if int(data['conf'][i]) > 30:  # 置信度阈值
                    text = data['text'][i].strip()
                    if text:
                        x = data['left'][i] + data['width'][i] / 2
                        y = data['top'][i] + data['height'][i] / 2
                        
                        messages.append({
                            'text': text,
                            'confidence': data['conf'][i] / 100.0,
                            'position': (x, y),
                            'bbox': None
                        })
            
            return messages
            
        except Exception as e:
            print(f"[OCR错误] Tesseract识别失败: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查OCR是否可用"""
        return self.engine_type != "none"


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("OCR 模块测试")
    print("=" * 60)
    
    # 检查可用引擎
    print(f"\n引擎状态:")
    print(f"  PaddleOCR: {'✅' if PADDLE_AVAILABLE else '❌'}")
    print(f"  Tesseract: {'✅' if TESSERACT_AVAILABLE else '❌'}")
    
    # 初始化OCR
    ocr = OCREngine("auto")
    
    if not ocr.is_available():
        print("\n⚠️ 没有可用的OCR引擎")
        print("请运行: python install_ocr.py")
        exit(1)
    
    # 创建测试图片
    from PIL import ImageDraw, ImageFont
    
    print("\n创建测试图片...")
    img = Image.new('RGB', (400, 150), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("msyh.ttc", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((20, 30), "左侧消息：你好", fill='black', font=font)
    draw.text((200, 80), "右侧回复：Hello", fill='blue', font=font)
    
    test_path = "test_ocr.png"
    img.save(test_path)
    
    # 测试识别
    print(f"\n识别测试图片...")
    results = ocr.recognize(test_path)
    
    print(f"\n识别结果 ({len(results)}条):")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['text']} (置信度: {r['confidence']:.2f})")
    
    # 清理
    os.remove(test_path)
    
    print("\n✅ OCR 测试完成!")
