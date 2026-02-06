"""
主窗口模块

此模块提供主窗口界面，协调用户交互。
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime

from config.config_manager import ConfigManager
from services.ocr_service import OCRService
from services.ai_service import AIService
from automation.screenshot_manager import ScreenshotManager
from automation.automation_controller import AutomationController
from gui.region_selector import RegionSelector
from gui.option_marker import OptionMarker


class MainWindow:
    """
    主窗口类
    
    提供用户界面和交互逻辑。
    协调各个服务模块，实现完整的自动答题功能。
    """
    
    def __init__(self, root: tk.Tk):
        """
        初始化主窗口
        
        创建所有依赖服务实例，初始化状态变量，并设置用户界面。
        
        Args:
            root: Tkinter 根窗口
        """
        self.root = root
        self.root.title("🤖 自动答题系统")
        self.root.geometry("1000x850")
        
        # 设置窗口背景色
        try:
            self.root.configure(bg='#f0f2f5')
        except:
            pass
        
        # 配置现代化样式
        self._setup_styles()
        
        # 创建依赖服务实例
        self.config_manager = ConfigManager()
        self.ocr_service = OCRService(self.config_manager)
        self.ai_service = AIService(self.config_manager)
        self.screenshot_manager = ScreenshotManager()
        self.automation_controller = AutomationController(
            self.screenshot_manager,
            self.ocr_service,
            self.ai_service
        )
        
        # 初始化状态变量
        self.region = None  # 截图区域 (x1, y1, x2, y2)
        self.option_positions = None  # 选项位置 {'options': {...}, 'next': ...}
        self.is_running = False  # 是否正在答题
        
        # API Key 编辑状态
        self.api_key_editing = {
            'deepseek': False,
            'baidu_basic_api': False,
            'baidu_basic_secret': False,
            'baidu_accurate_api': False,
            'baidu_accurate_secret': False
        }
        
        # 设置用户界面
        self._setup_ui()
        
        # 加载配置并更新界面
        self._load_config_to_ui()
    
    def _setup_styles(self) -> None:
        """
        配置现代化UI样式（内部方法）
        """
        style = ttk.Style()
        
        # 设置主题
        try:
            style.theme_use('clam')
        except:
            pass
        
        # 配置卡片样式的LabelFrame
        style.configure(
            'Card.TLabelframe',
            background='#ffffff',
            borderwidth=1,
            relief='solid'
        )
        style.configure(
            'Card.TLabelframe.Label',
            background='#ffffff',
            foreground='#2c3e50',
            font=('Microsoft YaHei UI', 10, 'bold')
        )
        
        # 配置标题样式
        style.configure(
            'Title.TLabel',
            background='#f0f2f5',
            foreground='#1a1a1a',
            font=('Microsoft YaHei UI', 16, 'bold')
        )
        
        # 配置副标题样式
        style.configure(
            'Subtitle.TLabel',
            background='#ffffff',
            foreground='#34495e',
            font=('Microsoft YaHei UI', 9)
        )
        
        # 配置按钮样式
        style.configure(
            'TButton',
            padding=6,
            relief='flat',
            background='#3498db',
            foreground='#2c3e50'
        )
        
        # 配置强调按钮样式
        style.configure(
            'Accent.TButton',
            padding=10,
            font=('Microsoft YaHei UI', 11, 'bold')
        )
        
        # 配置单选按钮样式
        style.configure(
            'TRadiobutton',
            background='#ffffff',
            foreground='#2c3e50',
            font=('Microsoft YaHei UI', 9)
        )
        # 去掉焦点虚线框
        style.map('TRadiobutton',
            focuscolor=[('focus', '#ffffff')],
            background=[('active', '#ffffff')]
        )
        
        # 配置复选框样式
        style.configure(
            'TCheckbutton',
            background='#ffffff',
            foreground='#2c3e50',
            font=('Microsoft YaHei UI', 9)
        )
        # 去掉焦点虚线框
        style.map('TCheckbutton',
            focuscolor=[('focus', '#ffffff')],
            background=[('active', '#ffffff')]
        )
        
        # 配置Frame样式
        style.configure(
            'TFrame',
            background='#ffffff'
        )
        
        # 配置Entry样式
        style.configure(
            'TEntry',
            fieldbackground='#ffffff',
            borderwidth=1
        )
    
    def _setup_ui(self) -> None:
        """
        设置用户界面（内部方法）
        
        创建完整的用户界面，包括：
        - 答题模式选择
        - DeepSeek API Key 输入区域
        - 百度 OCR API Key 输入区域
        - 模型选择区域
        - 截图区域设置
        - 答题设置
        - 开始/停止按钮
        - 日志显示区域
        """
        # 创建主框架（带内边距）- 直接放在root上，不使用Canvas
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill="both", expand=True)
        main_frame.configure(style='TFrame')
        
        # 设置主框架背景色
        try:
            main_frame.configure(style='Main.TFrame')
            style = ttk.Style()
            style.configure('Main.TFrame', background='#f0f2f5')
        except:
            pass
        
        # 配置网格权重 - 确保两列平分空间
        main_frame.columnconfigure(0, weight=1, uniform="cols")
        main_frame.columnconfigure(1, weight=1, uniform="cols")
        
        row = 0
        
        # ===== 标题（跨两列） =====
        title_label = tk.Label(
            main_frame, 
            text="🤖 自动答题系统", 
            font=('Microsoft YaHei UI', 16, 'bold'),
            foreground='#1a1a1a',
            background='#f0f2f5'
        )
        title_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 12))
        row += 1
        
        # ===== 左列开始 =====
        left_col = 0
        left_row = row
        
        # ===== 答题模式选择区域（左列） =====
        mode_card = ttk.LabelFrame(
            main_frame, 
            text="  📋 答题模式  ",
            padding="10",
            style='Card.TLabelframe'
        )
        mode_card.grid(row=left_row, column=left_col, sticky=(tk.W, tk.E), pady=(0, 10), padx=(0, 5))
        mode_card.columnconfigure(0, weight=1)
        left_row += 1
        
        self.answering_mode_var = tk.StringVar(value="fixed")
        mode_frame = ttk.Frame(mode_card, style='TFrame')
        mode_frame.grid(row=0, column=0, sticky=tk.W, padx=3, pady=3)
        
        ttk.Radiobutton(
            mode_frame,
            text="🎯 固定答题",
            variable=self.answering_mode_var,
            value="fixed",
            command=self._on_answering_mode_changed,
            style='TRadiobutton'
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Radiobutton(
            mode_frame,
            text="📜 滚动答题",
            variable=self.answering_mode_var,
            value="scroll",
            command=self._on_answering_mode_changed,
            style='TRadiobutton'
        ).pack(side=tk.LEFT)
        
        # ===== API 配置卡片（左列） =====
        api_card = ttk.LabelFrame(
            main_frame,
            text="  🔑 API 配置  ",
            padding="10",
            style='Card.TLabelframe'
        )
        api_card.grid(row=left_row, column=left_col, sticky=(tk.W, tk.E, tk.N), pady=(0, 10), padx=(0, 5), rowspan=10)
        api_card.columnconfigure(0, weight=1)
        left_row += 1
        
        api_row = 0
        
        # DeepSeek API Key
        ttk.Label(
            api_card, 
            text="DeepSeek API Key",
            style='Subtitle.TLabel',
            font=('Microsoft YaHei UI', 8)
        ).grid(row=api_row, column=0, sticky=tk.W, pady=(0, 5))
        api_row += 1
        
        # DeepSeek API Key 输入框架
        deepseek_frame = ttk.Frame(api_card, style='TFrame')
        deepseek_frame.grid(row=api_row, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        deepseek_frame.columnconfigure(0, weight=1)
        api_row += 1
        
        self.deepseek_api_key_var = tk.StringVar()
        self.deepseek_api_key_entry = ttk.Entry(
            deepseek_frame, 
            textvariable=self.deepseek_api_key_var,
            show="",
            state="normal",
            font=('Consolas', 9)
        )
        self.deepseek_api_key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 8))
        
        self.deepseek_edit_btn = ttk.Button(
            deepseek_frame,
            text="编辑",
            command=lambda: self._toggle_edit_api_key('deepseek'),
            width=10,
            style='TButton'
        )
        self.deepseek_edit_btn.grid(row=0, column=1)
        
        # 百度 OCR 配置标题
        ttk.Label(
            api_card,
            text="百度 OCR",
            style='Subtitle.TLabel',
            font=('Microsoft YaHei UI', 8, 'bold')
        ).grid(row=api_row, column=0, sticky=tk.W, pady=(5, 5))
        api_row += 1
        
        # OCR 模式选择
        self.ocr_mode_var = tk.StringVar(value="general_basic")
        self.ocr_mode_frame = ttk.Frame(api_card, style='TFrame')
        self.ocr_mode_frame.grid(row=api_row, column=0, sticky=tk.W, pady=(0, 8))
        api_row += 1
        
        self.ocr_basic_radio = ttk.Radiobutton(
            self.ocr_mode_frame,
            text="基础版",
            variable=self.ocr_mode_var,
            value="general_basic",
            command=self._on_ocr_mode_changed,
            style='TRadiobutton'
        )
        self.ocr_basic_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        self.ocr_accurate_radio = ttk.Radiobutton(
            self.ocr_mode_frame,
            text="位置信息版",
            variable=self.ocr_mode_var,
            value="accurate_basic",
            command=self._on_ocr_mode_changed,
            style='TRadiobutton'
        )
        self.ocr_accurate_radio.pack(side=tk.LEFT)
        
        # 基础模式 API Key
        ttk.Label(
            api_card,
            text="基础版 API Key",
            font=('Microsoft YaHei UI', 8)
        ).grid(row=api_row, column=0, sticky=tk.W, pady=(0, 3))
        api_row += 1
        
        baidu_basic_api_frame = ttk.Frame(api_card, style='TFrame')
        baidu_basic_api_frame.grid(row=api_row, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        baidu_basic_api_frame.columnconfigure(0, weight=1)
        api_row += 1
        
        self.baidu_basic_api_key_var = tk.StringVar()
        self.baidu_basic_api_key_entry = ttk.Entry(
            baidu_basic_api_frame,
            textvariable=self.baidu_basic_api_key_var,
            show="",
            state="normal",
            font=('Consolas', 9)
        )
        self.baidu_basic_api_key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 8))
        
        self.baidu_basic_api_edit_btn = ttk.Button(
            baidu_basic_api_frame,
            text="编辑",
            command=lambda: self._toggle_edit_api_key('baidu_basic_api'),
            width=10,
            style='TButton'
        )
        self.baidu_basic_api_edit_btn.grid(row=0, column=1)
        
        # 基础模式 Secret Key
        ttk.Label(
            api_card,
            text="基础版 Secret Key",
            font=('Microsoft YaHei UI', 8)
        ).grid(row=api_row, column=0, sticky=tk.W, pady=(0, 3))
        api_row += 1
        
        baidu_basic_secret_frame = ttk.Frame(api_card, style='TFrame')
        baidu_basic_secret_frame.grid(row=api_row, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        baidu_basic_secret_frame.columnconfigure(0, weight=1)
        api_row += 1
        
        self.baidu_basic_secret_key_var = tk.StringVar()
        self.baidu_basic_secret_key_entry = ttk.Entry(
            baidu_basic_secret_frame,
            textvariable=self.baidu_basic_secret_key_var,
            show="",
            state="normal",
            font=('Consolas', 9)
        )
        self.baidu_basic_secret_key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 8))
        
        self.baidu_basic_secret_edit_btn = ttk.Button(
            baidu_basic_secret_frame,
            text="编辑",
            command=lambda: self._toggle_edit_api_key('baidu_basic_secret'),
            width=10,
            style='TButton'
        )
        self.baidu_basic_secret_edit_btn.grid(row=0, column=1)
        
        # 高精度模式 API Key
        ttk.Label(
            api_card,
            text="位置信息版 API Key",
            font=('Microsoft YaHei UI', 8)
        ).grid(row=api_row, column=0, sticky=tk.W, pady=(0, 3))
        api_row += 1
        
        baidu_accurate_api_frame = ttk.Frame(api_card, style='TFrame')
        baidu_accurate_api_frame.grid(row=api_row, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        baidu_accurate_api_frame.columnconfigure(0, weight=1)
        api_row += 1
        
        self.baidu_accurate_api_key_var = tk.StringVar()
        self.baidu_accurate_api_key_entry = ttk.Entry(
            baidu_accurate_api_frame,
            textvariable=self.baidu_accurate_api_key_var,
            show="",
            state="normal",
            font=('Consolas', 9)
        )
        self.baidu_accurate_api_key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 8))
        
        self.baidu_accurate_api_edit_btn = ttk.Button(
            baidu_accurate_api_frame,
            text="编辑",
            command=lambda: self._toggle_edit_api_key('baidu_accurate_api'),
            width=10,
            style='TButton'
        )
        self.baidu_accurate_api_edit_btn.grid(row=0, column=1)
        
        # 高精度模式 Secret Key
        ttk.Label(
            api_card,
            text="位置信息版 Secret Key",
            font=('Microsoft YaHei UI', 8)
        ).grid(row=api_row, column=0, sticky=tk.W, pady=(0, 3))
        api_row += 1
        
        baidu_accurate_secret_frame = ttk.Frame(api_card, style='TFrame')
        baidu_accurate_secret_frame.grid(row=api_row, column=0, sticky=(tk.W, tk.E), pady=(0, 3))
        baidu_accurate_secret_frame.columnconfigure(0, weight=1)
        api_row += 1
        
        self.baidu_accurate_secret_key_var = tk.StringVar()
        self.baidu_accurate_secret_key_entry = ttk.Entry(
            baidu_accurate_secret_frame,
            textvariable=self.baidu_accurate_secret_key_var,
            show="",
            state="normal",
            font=('Consolas', 9)
        )
        self.baidu_accurate_secret_key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 8))
        
        self.baidu_accurate_secret_edit_btn = ttk.Button(
            baidu_accurate_secret_frame,
            text="编辑",
            command=lambda: self._toggle_edit_api_key('baidu_accurate_secret'),
            width=10,
            style='TButton'
        )
        self.baidu_accurate_secret_edit_btn.grid(row=0, column=1)
        
        # ===== 右列开始 =====
        right_col = 1
        right_row = row
        
        # ===== AI 模型选择卡片（右列） =====
        model_card = ttk.LabelFrame(
            main_frame,
            text="  🤖 AI 模型  ",
            padding="10",
            style='Card.TLabelframe'
        )
        model_card.grid(row=right_row, column=right_col, sticky=(tk.W, tk.E, tk.N), pady=(0, 10), padx=(5, 0))
        model_card.columnconfigure(0, weight=1)
        right_row += 1
        
        self.model_var = tk.StringVar(value="deepseek-chat")
        model_frame = ttk.Frame(model_card, style='TFrame')
        model_frame.grid(row=0, column=0, sticky=tk.W, padx=3, pady=3)
        
        ttk.Radiobutton(
            model_frame,
            text="快速模式",
            variable=self.model_var,
            value="deepseek-chat",
            style='TRadiobutton'
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Radiobutton(
            model_frame,
            text="深度思考",
            variable=self.model_var,
            value="deepseek-reasoner",
            style='TRadiobutton'
        ).pack(side=tk.LEFT)
        
        # ===== 截图区域设置卡片（右列） =====
        region_card = ttk.LabelFrame(
            main_frame,
            text="  📸 截图设置  ",
            padding="10",
            style='Card.TLabelframe'
        )
        region_card.grid(row=right_row, column=right_col, sticky=(tk.W, tk.E, tk.N), pady=(0, 10), padx=(5, 0))
        region_card.columnconfigure(1, weight=1)
        right_row += 1
        
        region_row = 0
        
        ttk.Button(
            region_card,
            text="📐 框选区域",
            command=self._on_select_region_click,
            style='TButton'
        ).grid(row=region_row, column=0, padx=(0, 8), pady=3)
        
        self.region_label = ttk.Label(
            region_card,
            text="未设置",
            foreground="#e74c3c",
            background='#ffffff'
        )
        self.region_label.grid(row=region_row, column=1, sticky=tk.W, pady=3)
        region_row += 1
        
        # 标记选项位置
        self.option_frame = ttk.Frame(region_card, style='TFrame')
        self.option_frame.grid(row=region_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=3)
        self.option_frame.columnconfigure(1, weight=1)
        
        self.mark_option_btn = ttk.Button(
            self.option_frame,
            text="✏️ 标记选项",
            command=self._on_mark_options_click,
            style='TButton'
        )
        self.mark_option_btn.grid(row=0, column=0, padx=(0, 8))
        
        self.option_label = ttk.Label(
            self.option_frame,
            text="未设置",
            foreground="#e74c3c",
            background='#ffffff'
        )
        self.option_label.grid(row=0, column=1, sticky=tk.W)
        
        
        # ===== 答题设置卡片（右列） =====
        settings_card = ttk.LabelFrame(
            main_frame,
            text="  ⚙️ 答题设置  ",
            padding="10",
            style='Card.TLabelframe'
        )
        settings_card.grid(row=right_row, column=right_col, sticky=(tk.W, tk.E, tk.N), pady=(0, 10), padx=(5, 0))
        settings_card.columnconfigure(0, weight=1)
        right_row += 1
        
        settings_row = 0
        
        # 基本设置
        basic_settings_frame = ttk.Frame(settings_card, style='TFrame')
        basic_settings_frame.grid(row=settings_row, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        settings_row += 1
        
        ttk.Label(
            basic_settings_frame,
            text="间隔(秒):",
            background='#ffffff',
            font=('Microsoft YaHei UI', 8)
        ).grid(row=0, column=0, sticky=tk.W, padx=(0, 3))
        
        self.interval_var = tk.StringVar(value="3")
        ttk.Entry(
            basic_settings_frame,
            textvariable=self.interval_var,
            width=8,
            font=('Consolas', 9)
        ).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(
            basic_settings_frame,
            text="题数:",
            background='#ffffff',
            font=('Microsoft YaHei UI', 8)
        ).grid(row=0, column=2, sticky=tk.W, padx=(0, 3))
        
        self.total_questions_var = tk.StringVar(value="10")
        ttk.Entry(
            basic_settings_frame,
            textvariable=self.total_questions_var,
            width=8,
            font=('Consolas', 9)
        ).grid(row=0, column=3)
        
        # 自动跳转选项
        self.auto_next_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            settings_card,
            text="自动跳转（无下一题按钮）",
            variable=self.auto_next_var,
            bg='#ffffff',
            fg='#2c3e50',
            activebackground='#ffffff',
            activeforeground='#2c3e50',
            selectcolor='#ffffff',
            font=('Microsoft YaHei UI', 9),
            relief='flat',
            highlightthickness=0
        ).grid(row=settings_row, column=0, sticky=tk.W, pady=(0, 5))
        settings_row += 1
        
        # 滚动设置框架（仅在滚动模式下显示）
        self.scroll_settings_frame = ttk.Frame(settings_card, style='TFrame')
        self.scroll_settings_frame.grid(row=settings_row, column=0, sticky=(tk.W, tk.E), pady=(3, 0))
        self.scroll_settings_frame.columnconfigure(1, weight=1)
        
        ttk.Label(
            self.scroll_settings_frame,
            text="📜 滚动设置",
            font=('Microsoft YaHei UI', 8, 'bold'),
            background='#ffffff'
        ).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(
            self.scroll_settings_frame,
            text="重叠(px):",
            background='#ffffff',
            font=('Microsoft YaHei UI', 8)
        ).grid(row=1, column=0, sticky=tk.W, padx=(0, 3))
        
        self.scroll_overlap_var = tk.StringVar(value="150")
        ttk.Entry(
            self.scroll_settings_frame,
            textvariable=self.scroll_overlap_var,
            width=8,
            font=('Consolas', 9)
        ).grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(
            self.scroll_settings_frame,
            text="延迟(秒):",
            background='#ffffff',
            font=('Microsoft YaHei UI', 8)
        ).grid(row=1, column=2, sticky=tk.W, padx=(0, 3))
        
        self.scroll_delay_var = tk.StringVar(value="1.0")
        ttk.Entry(
            self.scroll_settings_frame,
            textvariable=self.scroll_delay_var,
            width=8,
            font=('Consolas', 9)
        ).grid(row=1, column=3, sticky=tk.W)
        
        # 初始隐藏滚动设置
        self.scroll_settings_frame.grid_remove()
        
        # ===== 开始答题按钮（右列） =====
        self.start_button = tk.Button(
            main_frame,
            text="▶️ 开始答题",
            command=self._on_start_button_click,
            font=('Microsoft YaHei UI', 11, 'bold'),
            bg='#27ae60',
            fg='white',
            activebackground='#229954',
            activeforeground='white',
            relief='flat',
            padx=25,
            pady=10,
            cursor='hand2',
            borderwidth=0
        )
        self.start_button.grid(row=right_row, column=right_col, pady=(0, 10), padx=(5, 0))
        right_row += 1
        
        # ===== 计算下一行（考虑 rowspan） =====
        # left_row 是 API 配置卡片的起始行 + 1
        # API 配置卡片使用 rowspan=10，所以实际占据到 left_row + 10 - 1
        # 日志区域应该在 API 配置卡片之后
        api_card_end_row = (left_row - 1) + 10  # left_row-1 是 API 配置卡片的起始行
        next_row = max(api_card_end_row, right_row)
        
        # ===== 日志显示区域卡片（跨两列） =====
        log_card = ttk.LabelFrame(
            main_frame,
            text="  📝 运行日志  ",
            padding="8",
            style='Card.TLabelframe'
        )
        log_card.grid(row=next_row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(0, weight=1)
        next_row += 1
        
        self.log_text = scrolledtext.ScrolledText(
            log_card,
            height=6,
            width=80,
            wrap=tk.WORD,
            state='disabled',
            font=('Consolas', 8),
            bg='#fafafa',
            fg='#2c3e50',
            relief='flat',
            borderwidth=0
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置日志区域的网格权重，使其可以扩展
        main_frame.rowconfigure(next_row - 1, weight=1)
    
    def _load_config_to_ui(self) -> None:
        """
        从配置管理器加载配置并更新界面（内部方法）
        """
        # 加载 DeepSeek API Key
        deepseek_key = self.config_manager.get('api_key', '')
        if deepseek_key:
            self.deepseek_api_key_var.set(self.config_manager.mask_api_key(deepseek_key))
            self.deepseek_api_key_entry.config(state="readonly", show="")  # 不遮蔽，直接显示遮蔽后的文本
            self.deepseek_edit_btn.config(text="编辑")
        else:
            self.deepseek_api_key_var.set("")
            self.deepseek_api_key_entry.config(state="normal", show="")
            self.deepseek_edit_btn.config(text="保存")
            self.api_key_editing['deepseek'] = True
        
        # 基础模式 API Key
        baidu_basic_api_key = self.config_manager.get('baidu_basic_api_key', '')
        if baidu_basic_api_key:
            self.baidu_basic_api_key_var.set(self.config_manager.mask_api_key(baidu_basic_api_key))
            self.baidu_basic_api_key_entry.config(state="readonly", show="")
            self.baidu_basic_api_edit_btn.config(text="编辑")
        else:
            self.baidu_basic_api_key_var.set("")
            self.baidu_basic_api_key_entry.config(state="normal", show="")
            self.baidu_basic_api_edit_btn.config(text="保存")
            self.api_key_editing['baidu_basic_api'] = True
        
        # 基础模式 Secret Key
        baidu_basic_secret_key = self.config_manager.get('baidu_basic_secret_key', '')
        if baidu_basic_secret_key:
            self.baidu_basic_secret_key_var.set(self.config_manager.mask_api_key(baidu_basic_secret_key))
            self.baidu_basic_secret_key_entry.config(state="readonly", show="")
            self.baidu_basic_secret_edit_btn.config(text="编辑")
        else:
            self.baidu_basic_secret_key_var.set("")
            self.baidu_basic_secret_key_entry.config(state="normal", show="")
            self.baidu_basic_secret_edit_btn.config(text="保存")
            self.api_key_editing['baidu_basic_secret'] = True
        
        # 高精度模式 API Key
        baidu_accurate_api_key = self.config_manager.get('baidu_accurate_api_key', '')
        if baidu_accurate_api_key:
            self.baidu_accurate_api_key_var.set(self.config_manager.mask_api_key(baidu_accurate_api_key))
            self.baidu_accurate_api_key_entry.config(state="readonly", show="")
            self.baidu_accurate_api_edit_btn.config(text="编辑")
        else:
            self.baidu_accurate_api_key_var.set("")
            self.baidu_accurate_api_key_entry.config(state="normal", show="")
            self.baidu_accurate_api_edit_btn.config(text="保存")
            self.api_key_editing['baidu_accurate_api'] = True
        
        # 高精度模式 Secret Key
        baidu_accurate_secret_key = self.config_manager.get('baidu_accurate_secret_key', '')
        if baidu_accurate_secret_key:
            self.baidu_accurate_secret_key_var.set(self.config_manager.mask_api_key(baidu_accurate_secret_key))
            self.baidu_accurate_secret_key_entry.config(state="readonly", show="")
            self.baidu_accurate_secret_edit_btn.config(text="编辑")
        else:
            self.baidu_accurate_secret_key_var.set("")
            self.baidu_accurate_secret_key_entry.config(state="normal", show="")
            self.baidu_accurate_secret_edit_btn.config(text="保存")
            self.api_key_editing['baidu_accurate_secret'] = True
    
    def _toggle_edit_api_key(self, key_type: str) -> None:
        """
        切换 API Key 编辑模式（内部方法）
        
        点击"编辑"按钮时，切换输入框为可编辑状态，显示完整的 API Key。
        点击"保存"按钮时，保存 API Key 到配置文件，并切换回只读状态。
        
        Args:
            key_type: API Key 类型 ('deepseek', 'baidu_basic_api', 'baidu_basic_secret', 
                                    'baidu_accurate_api', 'baidu_accurate_secret')
        """
        # 根据类型选择对应的控件和配置键
        if key_type == 'deepseek':
            entry = self.deepseek_api_key_entry
            var = self.deepseek_api_key_var
            btn = self.deepseek_edit_btn
            config_key = 'api_key'
        elif key_type == 'baidu_basic_api':
            entry = self.baidu_basic_api_key_entry
            var = self.baidu_basic_api_key_var
            btn = self.baidu_basic_api_edit_btn
            config_key = 'baidu_basic_api_key'
        elif key_type == 'baidu_basic_secret':
            entry = self.baidu_basic_secret_key_entry
            var = self.baidu_basic_secret_key_var
            btn = self.baidu_basic_secret_edit_btn
            config_key = 'baidu_basic_secret_key'
        elif key_type == 'baidu_accurate_api':
            entry = self.baidu_accurate_api_key_entry
            var = self.baidu_accurate_api_key_var
            btn = self.baidu_accurate_api_edit_btn
            config_key = 'baidu_accurate_api_key'
        elif key_type == 'baidu_accurate_secret':
            entry = self.baidu_accurate_secret_key_entry
            var = self.baidu_accurate_secret_key_var
            btn = self.baidu_accurate_secret_edit_btn
            config_key = 'baidu_accurate_secret_key'
        else:
            return
        
        # 切换编辑状态
        if not self.api_key_editing[key_type]:
            # 进入编辑模式
            self.api_key_editing[key_type] = True
            entry.config(state='normal', show='')
            
            # 显示完整的 API Key
            full_key = self.config_manager.get(config_key, '')
            var.set(full_key)
            
            btn.config(text="保存")
        else:
            # 保存并退出编辑模式
            self.api_key_editing[key_type] = False
            
            # 获取输入的 API Key
            new_key = var.get().strip()
            
            # 保存到配置
            try:
                self.config_manager.set(config_key, new_key)
                self._log(f"已保存 {config_key}")
                
                # 如果是 OCR 相关的 Key，清除缓存的 Access Token
                if key_type.startswith('baidu_'):
                    self.ocr_service.clear_token_cache()
                
            except Exception as e:
                messagebox.showerror("保存失败", f"保存配置失败: {str(e)}")
                self._log(f"保存配置失败: {str(e)}")
            
            # 切换回只读模式，显示遮蔽版本
            entry.config(state='readonly', show='')  # 不使用 show="*"，直接显示遮蔽后的文本
            if new_key:
                var.set(self.config_manager.mask_api_key(new_key))
            else:
                var.set('')
            
            btn.config(text="编辑")
    
    def _on_answering_mode_changed(self) -> None:
        """
        答题模式切换事件处理（内部方法）
        
        根据答题模式的选择：
        - 固定答题：可以选择任意OCR模式，显示标记选项位置按钮
        - 滚动答题：强制使用高精度OCR模式，显示滚动设置
        """
        answering_mode = self.answering_mode_var.get()
        
        if answering_mode == "fixed":
            # 固定答题模式
            # 启用OCR模式选择
            self.ocr_basic_radio.config(state="normal")
            self.ocr_accurate_radio.config(state="normal")
            
            # 隐藏滚动设置
            self.scroll_settings_frame.grid_remove()
            
            # 根据当前OCR模式显示/隐藏标记选项位置按钮
            self._on_ocr_mode_changed()
            
            self._log("切换到固定答题模式")
            
        else:  # scroll
            # 滚动答题模式
            # 强制使用高精度OCR模式
            self.ocr_mode_var.set("accurate_basic")
            self.ocr_basic_radio.config(state="disabled")
            self.ocr_accurate_radio.config(state="disabled")
            
            # 显示滚动设置
            self.scroll_settings_frame.grid()
            
            # 隐藏标记选项位置按钮（滚动模式自动提取）
            self.mark_option_btn.grid_remove()
            self.option_label.config(text="将自动从 OCR 结果提取", foreground="#3498db")
            
            self._log("切换到滚动答题模式（强制使用高精度OCR）")
    
    def _on_ocr_mode_changed(self) -> None:
        """
        OCR 模式切换事件处理（内部方法）
        
        根据选择的 OCR 模式显示或隐藏"标记选项位置"按钮。
        - 基础模式：显示按钮，需要手动标记
        - 高精度模式：隐藏按钮，自动从 OCR 结果提取位置
        
        注意：滚动答题模式下，此函数不会被调用（OCR模式被锁定）
        """
        ocr_mode = self.ocr_mode_var.get()
        
        # 只在固定答题模式下才处理OCR模式切换
        if self.answering_mode_var.get() == "fixed":
            if ocr_mode == "general_basic":
                # 基础模式：显示标记选项位置按钮
                self.mark_option_btn.grid()
                if not self.option_positions or not self.option_positions.get('options'):
                    self.option_label.config(text="未设置", foreground="#e74c3c")
            else:
                # 高精度模式：隐藏标记选项位置按钮
                self.mark_option_btn.grid_remove()
                self.option_label.config(text="将自动从 OCR 结果提取", foreground="#3498db")
                # 清除手动标记的选项位置，因为会自动提取
                if self.option_positions:
                    self.option_positions = None
    
    def _on_scroll_mode_changed(self) -> None:
        """
        滚动模式切换事件处理（内部方法）
        
        已废弃：现在使用答题模式单选按钮替代
        """
        pass  # 保留此方法以保持向后兼容
    
    def _on_select_region_click(self) -> None:
        """
        框选区域按钮点击事件处理（内部方法）
        
        隐藏主窗口，创建 RegionSelector 让用户框选答题区域。
        选择完成后，更新界面状态并显示主窗口。
        """
        # 隐藏主窗口
        self.root.withdraw()
        
        # 定义区域选择完成的回调函数
        def on_region_selected(region):
            # 保存区域
            self.region = region
            
            # 更新界面显示
            self.region_label.config(
                text=f"已设置: ({region[0]}, {region[1]}) -> ({region[2]}, {region[3]})",
                foreground="#27ae60"
            )
            
            # 记录日志
            self._log(f"已设置答题区域: {region}")
            
            # 显示主窗口
            self.root.deiconify()
        
        # 创建区域选择器
        RegionSelector(self.root, on_region_selected)
    
    def _on_mark_options_click(self) -> None:
        """
        标记选项按钮点击事件处理（内部方法）
        
        隐藏主窗口，创建 OptionMarker 让用户标记选项位置。
        标记完成后，更新界面状态并显示主窗口。
        """
        # 隐藏主窗口
        self.root.withdraw()
        
        # 定义选项标记完成的回调函数
        def on_options_marked(positions):
            # 保存选项位置
            self.option_positions = positions
            
            # 构建显示文本
            marked_options = list(positions['options'].keys())
            has_next = positions['next'] is not None
            
            display_text = f"已标记: {', '.join(marked_options)}"
            if has_next:
                display_text += ", 下一题"
            
            # 更新界面显示
            self.option_label.config(
                text=display_text,
                foreground="#27ae60"
            )
            
            # 记录日志
            self._log(f"已标记选项位置: {marked_options}")
            if has_next:
                self._log(f"已标记下一题按钮位置: {positions['next']}")
            
            # 显示主窗口
            self.root.deiconify()
        
        # 创建选项标记器
        OptionMarker(self.root, on_options_marked)
    
    def _on_start_button_click(self) -> None:
        """
        开始/停止按钮点击事件处理（内部方法）
        
        如果当前未在答题，则验证所有必要设置并开始答题。
        如果当前正在答题，则停止答题。
        """
        if not self.is_running:
            # 开始答题
            try:
                # 验证 API Keys
                if not self.config_manager.get('api_key'):
                    messagebox.showerror("配置错误", "请先设置 DeepSeek API Key")
                    return
                
                # 获取当前选择的 OCR 模式
                ocr_mode = self.ocr_mode_var.get()
                
                # 根据 OCR 模式验证对应的 API Keys
                if ocr_mode == "general_basic":
                    if not self.config_manager.get('baidu_basic_api_key'):
                        messagebox.showerror("配置错误", "请先设置百度 OCR 基础模式 API Key")
                        return
                    if not self.config_manager.get('baidu_basic_secret_key'):
                        messagebox.showerror("配置错误", "请先设置百度 OCR 基础模式 Secret Key")
                        return
                else:  # accurate_basic
                    if not self.config_manager.get('baidu_accurate_api_key'):
                        messagebox.showerror("配置错误", "请先设置百度 OCR 高精度模式 API Key")
                        return
                    if not self.config_manager.get('baidu_accurate_secret_key'):
                        messagebox.showerror("配置错误", "请先设置百度 OCR 高精度模式 Secret Key")
                        return
                
                # 验证区域设置
                if not self.region:
                    messagebox.showerror("配置错误", "请先框选答题区域")
                    return
                
                # 验证选项位置（仅固定答题模式 + 基础OCR模式需要）
                if not scroll_mode:  # 固定答题模式
                    ocr_mode = self.ocr_mode_var.get()
                    if ocr_mode == "general_basic":
                        if not self.option_positions or not self.option_positions['options']:
                            messagebox.showerror("配置错误", "请先标记选项位置")
                            return
                
                # 验证答题设置
                try:
                    interval = float(self.interval_var.get())
                    if interval < 0:
                        raise ValueError("间隔时间不能为负数")
                except ValueError as e:
                    messagebox.showerror("配置错误", f"每题间隔设置无效: {str(e)}")
                    return
                
                try:
                    total_questions = int(self.total_questions_var.get())
                    if total_questions <= 0:
                        raise ValueError("总题数必须大于 0")
                except ValueError as e:
                    messagebox.showerror("配置错误", f"总题数设置无效: {str(e)}")
                    return
                
                # 获取模型选择和 OCR 模式
                model = self.model_var.get()
                ocr_mode = self.ocr_mode_var.get()
                auto_next = self.auto_next_var.get()
                
                # 获取答题模式
                answering_mode = self.answering_mode_var.get()
                scroll_mode = (answering_mode == "scroll")
                
                # 获取滚动模式设置
                scroll_overlap = 150  # 默认值
                scroll_delay = 1.0    # 默认值
                
                if scroll_mode:
                    try:
                        scroll_overlap = int(self.scroll_overlap_var.get())
                        if scroll_overlap < 0:
                            raise ValueError("重叠区域不能为负数")
                    except ValueError as e:
                        messagebox.showerror("配置错误", f"重叠区域设置无效: {str(e)}")
                        return
                    
                    try:
                        scroll_delay = float(self.scroll_delay_var.get())
                        if scroll_delay < 0:
                            raise ValueError("滚动延迟不能为负数")
                    except ValueError as e:
                        messagebox.showerror("配置错误", f"滚动延迟设置无效: {str(e)}")
                        return
                
                # 根据答题模式和OCR模式决定是否传递选项位置
                if scroll_mode:
                    # 滚动模式：不需要手动标记，由 automation controller 自动提取
                    option_positions = None
                    next_button_pos = None
                elif ocr_mode == "general_basic":
                    # 固定模式 + 基础OCR：使用手动标记的位置
                    option_positions = self.option_positions['options']
                    next_button_pos = self.option_positions['next']
                else:
                    # 固定模式 + 高精度OCR：由 automation controller 自动提取
                    option_positions = None
                    next_button_pos = None
                
                # 更新状态
                self.is_running = True
                self.start_button.config(
                    text="⏸️ 停止答题",
                    bg='#e74c3c',
                    activebackground='#c0392b'
                )
                
                # 定义停止回调
                def on_stop():
                    self.is_running = False
                    self.start_button.config(
                        text="▶️ 开始答题",
                        bg='#27ae60',
                        activebackground='#229954'
                    )
                
                # 开始答题
                self.automation_controller.start_answering(
                    region=self.region,
                    option_positions=option_positions,
                    next_button_pos=next_button_pos,
                    interval=interval,
                    total_questions=total_questions,
                    model=model,
                    ocr_mode=ocr_mode,
                    auto_next=auto_next,
                    scroll_mode=scroll_mode,
                    scroll_overlap=scroll_overlap,
                    scroll_delay=scroll_delay,
                    log_callback=self._log,
                    stop_callback=on_stop
                )
                
            except Exception as e:
                self.is_running = False
                self.start_button.config(
                    text="▶️ 开始答题",
                    bg='#27ae60',
                    activebackground='#229954'
                )
                messagebox.showerror("启动失败", f"启动答题失败: {str(e)}")
                self._log(f"启动答题失败: {str(e)}")
        else:
            # 停止答题
            self.automation_controller.stop_answering()
            self.start_button.config(
                text="▶️ 开始答题",
                bg='#27ae60',
                activebackground='#229954'
            )
            self.is_running = False
    
    def _log(self, message: str) -> None:
        """
        添加日志到界面（内部方法）
        
        在日志显示区域添加带时间戳的日志消息。
        
        Args:
            message: 日志消息
        """
        # 获取当前时间
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 构建日志行
        log_line = f"[{timestamp}] {message}\n"
        
        # 添加到日志区域
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_line)
        self.log_text.see(tk.END)  # 自动滚动到底部
        self.log_text.config(state='disabled')
