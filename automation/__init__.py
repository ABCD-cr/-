"""
自动化控制模块

此模块负责截图管理和自动化答题流程控制。
"""

from .screenshot_manager import ScreenshotManager
from .automation_controller import AutomationController

__all__ = ['ScreenshotManager', 'AutomationController']
