"""
GPIO控制器 - 管理物理按键
"""

import time
import threading
import logging
from collections import deque
from typing import Optional, List, Tuple

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    logging.warning("RPi.GPIO未找到，使用模拟模式")

class GPIOController:
    """GPIO控制器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # GPIO引脚定义 (BCM编号)
        self.button_pins = {
            'PREV': 5,    # 上一页
            'NEXT': 6,    # 下一页
            'HOME': 13,   # 主页
            'MENU': 19,   # 菜单
        }
        
        # 按键状态
        self.button_states = {name: True for name in self.button_pins}
        self.last_states = {name: True for name in self.button_pins}
        self.press_times = {name: 0 for name in self.button_pins}
        
        # 事件队列
        self.event_queue = deque()
        
        # 运行状态
        self.running = False
        self.thread = None
        
        # 初始化GPIO
        if HAS_GPIO:
            self.setup_gpio()
        else:
            self.logger.info("使用模拟GPIO模式")
    
    def setup_gpio(self):
        """设置GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # 设置按钮为输入，启用上拉电阻
            for pin in self.button_pins.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            self.logger.info("GPIO初始化完成")
            
        except Exception as e:
            self.logger.error(f"GPIO初始化失败: {e}")
            HAS_GPIO = False
    
    def start_monitoring(self):
        """开始监控按键"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_buttons)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("按键监控启动")
    
    def _monitor_buttons(self):
        """监控按键状态"""
        LONG_PRESS_TIME = 1.0  # 长按时间阈值
        
        while self.running:
            current_time = time.time()
            
            for name, pin in self.button_pins.items():
                if HAS_GPIO:
                    current_state = GPIO.input(pin)
                else:
                    # 模拟模式，始终为释放状态
                    current_state = True
                
                # 检测状态变化
                if current_state != self.last_states[name]:
                    if current_state == False:  # 按下
                        self.press_times[name] = current_time
                        self.event_queue.append(('BUTTON_DOWN', name))
                    else:  # 释放
                        press_duration = current_time - self.press_times[name]
                        self.event_queue.append(('BUTTON_UP', name))
                        
                        if press_duration < LONG_PRESS_TIME:
                            self.event_queue.append(('BUTTON_CLICK', name))
                        else:
                            self.event_queue.append(('BUTTON_LONG_PRESS', (name, press_duration)))
                    
                    self.last_states[name] = current_state
                else:
                    # 检查长按
                    if current_state == False:  # 按键保持按下
                        press_duration = current_time - self.press_times[name]
                        if press_duration >= LONG_PRESS_TIME and press_duration < LONG_PRESS_TIME + 0.1:
                            # 触发长按事件
                            self.event_queue.append(('BUTTON_LONG_HOLD', (name, press_duration)))
            
            time.sleep(0.01)  # 10ms轮询
    
    def get_events(self) -> List[Tuple[str, any]]:
        """获取所有待处理事件"""
        events = []
        while self.event_queue:
            events.append(self.event_queue.popleft())
        return events
    
    def wait_for_event(self, timeout: float = None) -> Optional[Tuple[str, any]]:
        """等待事件"""
        start_time = time.time()
        while self.running:
            if self.event_queue:
                return self.event_queue.popleft()
            
            if timeout and (time.time() - start_time) > timeout:
                return None
            
            time.sleep(0.01)
        return None
    
    def cleanup(self):
        """清理资源"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        
        if HAS_GPIO:
            GPIO.cleanup()
        
        self.logger.info("GPIO控制器已清理")