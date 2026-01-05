"""
文件加载器 - 支持多种文件格式
"""

import os
import zipfile
import tempfile
from pathlib import Path
from typing import Optional

class FileLoader:
    """通用文件加载器"""
    
    @staticmethod
    def load_file(file_path: str) -> Optional[str]:
        """通用文件加载方法"""
        path = Path(file_path)
        
        if not path.exists():
            return None
        
        suffix = path.suffix.lower()
        
        if suffix == '.txt':
            return FileLoader.load_txt(path)
        elif suffix == '.epub':
            return FileLoader.load_epub(path)
        elif suffix == '.pdf':
            return FileLoader.load_pdf(path)
        elif suffix in ['.zip', '.rar', '.7z']:
            return FileLoader.load_archive(path)
        else:
            return None
    
    @staticmethod
    def load_txt(file_path: Path) -> Optional[str]:
        """加载文本文件"""
        try:
            encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'utf-16']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            # 尝试二进制读取
            with open(file_path, 'rb') as f:
                return f.read().decode('utf-8', errors='ignore')
                
        except Exception as e:
            print(f"加载TXT文件失败: {e}")
            return None
    
    @staticmethod
    def load_epub(file_path: Path) -> Optional[str]:
        """加载EPUB文件"""
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            
            book = epub.read_epub(str(file_path))
            content_parts = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # 移除脚本和样式
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text = soup.get_text()
                    # 清理空白字符
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    if text:
                        content_parts.append(text)
            
            return '\n\n'.join(content_parts)
            
        except ImportError:
            print("请安装: pip install ebooklib beautifulsoup4")
            return None
        except Exception as e:
            print(f"加载EPUB文件失败: {e}")
            return None
    
    @staticmethod
    def load_pdf(file_path: Path) -> Optional[str]:
        """加载PDF文件"""
        try:
            # 尝试PyMuPDF
            try:
                import fitz
                doc = fitz.open(str(file_path))
                text_parts = []
                for page in doc:
                    text = page.get_text()
                    if text:
                        text_parts.append(text)
                return '\n\n'.join(text_parts)
            except ImportError:
                pass
            
            # 尝试PyPDF2
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text_parts = []
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    return '\n\n'.join(text_parts)
            except ImportError:
                pass
            
            # 尝试pdfminer
            try:
                from pdfminer.high_level import extract_text
                return extract_text(file_path)
            except ImportError:
                pass
            
            print("请安装PDF解析库: pip install PyMuPDF 或 PyPDF2 或 pdfminer.six")
            return None
            
        except Exception as e:
            print(f"加载PDF文件失败: {e}")
            return None
    
    @staticmethod
    def load_archive(file_path: Path) -> Optional[str]:
        """加载压缩文件"""
        try:
            if file_path.suffix.lower() != '.zip':
                print("目前只支持ZIP格式")
                return None
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # 寻找文本文件
                text_files = []
                for name in zip_ref.namelist():
                    if name.lower().endswith(('.txt', '.epub', '.pdf')):
                        text_files.append(name)
                
                if not text_files:
                    return "压缩包中没有找到支持的文本文件"
                
                # 解压第一个找到的文本文件
                target_file = text_files[0]
                with tempfile.TemporaryDirectory() as tmpdir:
                    zip_ref.extract(target_file, tmpdir)
                    extracted_path = Path(tmpdir) / target_file
                    return FileLoader.load_file(str(extracted_path))
                    
        except Exception as e:
            print(f"加载压缩文件失败: {e}")
            return None
    
    @staticmethod
    def detect_encoding(file_path: Path) -> str:
        """检测文件编码"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read(1024)
                result = chardet.detect(raw_data)
                return result['encoding']
        except ImportError:
            return 'utf-8'
        except Exception:
            return 'utf-8'