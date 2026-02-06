"""
图像工具模块

此模块提供图像处理工具函数。
"""

import base64
from io import BytesIO
from PIL import Image


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """
    将 PIL Image 转换为 base64 编码
    
    Args:
        image: PIL Image 对象
        format: 图像格式（默认 PNG）
        
    Returns:
        base64 编码的图像字符串
    """
    # 创建一个字节流缓冲区
    buffered = BytesIO()
    
    # 将图像保存到缓冲区
    image.save(buffered, format=format)
    
    # 获取缓冲区的字节数据
    img_bytes = buffered.getvalue()
    
    # 转换为 base64 编码
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return img_base64
