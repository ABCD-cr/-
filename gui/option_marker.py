"""
选项标记器模块

此模块提供选项位置标记功能。
用户可以依次点击屏幕上的选项位置（A、B、C、D）和下一题按钮位置。
"""

import tkinter as tk


class OptionMarker:
    """
    选项标记器类
    
    提供选项位置标记功能。
    用户可以依次点击屏幕上的选项位置，标记完成后通过回调函数返回位置信息。
    """
    
    def __init__(self, parent: tk.Tk, callback: callable):
        """
        初始化选项标记器
        
        创建一个全屏透明窗口，用户可以依次点击选项位置。
        标记顺序：A -> B -> C -> D -> 下一题按钮
        用户可以按 ESC 键跳过当前选项。
        
        Args:
            parent: 父窗口
            callback: 标记完成回调函数 callback(positions: dict)
                     positions 格式为 {'options': {'A': (x, y), ...}, 'next': (x, y) | None}
        """
        self.callback = callback
        self.positions = {'options': {}, 'next': None}
        self.marking_sequence = ['A', 'B', 'C', 'D', '下一题']
        self.current_index = 0
        self.marks = []  # 存储已标记的图形对象
        
        # 创建全屏透明窗口
        self.top = tk.Toplevel(parent)
        self.top.attributes('-fullscreen', True)
        self.top.attributes('-alpha', 0.3)  # 30% 透明度
        self.top.configure(bg='black')
        
        # 创建 Canvas 用于绘制标记
        self.canvas = tk.Canvas(
            self.top,
            cursor="crosshair",  # 十字光标
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标和键盘事件
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Escape>", self._on_cancel)
        
        # 显示提示文字
        screen_width = self.top.winfo_screenwidth()
        
        self.instruction_text = self.canvas.create_text(
            screen_width // 2,
            50,
            text=f"请点击选项 {self.marking_sequence[0]} 的位置",
            fill="white",
            font=("Arial", 20)
        )
        
        self.hint_text = self.canvas.create_text(
            screen_width // 2,
            100,
            text="按 ESC 跳过当前选项 | 标记完成后自动关闭",
            fill="yellow",
            font=("Arial", 14)
        )
    
    def _on_click(self, event) -> None:
        """
        鼠标点击事件处理（内部方法）
        
        记录当前选项的位置，在屏幕上绘制标记，并移动到下一个选项。
        如果所有选项都已标记，则完成标记流程。
        
        Args:
            event: 鼠标事件对象，包含 x, y 坐标
        """
        x, y = event.x, event.y
        current_option = self.marking_sequence[self.current_index]
        
        # 保存位置
        if current_option == '下一题':
            self.positions['next'] = (x, y)
        else:
            self.positions['options'][current_option] = (x, y)
        
        # 在屏幕上绘制标记（红色圆圈 + 白色文字）
        mark_circle = self.canvas.create_oval(
            x - 10, y - 10,
            x + 10, y + 10,
            fill='red',
            outline='white',
            width=2
        )
        mark_label = self.canvas.create_text(
            x, y,
            text=current_option,
            fill='white',
            font=("Arial", 12, "bold")
        )
        self.marks.append((mark_circle, mark_label))
        
        # 移动到下一个选项
        self.current_index += 1
        
        if self.current_index < len(self.marking_sequence):
            # 更新提示文字
            next_option = self.marking_sequence[self.current_index]
            self.canvas.itemconfig(
                self.instruction_text,
                text=f"请点击选项 {next_option} 的位置"
            )
        else:
            # 所有选项已标记，完成流程
            self._finish()
    
    def _on_cancel(self, event) -> None:
        """
        取消事件处理（内部方法）
        
        跳过当前选项，移动到下一个选项。
        如果所有选项都已处理（标记或跳过），则完成标记流程。
        
        Args:
            event: 键盘事件对象
        """
        # 跳过当前选项，移动到下一个
        self.current_index += 1
        
        if self.current_index < len(self.marking_sequence):
            # 更新提示文字
            next_option = self.marking_sequence[self.current_index]
            self.canvas.itemconfig(
                self.instruction_text,
                text=f"请点击选项 {next_option} 的位置"
            )
        else:
            # 所有选项已处理，完成流程
            self._finish()
    
    def _finish(self) -> None:
        """
        完成标记（内部方法）
        
        关闭标记窗口，并调用回调函数返回标记结果。
        """
        # 关闭窗口
        self.top.destroy()
        
        # 调用回调函数，返回标记结果
        self.callback(self.positions)
