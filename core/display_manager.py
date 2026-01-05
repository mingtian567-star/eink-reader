"""
显示管理器 - 管理屏幕显示和刷新
"""

import time
import logging
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

class DisplayManager:
    """显示管理器"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 屏幕参数
        self.screen_type = config.get("screen_type", "7in5")
        self.width, self.height = self.get_screen_size()
        
        # 字体
        self.font_cache = {}
        self.load_fonts()
        
        # 当前图像
        self.current_image = None
        self.last_image = None
        
        self.logger.info(f"显示管理器初始化: {self.width}x{self.height}")
    
    def get_screen_size(self):
        """获取屏幕尺寸"""
        screen_sizes = {
            "7in5": (800, 480),
            "7in5_V2": (800, 480),
            "7in5_HD": (880, 528),
            "5in83": (648, 480)
        }
        return screen_sizes.get(self.screen_type, (800, 480))
    
    def load_fonts(self):
        """加载字体"""
        font_path = self.config.get("font_path")
        
        if font_path and Path(font_path).exists():
            self.default_font_path = font_path
        else:
            # 尝试系统字体
            system_fonts = [
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
            for font in system_fonts:
                if Path(font).exists():
                    self.default_font_path = font
                    break
            else:
                self.default_font_path = None
        
        self.logger.info(f"使用字体: {self.default_font_path}")
    
    def get_font(self, size):
        """获取字体对象"""
        if size in self.font_cache:
            return self.font_cache[size]
        
        try:
            if self.default_font_path:
                font = ImageFont.truetype(self.default_font_path, size)
            else:
                font = ImageFont.load_default()
            self.font_cache[size] = font
            return font
        except Exception as e:
            self.logger.error(f"加载字体失败: {e}")
            return ImageFont.load_default()
    
    def create_blank_image(self, bg_color=255):
        """创建空白图像"""
        return Image.new('1', (self.width, self.height), bg_color)
    
    def draw_text_box(self, text, x, y, width, height, font_size=None, 
                     line_spacing=None, align="left", valign="top"):
        """在指定区域内绘制文本"""
        if font_size is None:
            font_size = self.config.get("font_size", 20)
        if line_spacing is None:
            line_spacing = self.config.get("line_spacing", 1.5)
        
        # 创建临时图像用于计算
        temp_image = self.create_blank_image(255)
        temp_draw = ImageDraw.Draw(temp_image)
        font = self.get_font(font_size)
        
        # 计算行高
        bbox = temp_draw.textbbox((0, 0), "测试", font=font)
        line_height = int((bbox[3] - bbox[1]) * line_spacing)
        
        # 分割文本为行
        lines = []
        words = text.split(' ')
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= width or not current_line:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # 裁剪超出行数
        max_lines = height // line_height
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            if len(lines) >= max_lines:
                lines[-1] = lines[-1][: -3] + "..."
        
        # 创建实际图像
        image = self.create_blank_image(255)
        draw = ImageDraw.Draw(image)
        
        # 垂直对齐
        if valign == "center":
            y_start = y + (height - len(lines) * line_height) // 2
        elif valign == "bottom":
            y_start = y + height - len(lines) * line_height
        else:  # top
            y_start = y
        
        # 绘制每一行
        for i, line in enumerate(lines):
            line_y = y_start + i * line_height
            
            # 水平对齐
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if align == "center":
                line_x = x + (width - text_width) // 2
            elif align == "right":
                line_x = x + width - text_width
            else:  # left
                line_x = x
            
            draw.text((line_x, line_y), line, font=font, fill=0)
        
        return image, len(lines)
    
    def draw_text_page(self, text, **kwargs):
        """绘制完整文本页"""
        margin = self.config.get("margin", 20)
        width = self.width - 2 * margin
        height = self.height - 2 * margin
        
        # 创建图像
        image = self.create_blank_image(255)
        
        # 绘制主文本
        text_image, lines_used = self.draw_text_box(
            text, margin, margin, width, height, **kwargs
        )
        
        # 合并图像
        image.paste(text_image, (0, 0))
        
        # 添加页码信息（如果有）
        if 'page_info' in kwargs:
            self.draw_page_info(image, kwargs['page_info'])
        
        self.current_image = image
        return image
    
    def draw_page_info(self, image, page_info):
        """绘制页码信息"""
        draw = ImageDraw.Draw(image)
        font = self.get_font(12)
        
        bbox = draw.textbbox((0, 0), page_info, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.width - text_width) // 2
        y = self.height - text_height - 10
        
        draw.text((x, y), page_info, font=font, fill=0)
    
    def save_current_image(self, path):
        """保存当前图像"""
        if self.current_image:
            self.current_image.save(path)
            self.logger.info(f"图像已保存: {path}")
    
    def clear(self):
        """清屏"""
        self.logger.info("清屏")
        self.current_image = None
        self.last_image = None