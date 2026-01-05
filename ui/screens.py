"""
屏幕界面 - 各种界面屏幕的实现
"""

import time
import logging
from typing import Optional, Dict, Any, Tuple
from PIL import Image, ImageDraw

class BaseScreen:
    """基础屏幕类"""
    
    def __init__(self, display, book_manager, config):
        self.display = display
        self.book_manager = book_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 屏幕参数
        self.width = display.width
        self.height = display.height
        
        # 状态
        self.selected_index = 0
        self.need_refresh = True
    
    def show(self):
        """显示屏幕"""
        if self.need_refresh:
            self.render()
            self.need_refresh = False
    
    def render(self):
        """渲染屏幕内容（子类实现）"""
        raise NotImplementedError
    
    def handle_event(self, event_type: str, event_data: Any = None) -> Optional[Tuple[str, Any]]:
        """处理事件（子类实现）"""
        raise NotImplementedError
    
    def draw_title_bar(self, image: Image.Image, title: str):
        """绘制标题栏"""
        draw = ImageDraw.Draw(image)
        
        # 绘制标题背景
        draw.rectangle([0, 0, self.width-1, 40], fill=0)
        
        # 绘制标题文字
        try:
            from core.display_manager import DisplayManager
            dm = DisplayManager(self.config)
            font = dm.get_font(18)
        except:
            font = None
        
        draw.text((20, 10), title, font=font, fill=255)
    
    def draw_status_bar(self, image: Image.Image, status: str = ""):
        """绘制状态栏"""
        draw = ImageDraw.Draw(image)
        
        # 绘制状态栏背景
        draw.rectangle([0, self.height-30, self.width-1, self.height-1], fill=0)
        
        # 绘制状态文字
        try:
            from core.display_manager import DisplayManager
            dm = DisplayManager(self.config)
            font = dm.get_font(12)
        except:
            font = None
        
        if status:
            draw.text((20, self.height-25), status, font=font, fill=255)
        
        # 绘制时间
        current_time = time.strftime("%H:%M")
        time_width = draw.textlength(current_time, font=font) if font else 50
        draw.text((self.width - time_width - 20, self.height-25), 
                 current_time, font=font, fill=255)
    
    def draw_selection_indicator(self, image: Image.Image, y: int, height: int):
        """绘制选择指示器"""
        draw = ImageDraw.Draw(image)
        draw.rectangle([5, y, self.width-5, y+height-5], outline=0, width=2)

class HomeScreen(BaseScreen):
    """主屏幕"""
    
    def __init__(self, display, book_manager, config):
        super().__init__(display, book_manager, config)
        self.books = []
        self.items_per_page = 6
        self.current_page = 0
    
    def render(self):
        """渲染主屏幕"""
        from core.display_manager import DisplayManager
        
        dm = DisplayManager(self.config)
        dm.width = self.width
        dm.height = self.height
        
        # 获取书籍列表
        self.books = self.book_manager.list_books()
        total_pages = (len(self.books) + self.items_per_page - 1) // self.items_per_page
        
        # 创建页面内容
        lines = ["📚 我的书架", ""]
        
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.books))
        
        for i in range(start_idx, end_idx):
            book = self.books[i]
            prefix = "▶ " if i == self.selected_index else "  "
            # 截断长文件名
            name = book['name']
            if len(name) > 20:
                name = name[:17] + "..."
            lines.append(f"{prefix}{name} ({book['size']})")
        
        lines.append("")
        lines.append(f"第 {self.current_page + 1}/{total_pages} 页")
        lines.append("")
        lines.append("使用 ↑↓ 选择，←→ 翻页，ENTER 打开")
        
        content = "\n".join(lines)
        page_info = f"共 {len(self.books)} 本书"
        
        image = dm.draw_text_page(content, page_info=page_info)
        self.display.display(image)
    
    def handle_event(self, event_type: str, event_data: Any = None):
        """处理主屏幕事件"""
        if event_type == "NEXT_PAGE":
            total_pages = (len(self.books) + self.items_per_page - 1) // self.items_per_page
            if self.current_page < total_pages - 1:
                self.current_page += 1
                self.need_refresh = True
                return ("REFRESH", None)
        
        elif event_type == "PREV_PAGE":
            if self.current_page > 0:
                self.current_page -= 1
                self.need_refresh = True
                return ("REFRESH", None)
        
        elif event_type == "UP":
            if self.selected_index > 0:
                self.selected_index -= 1
                # 如果超出当前页，翻到上一页
                if self.selected_index < self.current_page * self.items_per_page:
                    self.current_page = max(0, self.current_page - 1)
                self.need_refresh = True
                return ("REFRESH", None)
        
        elif event_type == "DOWN":
            if self.selected_index < len(self.books) - 1:
                self.selected_index += 1
                # 如果超出当前页，翻到下一页
                items_per_page = self.items_per_page
                if self.selected_index >= (self.current_page + 1) * items_per_page:
                    self.current_page += 1
                self.need_refresh = True
                return ("REFRESH", None)
        
        elif event_type == "SELECT":
            if 0 <= self.selected_index < len(self.books):
                book = self.books[self.selected_index]
                return ("LOAD_BOOK", {"path": book['path']})
        
        elif event_type == "SHOW_MENU":
            return ("SHOW_MENU", None)
        
        return None

class ReadingScreen(BaseScreen):
    """阅读屏幕"""
    
    def render(self):
        """渲染阅读屏幕"""
        from core.display_manager import DisplayManager
        
        dm = DisplayManager(self.config)
        dm.width = self.width
        dm.height = self.height
        
        # 获取当前页内容
        if self.book_manager.current_book_path:
            book_name = self.book_manager.current_book_path.name
            page_content = self.book_manager.get_current_page()
            current_page = self.book_manager.current_page + 1
            total_pages = self.book_manager.total_pages
            
            if page_content:
                # 添加书籍名和页码
                header = f"{book_name}\n"
                content = header + page_content
                page_info = f"第 {current_page}/{total_pages} 页"
                
                image = dm.draw_text_page(content, page_info=page_info)
                self.display.display(image)
                return
        
        # 没有书籍时的显示
        content = "暂无打开的书籍\n\n按 HOME 键返回主屏幕"
        image = dm.draw_text_page(content)
        self.display.display(image)
    
    def handle_event(self, event_type: str, event_data: Any = None):
        """处理阅读屏幕事件"""
        if event_type == "NEXT_PAGE":
            if self.book_manager.next_page():
                self.config["current_page"] = self.book_manager.current_page
                self.need_refresh = True
                return ("SAVE_CONFIG", None)
        
        elif event_type == "PREV_PAGE":
            if self.book_manager.prev_page():
                self.config["current_page"] = self.book_manager.current_page
                self.need_refresh = True
                return ("SAVE_CONFIG", None)
        
        elif event_type == "SHOW_HOME":
            return ("SHOW_HOME", None)
        
        elif event_type == "SHOW_MENU":
            return ("SHOW_MENU", None)
        
        elif event_type == "GOTO_PAGE":
            if isinstance(event_data, int):
                if self.book_manager.go_to_page(event_data):
                    self.config["current_page"] = self.book_manager.current_page
                    self.need_refresh = True
                    return ("SAVE_CONFIG", None)
        
        return None

class MenuScreen(BaseScreen):
    """菜单屏幕"""
    
    def __init__(self, display, book_manager, config):
        super().__init__(display, book_manager, config)
        self.menu_items = [
            ("返回", "BACK"),
            ("设置", "SETTINGS"),
            ("书签", "BOOKMARKS"),
            ("Wi-Fi传书", "WIFI_UPLOAD"),
            ("关于", "ABOUT"),
            ("关机", "SHUTDOWN")
        ]
        self.selected_index = 0
    
    def render(self):
        """渲染菜单屏幕"""
        from core.display_manager import DisplayManager
        
        dm = DisplayManager(self.config)
        dm.width = self.width
        dm.height = self.height
        
        # 创建菜单内容
        lines = ["⚙️ 菜单", ""]
        
        for i, (text, _) in enumerate(self.menu_items):
            prefix = "▶ " if i == self.selected_index else "  "
            lines.append(f"{prefix}{text}")
        
        lines.append("")
        lines.append("使用 ↑↓ 选择，ENTER 确认，HOME 返回")
        
        content = "\n".join(lines)
        image = dm.draw_text_page(content)
        self.display.display(image)
    
    def handle_event(self, event_type: str, event_data: Any = None):
        """处理菜单事件"""
        if event_type == "UP":
            if self.selected_index > 0:
                self.selected_index -= 1
                self.need_refresh = True
                return ("REFRESH", None)
        
        elif event_type == "DOWN":
            if self.selected_index < len(self.menu_items) - 1:
                self.selected_index += 1
                self.need_refresh = True
                return ("REFRESH", None)
        
        elif event_type == "SELECT":
            _, action = self.menu_items[self.selected_index]
            
            if action == "BACK":
                if self.book_manager.current_book_path:
                    return ("SHOW_READING", None)
                else:
                    return ("SHOW_HOME", None)
            
            elif action == "SETTINGS":
                return ("SHOW_SETTINGS", None)
            
            elif action == "BOOKMARKS":
                return ("SHOW_BOOKMARKS", None)
            
            elif action == "WIFI_UPLOAD":
                return ("START_WIFI_UPLOAD", None)
            
            elif action == "ABOUT":
                return ("SHOW_ABOUT", None)
            
            elif action == "SHUTDOWN":
                return ("SHUTDOWN_CONFIRM", None)
        
        elif event_type == "SHOW_HOME":
            return ("SHOW_HOME", None)
        
        return None