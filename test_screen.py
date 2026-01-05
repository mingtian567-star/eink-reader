#!/usr/bin/env python3
"""
屏幕测试程序
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from hardware.eink_driver import EinkDisplay

def test_screen():
    """测试屏幕功能"""
    print("开始测试屏幕...")
    
    try:
        # 初始化屏幕
        display = EinkDisplay("7in5")
        print(f"屏幕尺寸: {display.width}x{display.height}")
        
        # 测试图案
        print("显示测试图案...")
        display.test_pattern()
        time.sleep(3)
        
        # 清屏
        print("清屏...")
        display.clear()
        
        # 显示文本
        print("显示文本...")
        test_text = """
        屏幕测试
        ========
        
        这是一段测试文本，
        用于验证屏幕显示功能。
        
        如果能看到这段文字，
        说明屏幕工作正常。
        
        测试完成！
        """
        
        display.draw_text(test_text, font_size=20)
        time.sleep(5)
        
        # 清理
        display.clear()
        display.sleep()
        
        print("屏幕测试完成！")
        return True
        
    except Exception as e:
        print(f"屏幕测试失败: {e}")
        return False

if __name__ == "__main__":
    test_screen()