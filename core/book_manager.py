"""
书籍管理器 - 管理书籍加载、分页、进度
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

class BookManager:
    """书籍管理器"""
    
    def __init__(self, books_dir="books"):
        self.books_dir = Path(books_dir)
        self.logger = logging.getLogger(__name__)
        
        # 当前书籍信息
        self.current_book = None
        self.current_book_path = None
        self.pages = []
        self.current_page = 0
        self.total_pages = 0
        
        # 书签
        self.bookmarks = {}
        
        # 确保目录存在
        self.books_dir.mkdir(exist_ok=True)
        
        self.logger.info(f"书籍管理器初始化: {self.books_dir}")
    
    def list_books(self) -> List[Dict]:
        """列出所有可用书籍"""
        books = []
        extensions = ['.txt', '.epub', '.pdf']
        
        for ext in extensions:
            for book_path in self.books_dir.glob(f"*{ext}"):
                if book_path.is_file():
                    try:
                        stat = book_path.stat()
                        books.append({
                            'path': str(book_path),
                            'name': book_path.name,
                            'size': self.format_size(stat.st_size),
                            'modified': stat.st_mtime,
                            'extension': ext[1:].upper()
                        })
                    except Exception as e:
                        self.logger.error(f"获取书籍信息失败 {book_path}: {e}")
        
        # 按修改时间排序
        books.sort(key=lambda x: x['modified'], reverse=True)
        return books
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def load_book(self, book_path: str) -> bool:
        """加载书籍"""
        try:
            book_path = Path(book_path)
            if not book_path.exists():
                self.logger.error(f"书籍不存在: {book_path}")
                return False
            
            self.current_book_path = book_path
            self.current_page = 0
            
            # 根据扩展名使用不同加载器
            if book_path.suffix.lower() == '.txt':
                content = self.load_txt(book_path)
            elif book_path.suffix.lower() == '.epub':
                content = self.load_epub(book_path)
            elif book_path.suffix.lower() == '.pdf':
                content = self.load_pdf(book_path)
            else:
                self.logger.error(f"不支持的文件格式: {book_path.suffix}")
                return False
            
            # 分页
            self.pages = self.split_into_pages(content)
            self.total_pages = len(self.pages)
            
            # 加载书签
            self.load_bookmarks(book_path)
            
            self.logger.info(f"书籍加载成功: {book_path.name}, 共{self.total_pages}页")
            return True
            
        except Exception as e:
            self.logger.error(f"加载书籍失败 {book_path}: {e}", exc_info=True)
            return False
    
    def load_txt(self, file_path: Path) -> str:
        """加载TXT文件"""
        try:
            # 尝试不同编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，使用二进制读取
            with open(file_path, 'rb') as f:
                return f.read().decode('utf-8', errors='ignore')
                
        except Exception as e:
            self.logger.error(f"读取TXT文件失败: {e}")
            return f"读取文件失败: {e}"
    
    def load_epub(self, file_path: Path) -> str:
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
                    text = soup.get_text().strip()
                    if text:
                        content_parts.append(text)
            
            return '\n\n'.join(content_parts)
            
        except ImportError:
            return "请安装 ebooklib 和 beautifulsoup4 库来支持EPUB格式"
        except Exception as e:
            self.logger.error(f"读取EPUB文件失败: {e}")
            return f"读取EPUB失败: {e}"
    
    def load_pdf(self, file_path: Path) -> str:
        """加载PDF文件"""
        try:
            import PyPDF2
            
            content_parts = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        content_parts.append(text)
            
            return '\n\n'.join(content_parts)
            
        except ImportError:
            return "请安装 PyPDF2 库来支持PDF格式"
        except Exception as e:
            self.logger.error(f"读取PDF文件失败: {e}")
            return f"读取PDF失败: {e}"
    
    def split_into_pages(self, text: str, chars_per_page: int = 1500) -> List[str]:
        """将文本分割成页"""
        if not text:
            return ["空内容"]
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        pages = []
        current_page = []
        current_chars = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_chars = len(para)
            
            if current_chars + para_chars <= chars_per_page or not current_page:
                # 可以添加到当前页
                current_page.append(para)
                current_chars += para_chars
            else:
                # 当前页已满，开始新页
                pages.append('\n'.join(current_page))
                current_page = [para]
                current_chars = para_chars
        
        # 添加最后一页
        if current_page:
            pages.append('\n'.join(current_page))
        
        return pages
    
    def get_page(self, page_num: int) -> Optional[str]:
        """获取指定页码的内容"""
        if 0 <= page_num < len(self.pages):
            return self.pages[page_num]
        return None
    
    def get_current_page(self) -> Optional[str]:
        """获取当前页内容"""
        return self.get_page(self.current_page)
    
    def go_to_page(self, page_num: int) -> bool:
        """跳转到指定页码"""
        if 0 <= page_num < len(self.pages):
            self.current_page = page_num
            return True
        return False
    
    def next_page(self) -> bool:
        """下一页"""
        return self.go_to_page(self.current_page + 1)
    
    def prev_page(self) -> bool:
        """上一页"""
        return self.go_to_page(self.current_page - 1)
    
    def get_progress(self) -> float:
        """获取阅读进度"""
        if self.total_pages == 0:
            return 0.0
        return (self.current_page + 1) / self.total_pages
    
    def add_bookmark(self, name: str = None):
        """添加书签"""
        if not self.current_book_path:
            return False
        
        if name is None:
            name = f"书签 {len(self.bookmarks) + 1}"
        
        self.bookmarks[name] = {
            'page': self.current_page,
            'timestamp': time.time()
        }
        
        self.save_bookmarks()
        return True
    
    def goto_bookmark(self, name: str) -> bool:
        """跳转到书签"""
        if name in self.bookmarks:
            return self.go_to_page(self.bookmarks[name]['page'])
        return False
    
    def load_bookmarks(self, book_path: Path):
        """加载书签"""
        bookmark_file = self.get_bookmark_path(book_path)
        if bookmark_file.exists():
            try:
                import json
                with open(bookmark_file, 'r', encoding='utf-8') as f:
                    self.bookmarks = json.load(f)
            except Exception as e:
                self.logger.error(f"加载书签失败: {e}")
                self.bookmarks = {}
    
    def save_bookmarks(self):
        """保存书签"""
        if not self.current_book_path:
            return
        
        bookmark_file = self.get_bookmark_path(self.current_book_path)
        try:
            import json
            with open(bookmark_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存书签失败: {e}")
    
    def get_bookmark_path(self, book_path: Path) -> Path:
        """获取书签文件路径"""
        return book_path.parent / f"{book_path.stem}.bookmarks.json"