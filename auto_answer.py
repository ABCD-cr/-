import tkinter as tk
from tkinter import messagebox, scrolledtext
from openai import OpenAI
import threading
import json
import os
import pyautogui
import time
from PIL import ImageGrab, ImageTk
import base64
from urllib.parse import quote
import requests

class AutoAnswerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek 自动答题系统")
        self.root.geometry("700x750")
        
        self.config_file = "config.json"
        self.api_key = ""
        self.baidu_api_key = ""
        self.baidu_secret_key = ""
        self.baidu_access_token = None
        self.is_editing = False
        self.is_editing_baidu_api = False
        self.is_editing_baidu_secret = False
        self.is_running = False
        self.region = None  # 截图区域 (x1, y1, x2, y2)
        self.option_positions = {}  # 选项位置 {'A': (x, y), 'B': (x, y), ...}
        self.next_button_pos = None  # 下一题按钮位置 (x, y)
        
        # 加载配置
        self.load_config()
        
        # DeepSeek API Key 输入
        tk.Label(root, text="DeepSeek API Key:", font=("Arial", 10)).pack(pady=(10, 5))
        
        key_frame = tk.Frame(root)
        key_frame.pack(pady=5)
        
        self.api_key_entry = tk.Entry(key_frame, width=45)
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        
        if self.api_key:
            self.api_key_entry.insert(0, self.mask_api_key(self.api_key))
            self.api_key_entry.config(state=tk.DISABLED)
            btn_text = "修改"
        else:
            self.api_key_entry.insert(0, "")
            self.is_editing = True
            btn_text = "保存"
        
        self.edit_btn = tk.Button(key_frame, text=btn_text, command=self.toggle_edit, width=8)
        self.edit_btn.pack(side=tk.LEFT)
        
        # 百度 OCR API Key 输入
        tk.Label(root, text="百度 OCR API Key:", font=("Arial", 10)).pack(pady=(10, 5))
        
        baidu_key_frame = tk.Frame(root)
        baidu_key_frame.pack(pady=5)
        
        self.baidu_api_key_entry = tk.Entry(baidu_key_frame, width=45)
        self.baidu_api_key_entry.pack(side=tk.LEFT, padx=5)
        
        if self.baidu_api_key:
            self.baidu_api_key_entry.insert(0, self.mask_api_key(self.baidu_api_key))
            self.baidu_api_key_entry.config(state=tk.DISABLED)
            baidu_api_btn_text = "修改"
        else:
            self.baidu_api_key_entry.insert(0, "")
            self.is_editing_baidu_api = True
            baidu_api_btn_text = "保存"
        
        self.edit_baidu_api_btn = tk.Button(baidu_key_frame, text=baidu_api_btn_text, command=self.toggle_edit_baidu_api, width=8)
        self.edit_baidu_api_btn.pack(side=tk.LEFT)
        
        # 百度 OCR Secret Key 输入
        tk.Label(root, text="百度 OCR Secret Key:", font=("Arial", 10)).pack(pady=(5, 5))
        
        baidu_secret_frame = tk.Frame(root)
        baidu_secret_frame.pack(pady=5)
        
        self.baidu_secret_key_entry = tk.Entry(baidu_secret_frame, width=45)
        self.baidu_secret_key_entry.pack(side=tk.LEFT, padx=5)
        
        if self.baidu_secret_key:
            self.baidu_secret_key_entry.insert(0, self.mask_api_key(self.baidu_secret_key))
            self.baidu_secret_key_entry.config(state=tk.DISABLED)
            baidu_secret_btn_text = "修改"
        else:
            self.baidu_secret_key_entry.insert(0, "")
            self.is_editing_baidu_secret = True
            baidu_secret_btn_text = "保存"
        
        self.edit_baidu_secret_btn = tk.Button(baidu_secret_frame, text=baidu_secret_btn_text, command=self.toggle_edit_baidu_secret, width=8)
        self.edit_baidu_secret_btn.pack(side=tk.LEFT)
        
        # 深度思考模式选择
        tk.Label(root, text="深度思考模式:", font=("Arial", 10)).pack(pady=(10, 5))
        self.model_var = tk.StringVar(value="deepseek-chat")
        
        frame = tk.Frame(root)
        frame.pack(pady=5)
        tk.Radiobutton(frame, text="关闭 (deepseek-chat)", 
                      variable=self.model_var, value="deepseek-chat").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame, text="开启 (deepseek-reasoner)", 
                      variable=self.model_var, value="deepseek-reasoner").pack(side=tk.LEFT, padx=10)
        
        # 截图区域设置
        tk.Label(root, text="答题区域:", font=("Arial", 10)).pack(pady=(10, 5))
        region_frame = tk.Frame(root)
        region_frame.pack(pady=5)
        
        self.region_label = tk.Label(region_frame, text="未设置", fg="red")
        self.region_label.pack(side=tk.LEFT, padx=5)
        
        tk.Button(region_frame, text="框选区域", command=self.select_region, 
                 bg="#2196F3", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        
        tk.Button(region_frame, text="标记选项位置", command=self.mark_options, 
                 bg="#FF9800", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        
        # 选项位置状态
        self.options_label = tk.Label(root, text="选项位置: 未标记", fg="red", font=("Arial", 9))
        self.options_label.pack(pady=(0, 5))
        
        # 答题设置
        tk.Label(root, text="答题设置:", font=("Arial", 10)).pack(pady=(10, 5))
        setting_frame = tk.Frame(root)
        setting_frame.pack(pady=5)
        
        tk.Label(setting_frame, text="每题间隔(秒):").pack(side=tk.LEFT, padx=5)
        self.interval_var = tk.StringVar(value="3")
        tk.Entry(setting_frame, textvariable=self.interval_var, width=5).pack(side=tk.LEFT, padx=5)
        
        tk.Label(setting_frame, text="总题数:").pack(side=tk.LEFT, padx=5)
        self.total_questions_var = tk.StringVar(value="10")
        tk.Entry(setting_frame, textvariable=self.total_questions_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # 开始/停止按钮
        self.start_btn = tk.Button(root, text="开始答题", command=self.start_answering, 
                                   bg="#4CAF50", fg="white", font=("Arial", 12), 
                                   width=20, height=1)
        self.start_btn.pack(pady=15)
        
        # 日志显示
        tk.Label(root, text="答题日志:", font=("Arial", 10)).pack(pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(root, width=70, height=12, 
                                                  bg="#f9f9f9", state=tk.DISABLED)
        self.log_text.pack(pady=5)
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_key = config.get('api_key', '')
                    self.baidu_api_key = config.get('baidu_api_key', '')
                    self.baidu_secret_key = config.get('baidu_secret_key', '')
            except:
                pass
    
    def save_config(self):
        """保存配置文件"""
        config = {
            'api_key': self.api_key,
            'baidu_api_key': self.baidu_api_key,
            'baidu_secret_key': self.baidu_secret_key
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def mask_api_key(self, key):
        """显示前8位和后4位，中间用星号"""
        if not key:
            return ""
        if len(key) <= 12:
            return key
        return key[:8] + "*" * (len(key) - 12) + key[-4:]
    
    def toggle_edit(self):
        """切换编辑模式"""
        if not self.is_editing:
            self.api_key_entry.config(state=tk.NORMAL)
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.insert(0, self.api_key)
            self.edit_btn.config(text="保存")
            self.is_editing = True
        else:
            new_key = self.api_key_entry.get().strip()
            if new_key:
                self.api_key = new_key
                self.save_config()
                self.api_key_entry.delete(0, tk.END)
                self.api_key_entry.insert(0, self.mask_api_key(self.api_key))
                self.api_key_entry.config(state=tk.DISABLED)
                self.edit_btn.config(text="修改")
                self.is_editing = False
                messagebox.showinfo("成功", "API Key 已保存")
            else:
                messagebox.showerror("错误", "API Key 不能为空")
    
    def toggle_edit_baidu(self):
        """切换百度 API Key 编辑模式"""
        if not self.is_editing_baidu_api:
            # 进入编辑模式
            self.baidu_api_key_entry.config(state=tk.NORMAL)
            self.baidu_api_key_entry.delete(0, tk.END)
            self.baidu_api_key_entry.insert(0, self.baidu_api_key)
            
            self.edit_baidu_api_btn.config(text="保存")
            self.is_editing_baidu_api = True
        else:
            # 保存并退出编辑模式
            new_api_key = self.baidu_api_key_entry.get().strip()
            
            if new_api_key:
                self.baidu_api_key = new_api_key
                self.baidu_access_token = None  # 重置 token
                self.save_config()
                
                self.baidu_api_key_entry.delete(0, tk.END)
                self.baidu_api_key_entry.insert(0, self.mask_api_key(self.baidu_api_key))
                self.baidu_api_key_entry.config(state=tk.DISABLED)
                
                self.edit_baidu_api_btn.config(text="修改")
                self.is_editing_baidu_api = False
                messagebox.showinfo("成功", "百度 OCR API Key 已保存")
            else:
                messagebox.showerror("错误", "API Key 不能为空")
    
    def toggle_edit_baidu_api(self):
        """切换百度 API Key 编辑模式"""
        if not self.is_editing_baidu_api:
            # 进入编辑模式
            self.baidu_api_key_entry.config(state=tk.NORMAL)
            self.baidu_api_key_entry.delete(0, tk.END)
            self.baidu_api_key_entry.insert(0, self.baidu_api_key)
            
            self.edit_baidu_api_btn.config(text="保存")
            self.is_editing_baidu_api = True
        else:
            # 保存并退出编辑模式
            new_api_key = self.baidu_api_key_entry.get().strip()
            
            if new_api_key:
                self.baidu_api_key = new_api_key
                self.baidu_access_token = None  # 重置 token
                self.save_config()
                
                self.baidu_api_key_entry.delete(0, tk.END)
                self.baidu_api_key_entry.insert(0, self.mask_api_key(self.baidu_api_key))
                self.baidu_api_key_entry.config(state=tk.DISABLED)
                
                self.edit_baidu_api_btn.config(text="修改")
                self.is_editing_baidu_api = False
                messagebox.showinfo("成功", "百度 OCR API Key 已保存")
            else:
                messagebox.showerror("错误", "API Key 不能为空")
    
    def toggle_edit_baidu_secret(self):
        """切换百度 Secret Key 编辑模式"""
        if not self.is_editing_baidu_secret:
            # 进入编辑模式
            self.baidu_secret_key_entry.config(state=tk.NORMAL)
            self.baidu_secret_key_entry.delete(0, tk.END)
            self.baidu_secret_key_entry.insert(0, self.baidu_secret_key)
            
            self.edit_baidu_secret_btn.config(text="保存")
            self.is_editing_baidu_secret = True
        else:
            # 保存并退出编辑模式
            new_secret_key = self.baidu_secret_key_entry.get().strip()
            
            if new_secret_key:
                self.baidu_secret_key = new_secret_key
                self.baidu_access_token = None  # 重置 token
                self.save_config()
                
                self.baidu_secret_key_entry.delete(0, tk.END)
                self.baidu_secret_key_entry.insert(0, self.mask_api_key(self.baidu_secret_key))
                self.baidu_secret_key_entry.config(state=tk.DISABLED)
                
                self.edit_baidu_secret_btn.config(text="修改")
                self.is_editing_baidu_secret = False
                messagebox.showinfo("成功", "百度 OCR Secret Key 已保存")
            else:
                messagebox.showerror("错误", "Secret Key 不能为空")
    
    def mark_options(self):
        """标记选项和下一题按钮位置"""
        if not self.region:
            messagebox.showerror("错误", "请先框选答题区域")
            return
        
        self.root.withdraw()
        time.sleep(0.3)
        
        # 创建标记窗口
        marker = OptionMarker(self.root, self.on_options_marked)
    
    def on_options_marked(self, positions):
        """选项标记完成的回调"""
        if positions:
            self.option_positions = positions['options']
            self.next_button_pos = positions['next']
            
            # 更新状态显示
            marked_options = ', '.join(self.option_positions.keys())
            next_status = "已标记" if self.next_button_pos else "未标记"
            self.options_label.config(
                text=f"选项位置: {marked_options} | 下一题: {next_status}",
                fg="green"
            )
            self.log(f"已标记选项: {marked_options}, 下一题: {next_status}")
        
        self.root.deiconify()
    
    def select_region(self):
        """框选屏幕区域"""
        self.root.withdraw()  # 隐藏主窗口
        time.sleep(0.3)
        
        # 创建全屏透明窗口用于框选
        selector = RegionSelector(self.root, self.on_region_selected)
    
    def on_region_selected(self, region):
        """区域选择完成的回调"""
        self.region = region
        if region:
            self.region_label.config(
                text=f"已设置: ({region[0]}, {region[1]}) - ({region[2]}, {region[3]})",
                fg="green"
            )
            self.log(f"已设置答题区域: {region}")
        self.root.deiconify()  # 显示主窗口
    
    def start_answering(self):
        """开始/停止答题"""
        if not self.is_running:
            # 检查设置
            if not self.api_key:
                messagebox.showerror("错误", "请先设置 DeepSeek API Key")
                return
            
            if not self.baidu_api_key or not self.baidu_secret_key:
                messagebox.showerror("错误", "请先设置百度 OCR API Key")
                return
            
            if not self.option_positions:
                messagebox.showerror("错误", "请先标记选项位置")
                return
            
            try:
                interval = float(self.interval_var.get())
                total = int(self.total_questions_var.get())
                if interval <= 0 or total <= 0:
                    raise ValueError
            except:
                messagebox.showerror("错误", "请输入有效的间隔时间和题目数量")
                return
            
            # 开始答题
            self.is_running = True
            self.start_btn.config(text="停止答题", bg="#f44336")
            self.log("=" * 50)
            self.log("开始自动答题...")
            
            thread = threading.Thread(target=self.answer_loop, args=(interval, total))
            thread.start()
        else:
            # 停止答题
            self.is_running = False
            self.start_btn.config(text="开始答题", bg="#4CAF50")
            self.log("已停止答题")
    
    def answer_loop(self, interval, total):
        """答题循环"""
        for i in range(1, total + 1):
            if not self.is_running:
                break
            
            self.log(f"\n第 {i}/{total} 题:")
            
            try:
                # 截图
                screenshot = ImageGrab.grab(bbox=self.region)
                self.log("已截图")
                
                # 发送给 AI 分析
                answer = self.analyze_question(screenshot)
                self.log(f"AI 回答: {answer}")
                
                # 点击答案
                if answer and i < total:  # 最后一题不点击下一题
                    self.click_answer(answer)
                    time.sleep(1)
                    self.click_next()
                    self.log("已点击答案并进入下一题")
                elif i == total:
                    self.click_answer(answer)
                    self.log("最后一题，已点击答案但不提交")
                
                # 等待间隔
                if i < total:
                    time.sleep(interval)
                
            except Exception as e:
                self.log(f"错误: {str(e)}")
                break
        
        self.is_running = False
        self.start_btn.config(text="开始答题", bg="#4CAF50")
        self.log("\n答题完成！")
    
    def get_baidu_access_token(self):
        """获取百度 OCR Access Token"""
        if self.baidu_access_token:
            return self.baidu_access_token
        
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.baidu_api_key,
            "client_secret": self.baidu_secret_key
        }
        response = requests.post(url, params=params)
        self.baidu_access_token = response.json().get("access_token")
        return self.baidu_access_token
    
    def analyze_question(self, screenshot):
        """使用百度 OCR + AI 分析题目"""
        # 使用百度 OCR 提取文字
        try:
            # 将图片转换为 base64
            from io import BytesIO
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # 调用百度 OCR API
            url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=" + self.get_baidu_access_token()
            payload = f'image={quote(image_data)}'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload)
            result = response.json()
            
            if 'words_result' in result:
                # 提取所有识别的文字
                text = '\n'.join([item['words'] for item in result['words_result']])
                self.log(f"识别文字: {text[:100]}...")  # 显示前100个字符
            else:
                self.log(f"OCR 错误: {result}")
                return None
                
        except Exception as e:
            self.log(f"OCR 错误: {str(e)}")
            raise
        
        # 使用 DeepSeek AI 分析题目
        client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model=self.model_var.get(),
            messages=[
                {
                    "role": "system",
                    "content": "你是一个答题助手，请分析题目并给出答案。只回答选项字母或判断结果，不要解释。"
                },
                {
                    "role": "user",
                    "content": f"题目内容：\n{text}\n\n请直接回答正确选项（单选回答如：A，多选回答如：A,C，判断题回答：对 或 错）"
                }
            ],
            stream=False
        )
        
        return response.choices[0].message.content.strip()
    
    def click_answer(self, answer):
        """点击答案选项"""
        # 解析答案
        answers = [a.strip() for a in answer.upper().replace('，', ',').split(',')]
        
        for ans in answers:
            if ans in self.option_positions:
                # 使用标记的位置
                x, y = self.option_positions[ans]
                pyautogui.click(x, y)
                time.sleep(0.3)
                self.log(f"点击选项 {ans} 位置: ({x}, {y})")
            elif ans in ['对', '错', '正确', '错误', 'TRUE', 'FALSE']:
                # 判断题处理
                if '对' in self.option_positions or '正确' in self.option_positions:
                    key = '对' if '对' in self.option_positions else '正确'
                    x, y = self.option_positions[key]
                    if ans in ['对', '正确', 'TRUE']:
                        pyautogui.click(x, y)
                        self.log(f"点击 {key} 位置: ({x}, {y})")
                elif '错' in self.option_positions or '错误' in self.option_positions:
                    key = '错' if '错' in self.option_positions else '错误'
                    x, y = self.option_positions[key]
                    if ans in ['错', '错误', 'FALSE']:
                        pyautogui.click(x, y)
                        self.log(f"点击 {key} 位置: ({x}, {y})")
    
    def click_next(self):
        """点击下一题按钮"""
        if self.next_button_pos:
            x, y = self.next_button_pos
            pyautogui.click(x, y)
            self.log(f"点击下一题按钮位置: ({x}, {y})")
        else:
            self.log("警告: 未标记下一题按钮位置")
    
    def log(self, message):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)


class OptionMarker:
    """选项位置标记器"""
    def __init__(self, parent, callback):
        self.callback = callback
        self.positions = {'options': {}, 'next': None}
        self.current_marking = None
        self.marking_sequence = ['A', 'B', 'C', 'D', '下一题']
        self.current_index = 0
        
        self.top = tk.Toplevel(parent)
        self.top.attributes('-fullscreen', True)
        self.top.attributes('-alpha', 0.3)
        self.top.configure(bg='black')
        
        self.canvas = tk.Canvas(self.top, cursor="crosshair", bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Escape>", self.on_cancel)
        
        # 提示文字
        self.instruction_text = self.canvas.create_text(
            self.top.winfo_screenwidth() // 2,
            50,
            text=f"请点击选项 {self.marking_sequence[0]} 的位置",
            fill="white",
            font=("Arial", 20)
        )
        
        self.hint_text = self.canvas.create_text(
            self.top.winfo_screenwidth() // 2,
            100,
            text="按 ESC 跳过当前选项 | 标记完成后自动关闭",
            fill="yellow",
            font=("Arial", 14)
        )
        
        # 已标记的点
        self.marks = []
    
    def on_click(self, event):
        x, y = event.x, event.y
        current_option = self.marking_sequence[self.current_index]
        
        # 保存位置
        if current_option == '下一题':
            self.positions['next'] = (x, y)
        else:
            self.positions['options'][current_option] = (x, y)
        
        # 在屏幕上标记
        mark = self.canvas.create_oval(x-10, y-10, x+10, y+10, fill='red', outline='white', width=2)
        label = self.canvas.create_text(x, y, text=current_option, fill='white', font=("Arial", 12, "bold"))
        self.marks.append((mark, label))
        
        # 移动到下一个
        self.current_index += 1
        
        if self.current_index < len(self.marking_sequence):
            # 更新提示
            next_option = self.marking_sequence[self.current_index]
            self.canvas.itemconfig(self.instruction_text, text=f"请点击选项 {next_option} 的位置")
        else:
            # 完成标记
            self.finish()
    
    def on_cancel(self, event):
        # 跳过当前选项
        self.current_index += 1
        
        if self.current_index < len(self.marking_sequence):
            next_option = self.marking_sequence[self.current_index]
            self.canvas.itemconfig(self.instruction_text, text=f"请点击选项 {next_option} 的位置")
        else:
            self.finish()
    
    def finish(self):
        self.top.destroy()
        self.callback(self.positions)


class RegionSelector:
    """区域选择器"""
    def __init__(self, parent, callback):
        self.callback = callback
        self.start_x = None
        self.start_y = None
        
        self.top = tk.Toplevel(parent)
        self.top.attributes('-fullscreen', True)
        self.top.attributes('-alpha', 0.3)
        self.top.configure(bg='black')
        
        self.canvas = tk.Canvas(self.top, cursor="cross", bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.rect = None
        
        # 提示文字
        self.canvas.create_text(
            self.top.winfo_screenwidth() // 2,
            50,
            text="拖动鼠标框选答题区域",
            fill="white",
            font=("Arial", 20)
        )
    
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )
    
    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def on_release(self, event):
        end_x = event.x
        end_y = event.y
        
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        self.top.destroy()
        self.callback((x1, y1, x2, y2))


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoAnswerGUI(root)
    root.mainloop()
