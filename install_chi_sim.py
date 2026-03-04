"""
安装Tesseract中文语言包
"""
import urllib.request
import os
import sys
import shutil


def install_chinese_lang():
    """安装Tesseract中文语言包"""
    print("=" * 60)
    print("安装 Tesseract 中文语言包")
    print("=" * 60)
    print()
    
    # Tesseract语言包下载地址
    lang_url = "https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata"
    
    # 查找Tesseract安装目录
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tessdata",
        r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
        r"C:\Tesseract-OCR\tessdata",
    ]
    
    tessdata_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            tessdata_dir = path
            break
    
    if not tessdata_dir:
        print("❌ 未找到Tesseract安装目录")
        print("\n请确认Tesseract已安装到以下位置之一:")
        for p in possible_paths:
            print(f"  - {p}")
        return False
    
    print(f"✅ 找到Tesseract目录: {tessdata_dir}")
    
    # 下载中文语言包
    lang_file = os.path.join(tessdata_dir, "chi_sim.traineddata")
    
    if os.path.exists(lang_file):
        print(f"✅ 中文语言包已存在: {lang_file}")
        return True
    
    print(f"\n下载中文语言包...")
    print(f"来源: {lang_url}")
    print(f"目标: {lang_file}")
    print()
    
    try:
        # 使用urllib下载
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        
        print("下载中... (文件约40MB，请耐心等待)")
        urllib.request.urlretrieve(lang_url, lang_file + ".tmp")
        
        # 移动文件
        shutil.move(lang_file + ".tmp", lang_file)
        
        print(f"✅ 下载完成！")
        
        # 验证
        import pytesseract
        langs = pytesseract.get_languages()
        
        if 'chi_sim' in langs:
            print(f"✅ 中文语言包安装成功！")
            print(f"   已安装语言: {langs}")
            return True
        else:
            print("⚠️ 安装后未检测到中文语言包")
            return False
            
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        print("\n手动安装方法:")
        print("1. 浏览器打开: https://github.com/tesseract-ocr/tessdata")
        print("2. 下载文件: chi_sim.traineddata")
        print(f"3. 复制到: {tessdata_dir}")
        return False


if __name__ == "__main__":
    install_chinese_lang()
