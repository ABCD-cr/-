"""
自动答题系统 - 主入口文件

此文件是应用程序的入口点，创建主窗口并启动 GUI 主循环。
"""

import tkinter as tk
from gui.main_window import MainWindow


def main():
    """
    应用程序主函数
    
    创建 Tkinter 根窗口，初始化主窗口，并启动主循环。
    """
    # 创建 Tkinter 根窗口
    root = tk.Tk()
    
    # 创建主窗口实例
    app = MainWindow(root)
    
    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()
