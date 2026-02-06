"""
截图管理模块

此模块负责屏幕截图操作。
提供屏幕区域截图和坐标验证功能。
"""

from PIL import Image, ImageGrab
from utils.exceptions import ScreenshotException


class ScreenshotManager:
    """
    截图管理器类
    
    提供屏幕截图功能。
    """
    
    @staticmethod
    def validate_region(region: tuple) -> bool:
        """
        验证区域坐标是否有效
        
        Args:
            region: 区域坐标元组 (x1, y1, x2, y2)
            
        Returns:
            是否有效
        """
        # 检查是否为元组或列表
        if not isinstance(region, (tuple, list)):
            return False
        
        # 检查是否有4个元素
        if len(region) != 4:
            return False
        
        # 检查所有元素是否为数字
        try:
            x1, y1, x2, y2 = region
            # 尝试转换为数字以验证类型
            x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        except (TypeError, ValueError):
            return False
        
        # 检查坐标关系：x1 < x2 且 y1 < y2
        if x1 >= x2 or y1 >= y2:
            return False
        
        return True
    
    @staticmethod
    def capture_region(region: tuple) -> Image.Image:
        """
        截取屏幕指定区域
        
        Args:
            region: 区域坐标元组 (x1, y1, x2, y2)
            
        Returns:
            PIL Image 对象
            
        Raises:
            ScreenshotException: 截图失败时抛出
        """
        # 验证区域坐标
        if not ScreenshotManager.validate_region(region):
            raise ScreenshotException(f"无效的区域坐标: {region}")
        
        try:
            # 使用 PIL.ImageGrab 截取屏幕区域
            # ImageGrab.grab() 接受 bbox 参数 (x1, y1, x2, y2)
            screenshot = ImageGrab.grab(bbox=region)
            
            # 验证返回的对象是否为 PIL Image
            if not isinstance(screenshot, Image.Image):
                raise ScreenshotException("截图失败: 返回的对象不是 PIL Image")
            
            return screenshot
            
        except ScreenshotException:
            # 重新抛出我们自己的异常
            raise
        except Exception as e:
            # 捕获其他所有异常并转换为 ScreenshotException
            raise ScreenshotException(f"截图失败: {str(e)}")
