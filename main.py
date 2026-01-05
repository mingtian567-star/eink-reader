#!/usr/bin/env python3
"""
水墨屏阅读器 - 主程序
E-Ink Reader Main Program
"""

import os
import sys
import time
import signal
import logging
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    from core.display_manager import DisplayManager
    from core.book_manager import BookManager
    from hardware.gpio_controller import GPIOController
    from hardware.eink_driver import EinkDisplay
    from ui.screens import HomeScreen, ReadingScreen, MenuScreen
    from utils.logger import setup_logger
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖已安装")
    sys.exit(1)

class EinkReader:
    def __init__(self):
        """初始化阅读器"""
        # 设置项目根目录
        self.project_root = project_root
        
        # 设置日志
        self.logger = setup_logger('eink_reader')
        self.logger.info("=" * 50)
        self.logger.info("启动水墨屏阅读器")
        self.logger.info(f"项目路径: {self.project_root}")
        
        # 运行状态
        self.running = True
        self.current_screen = None
        
        # 加载配置
        self.config = self.load_config()
        
        # 初始化组件
        self.display = None
        self.book_manager = None
        self.gpio = None
        self.screens = {}
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def load_config(self):
        """加载配置文件"""
        config_path = self.project_root / "config.json"
        default_config = {
            "screen_type": "7in5",
            "font_size": 20,
            "line_spacing": 1.5,
            "margin": 20,
            "auto_sleep": 300,
            "books_dir": str(self.project_root / "books"),
            "current_book": None,
            "current_page": 0,
            "theme": "light"
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                self.logger.info(f"配置加载成功: {config_path}")
                return config
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
        
        return default_config
    
    def save_config(self):
        """保存配置"""
        try:
            config_path = self.project_root / "config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.logger.debug("配置保存成功")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
    
    def initialize(self):
        """初始化所有组件"""
        self.logger.info("初始化组件...")
        
        try:
            # 1. 初始化显示
            self.display = EinkDisplay(self.config.get("screen_type", "7in5"))
            self.logger.info("显示初始化完成")
            
            # 2. 显示启动画面
            self.show_splash_screen()
            
            # 3. 初始化书籍管理器
            self.book_manager = BookManager(self.config["books_dir"])
            self.logger.info("书籍管理器初始化完成")
            
            # 4. 初始化GPIO控制
            self.gpio = GPIOController()
            self.gpio.start_monitoring()
            self.logger.info("GPIO控制器初始化完成")
            
            # 5. 初始化屏幕管理器
            self.init_screens()
            
            # 6. 加载上次阅读的书籍
            if self.config.get("current_book"):
                self.load_book(self.config["current_book"])
            
            self.logger.info("所有组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失败: {e}", exc_info=True)
            if self.display:
                self.display.show_error(f"初始化失败: {str(e)[:50]}")
            return False
    
    def show_splash_screen(self):
        """显示启动画面"""
        splash_text = """
        水墨屏阅读器
        ============
        
        版本: 1.0.0
        
        正在启动系统...
        请稍候...
        """
        self.display.clear()
        self.display.draw_text(splash_text, font_size=20)
        self.display.update()
        time.sleep(1)
    
    def init_screens(self):
        """初始化所有屏幕"""
        self.screens = {
            "home": HomeScreen(self.display, self.book_manager, self.config),
            "reading": ReadingScreen(self.display, self.book_manager, self.config),
            "menu": MenuScreen(self.display, self.book_manager, self.config)
        }
        self.current_screen = "home"
    
    def load_book(self, book_path):
        """加载书籍"""
        self.logger.info(f"加载书籍: {book_path}")
        
        if self.book_manager.load_book(book_path):
            self.config["current_book"] = book_path
            self.config["current_page"] = 0
            self.save_config()
            
            # 切换到阅读屏幕
            self.current_screen = "reading"
            self.show_current_screen()
            
            return True
        return False
    
    def show_current_screen(self):
        """显示当前屏幕"""
        if self.current_screen in self.screens:
            self.screens[self.current_screen].show()
    
    def handle_event(self, event_type, event_data=None):
        """处理事件"""
        self.logger.debug(f"处理事件: {event_type}, 数据: {event_data}")
        
        if self.current_screen in self.screens:
            result = self.screens[self.current_screen].handle_event(event_type, event_data)
            if result:
                event, data = result
                self.handle_event(event, data)
        
        # 系统级事件处理
        if event_type == "LOAD_BOOK" and "path" in event_data:
            self.load_book(event_data["path"])
        elif event_type == "EXIT":
            self.running = False
        elif event_type == "SAVE_CONFIG":
            self.save_config()
        elif event_type == "SHOW_HOME":
            self.current_screen = "home"
            self.show_current_screen()
        elif event_type == "SHOW_MENU":
            self.current_screen = "menu"
            self.show_current_screen()
    
    def process_events(self):
        """处理事件循环"""
        # 处理GPIO事件
        if self.gpio:
            events = self.gpio.get_events()
            for event_type, button in events:
                if event_type == "BUTTON_CLICK":
                    self.handle_button(button)
                elif event_type == "BUTTON_LONG_PRESS":
                    self.handle_button_long(button)
        
        # 这里可以添加其他事件源（如网络、定时器等）
    
    def handle_button(self, button):
        """处理按钮点击"""
        button_events = {
            "PREV": "PREV_PAGE",
            "NEXT": "NEXT_PAGE",
            "HOME": "SHOW_HOME",
            "MENU": "SHOW_MENU"
        }
        
        if button in button_events:
            self.handle_event(button_events[button])
    
    def handle_button_long(self, button):
        """处理按钮长按"""
        if button == "HOME":
            self.handle_event("EXIT")
    
    def run(self):
        """主循环"""
        self.logger.info("进入主循环")
        
        # 显示初始屏幕
        self.show_current_screen()
        
        try:
            while self.running:
                # 处理事件
                self.process_events()
                
                # 短暂休眠，降低CPU使用率
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号")
        except Exception as e:
            self.logger.error(f"主循环错误: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("清理资源...")
        
        if self.gpio:
            self.gpio.cleanup()
        
        if self.display:
            self.display.clear()
            self.display.sleep()
        
        self.save_config()
        self.logger.info("程序退出")
    
    def signal_handler(self, signum, frame):
        """信号处理"""
        self.logger.info(f"收到信号: {signum}")
        self.running = False

def main():
    """主函数"""
    reader = EinkReader()
    
    if reader.initialize():
        reader.logger.info("初始化成功，开始运行")
        reader.run()
    else:
        reader.logger.error("初始化失败")
        reader.cleanup()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())