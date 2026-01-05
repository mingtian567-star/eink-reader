"""
电子墨水屏驱动
"""

import sys
import time
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 尝试导入真实驱动
try:
    # 添加屏幕驱动路径
    driver_path = Path.home() / "e-Paper" / "RaspberryPi_JetsonNano" / "python"
    if driver_path.exists():
        sys.path.append(str(driver_path))
    
    from waveshare_epd import epd7in5, epd7in5_V2
    HAS_REAL_DRIVER = True
except ImportError:
    HAS_REAL_DRIVER = False
    logging.warning("未找到Waveshare驱动，使用模拟模式")

class EinkDisplay:
    """电子墨水屏显示控制器"""
    
    def __init__(self, screen_type="7in5"):
        self.screen_type = screen_type
        self.logger = logging.getLogger(__name__)
        
        # 屏幕参数
        self.epd = None
        self.width = 800
        self.height = 480
        
        # 初始化屏幕
        self.init_display()
        
        self.logger.info(f"屏幕初始化: {self.width}x{self.height}")
    
    def init_display(self):
        """初始化显示设备"""
        if HAS_REAL_DRIVER:
            try:
                if self.screen_type == "7in5":
                    self.epd = epd7in5.EPD()
                    self.width = epd7in5.EPD_WIDTH
                    self.height = epd7in5.EPD_HEIGHT
                elif self.screen_type == "7in5_V2":
                    self.epd = epd7in5_V2.EPD()
                    self.width = epd7in5_V2.EPD_WIDTH
                    self.height = epd7in5_V2.EPD_HEIGHT
                
                self.epd.init()
                self.logger.info("真实屏幕初始化成功")
                return
                
            except Exception as e:
                self.logger.error(f"真实屏幕初始化失败: {e}")
                HAS_REAL_DRIVER = False
        
        # 模拟模式
        self.logger.info("使用模拟屏幕模式")
        self.epd = MockEPD(self.width, self.height)
    
    def clear(self):
        """清屏"""
        if self.epd:
            self.epd.Clear()
    
    def sleep(self):
        """进入睡眠模式"""
        if self.epd and hasattr(self.epd, 'sleep'):
            self.epd.sleep()
    
    def display(self, image: Image.Image, partial: bool = False):
        """显示图像"""
        if not self.epd or not image:
            return False
        
        try:
            if partial and hasattr(self.epd, 'displayPartial'):
                self.epd.displayPartial(self.epd.getbuffer(image))
            else:
                self.epd.display(self.epd.getbuffer(image))
            return True
        except Exception as e:
            self.logger.error(f"显示图像失败: {e}")
            return False
    
    def update(self):
        """更新显示（如果有缓存图像）"""
        if hasattr(self, 'current_image'):
            return self.display(self.current_image)
        return False
    
    def draw_text(self, text: str, font_size: int = 20, **kwargs):
        """绘制文本并更新显示"""
        from core.display_manager import DisplayManager
        
        # 创建临时配置
        config = {
            "screen_type": self.screen_type,
            "font_size": font_size,
            "margin": kwargs.get('margin', 20)
        }
        
        dm = DisplayManager(config)
        dm.width = self.width
        dm.height = self.height
        
        image = dm.draw_text_page(text, **kwargs)
        self.current_image = image
        
        return self.display(image)
    
    def show_error(self, message: str):
        """显示错误信息"""
        error_text = f"错误\n====\n\n{message}\n\n按任意键继续..."
        self.draw_text(error_text, font_size=16)
    
    def show_message(self, message: str):
        """显示普通消息"""
        self.draw_text(message, font_size=18)
    
    def test_pattern(self):
        """显示测试图案"""
        image = Image.new('1', (self.width, self.height), 255)
        draw = ImageDraw.Draw(image)
        
        # 画边框
        draw.rectangle([0, 0, self.width-1, self.height-1], outline=0)
        
        # 画网格
        grid_size = 50
        for x in range(0, self.width, grid_size):
            draw.line([(x, 0), (x, self.height)], fill=0, width=1)
        for y in range(0, self.height, grid_size):
            draw.line([(0, y), (self.width, y)], fill=0, width=1)
        
        # 显示文字
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        text = f"测试图案\n{self.width}x{self.height}"
        draw.text((20, 20), text, font=font, fill=0)
        
        self.display(image)
        return image

class MockEPD:
    """模拟EPD设备"""
    
    def __init__(self, width=800, height=480):
        self.width = width
        self.height = height
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"创建模拟EPD: {width}x{height}")
    
    def init(self):
        self.logger.info("模拟EPD初始化")
    
    def Clear(self):
        self.logger.info("模拟清屏")
    
    def sleep(self):
        self.logger.info("模拟进入睡眠")
    
    def display(self, buffer):
        self.logger.info("模拟显示图像")
        return True
    
    def displayPartial(self, buffer):
        self.logger.info("模拟局部刷新")
        return True
    
    def getbuffer(self, image):
        return image