"""
自定义异常类模块

此模块定义了自动答题系统使用的所有自定义异常类。
所有异常都继承自 AutoAnswerException 基类，便于统一处理。

异常层次结构：
    AutoAnswerException (基类)
    ├── ConfigException (配置相关异常)
    ├── OCRException (OCR 服务异常)
    ├── AIException (AI 服务异常)
    ├── ScreenshotException (截图相关异常)
    └── AutomationException (自动化控制异常)
"""


class AutoAnswerException(Exception):
    """
    自动答题系统基础异常类
    
    所有自定义异常都应该继承此类，以便统一捕获和处理。
    """
    pass


class ConfigException(AutoAnswerException):
    """
    配置相关异常
    
    当配置文件读写失败、配置格式错误或配置验证失败时抛出。
    
    示例：
        - 配置文件写入失败
        - 配置文件格式错误（非 JSON）
        - 必需的配置项缺失
    """
    pass


class OCRException(AutoAnswerException):
    """
    OCR 服务异常
    
    当 OCR API 调用失败、认证失败或图像处理失败时抛出。
    
    示例：
        - 网络连接失败
        - API 认证失败（API Key 无效）
        - OCR 识别失败（API 返回错误）
        - 图像格式不支持
    """
    pass


class AIException(AutoAnswerException):
    """
    AI 服务异常
    
    当 AI API 调用失败、认证失败或模型不支持时抛出。
    
    示例：
        - 网络连接失败
        - API 认证失败（API Key 无效）
        - AI 分析失败（API 返回错误）
        - 不支持的模型名称
    """
    pass


class ScreenshotException(AutoAnswerException):
    """
    截图相关异常
    
    当截图操作失败或区域坐标无效时抛出。
    
    示例：
        - 无效的区域坐标（x1 >= x2 或 y1 >= y2）
        - 截图失败（系统权限不足）
        - 区域超出屏幕范围
    """
    pass


class AutomationException(AutoAnswerException):
    """
    自动化控制异常
    
    当自动化流程执行失败或鼠标控制失败时抛出。
    
    示例：
        - 鼠标点击失败
        - 答题流程中断
        - 依赖服务调用失败
    """
    pass
