"""
区域选择器模块

此模块提供全屏透明窗口用于框选屏幕区域。
"""

import tkinter as tk


class RegionSelector:
    """
    区域选择器类
    
    提供全屏透明窗口用于框选区域。
    用户可以通过拖动鼠标来选择屏幕上的一个矩形区域。
    """
    
    def __init__(self, parent: tk.Tk, callback: callable):
        """
        初始化区域选择器
        
        创建一个全屏透明窗口，用户可以在其中拖动鼠标框选区域。
        选择完成后，通过回调函数返回区域坐标 (x1, y1, x2, y2)。
        
        Args:
            parent: 父窗口
            callback: 选择完成回调函数 callback(region: tuple)
                     region 格式为 (x1, y1, x2, y2)
        """
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # 创建全屏透明窗口
        self.top = tk.Toplevel(parent)
        self.top.attributes('-fullscreen', True)
        self.top.attributes('-alpha', 0.3)  # 30% 透明度
        self.top.configure(bg='black')
        
        # 创建 Canvas 用于绘制选择框
        self.canvas = tk.Canvas(
            self.top, 
            cursor="cross",  # 十字光标
            bg='black', 
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        
        # 显示提示文字
        self.canvas.create_text(
            self.top.winfo_screenwidth() // 2,
            50,
            text="拖动鼠标框选答题区域",
            fill="white",
            font=("Arial", 20)
        )
    
    def _on_press(self, event) -> None:
        """
        鼠标按下事件处理（内部方法）
        
        记录起始坐标并创建初始矩形。
        
        Args:
            event: 鼠标事件对象，包含 x, y 坐标
        """
        self.start_x = event.x
        self.start_y = event.y
        
        # 如果已有矩形，先删除
        if self.rect:
            self.canvas.delete(self.rect)
        
        # 创建新矩形（初始大小为 0）
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, 
            self.start_x, self.start_y,
            outline='red', 
            width=2
        )
    
    def _on_drag(self, event) -> None:
        """
        鼠标拖动事件处理（内部方法）
        
        更新矩形的大小以跟随鼠标移动。
        
        Args:
            event: 鼠标事件对象，包含当前 x, y 坐标
        """
        if self.rect:
            # 更新矩形坐标
            self.canvas.coords(
                self.rect, 
                self.start_x, self.start_y, 
                event.x, event.y
            )
    
    def _on_release(self, event) -> None:
        """
        鼠标释放事件处理（内部方法）
        
        计算最终的区域坐标，关闭窗口，并调用回调函数。
        确保返回的坐标满足 x1 < x2 且 y1 < y2。
        
        Args:
            event: 鼠标事件对象，包含结束 x, y 坐标
        """
        end_x = event.x
        end_y = event.y
        
        # 计算规范化的坐标（确保 x1 < x2, y1 < y2）
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # 关闭窗口
        self.top.destroy()
        
        # 调用回调函数，返回区域坐标
        self.callback((x1, y1, x2, y2))
