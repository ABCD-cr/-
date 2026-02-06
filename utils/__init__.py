"""
工具函数模块

此模块提供通用的工具函数和自定义异常类。
"""

from .exceptions import (
    AutoAnswerException,
    ConfigException,
    OCRException,
    AIException,
    ScreenshotException,
    AutomationException
)

__all__ = [
    'AutoAnswerException',
    'ConfigException',
    'OCRException',
    'AIException',
    'ScreenshotException',
    'AutomationException'
]
