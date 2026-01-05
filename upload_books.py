#!/usr/bin/env python3
"""
批量上传书籍脚本
"""

import os
import sys
import shutil
from pathlib import Path

def upload_books(source_dir, target_dir="books"):
    """批量上传书籍"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        print(f"源目录不存在: {source_dir}")
        return
    
    # 创建目标目录
    target_path.mkdir(exist_ok=True)
    
    # 支持的文件格式
    extensions = ['.txt', '.epub', '.pdf']
    
    # 查找并复制文件
    copied_count = 0
    for ext in extensions:
        for book_file in source_path.glob(f"**/*{ext}"):
            if book_file.is_file():
                target_file = target_path / book_file.name
                
                # 处理重名文件
                counter = 1
                while target_file.exists():
                    name = book_file.stem
                    suffix = book_file.suffix
                    target_file = target_path / f"{name}_{counter}{suffix}"
                    counter += 1
                
                # 复制文件
                try:
                    shutil.copy2(book_file, target_file)
                    print(f"已复制: {book_file.name} -> {target_file.name}")
                    copied_count += 1
                except Exception as e:
                    print(f"复制失败 {book_file.name}: {e}")
    
    print(f"\n完成！共复制 {copied_count} 本书籍")
    print(f"目录: {target_path.absolute()}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        source_dir = sys.argv[1]
    else:
        source_dir = input("请输入源目录路径: ")
    
    upload_books(source_dir)