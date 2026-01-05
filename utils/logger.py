"""
日志工具
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logger(name: str, 
                 level: int = logging.INFO,
                 log_dir: Optional[str] = None,
                 console: bool = True) -> logging.Logger:
    """设置日志配置"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 创建日志文件，按日期命名
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_path / f"{name}_{today}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_log_file_path(name: str, log_dir: str) -> str:
    """获取日志文件路径"""
    today = datetime.now().strftime('%Y-%m-%d')
    log_path = Path(log_dir) / f"{name}_{today}.log"
    return str(log_path)

def clear_old_logs(log_dir: str, days: int = 7):
    """清理旧日志文件"""
    import time
    from pathlib import Path
    
    log_path = Path(log_dir)
    if not log_path.exists():
        return
    
    cutoff_time = time.time() - (days * 24 * 3600)
    
    for log_file in log_path.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
            except Exception as e:
                print(f"删除日志文件失败 {log_file}: {e}")