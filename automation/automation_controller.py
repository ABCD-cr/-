"""
自动化控制模块

此模块协调答题流程，控制鼠标点击和循环逻辑。
"""

import time
import threading
import pyautogui
from utils.exceptions import AutomationException


class AutomationController:
    """
    自动化控制器类
    
    协调答题流程，控制鼠标点击和循环逻辑。
    使用线程执行答题循环，避免阻塞 GUI。
    """
    
    def __init__(self, screenshot_manager, ocr_service, ai_service):
        """
        初始化自动化控制器
        
        Args:
            screenshot_manager: 截图管理器实例
            ocr_service: OCR 服务实例
            ai_service: AI 服务实例
        """
        self.screenshot_manager = screenshot_manager
        self.ocr_service = ocr_service
        self.ai_service = ai_service
        
        # 停止标志，用于控制答题循环
        self._stop_flag = False
        
        # 答题线程
        self._answering_thread = None
        
        # 日志回调函数
        self._log_callback = None
    
    def start_answering(self, region: tuple, option_positions: dict,
                       next_button_pos: tuple, interval: float,
                       total_questions: int, model: str,
                       ocr_mode: str, auto_next: bool,
                       scroll_mode: bool, scroll_overlap: int, scroll_delay: float,
                       log_callback: callable, stop_callback: callable) -> None:
        """
        开始答题循环
        
        在新线程中执行答题循环，避免阻塞 GUI。
        
        Args:
            region: 截图区域 (x1, y1, x2, y2)
            option_positions: 选项位置字典 {'A': (x, y), 'B': (x, y), ...}
                             如果为 None，则从 OCR 结果中自动提取（仅高精度模式）
            next_button_pos: 下一题按钮位置 (x, y)，可以为 None
            interval: 每题间隔时间（秒）
            total_questions: 总题数
            model: AI 模型名称
            ocr_mode: OCR 模式 (general_basic 或 accurate_basic)
            auto_next: 是否自动跳转（点击选项后自动跳转，无需点击下一题按钮）
            scroll_mode: 是否启用滚动模式（长卷子答题）
            scroll_overlap: 滚动重叠区域（像素），防止漏题
            scroll_delay: 滚动后等待时间（秒）
            log_callback: 日志回调函数 log_callback(message: str)
            stop_callback: 停止回调函数 stop_callback()
        """
        # 重置停止标志
        self._stop_flag = False
        
        # 保存日志回调
        self._log_callback = log_callback
        
        # 定义答题线程函数
        def answering_thread():
            try:
                if scroll_mode:
                    # 滚动模式：长卷子答题
                    self._answering_loop_scroll_mode(
                        region=region,
                        option_positions=option_positions,
                        next_button_pos=next_button_pos,
                        interval=interval,
                        total_questions=total_questions,
                        model=model,
                        ocr_mode=ocr_mode,
                        auto_next=auto_next,
                        scroll_overlap=scroll_overlap,
                        scroll_delay=scroll_delay
                    )
                else:
                    # 普通模式：固定区域答题
                    self._answering_loop_normal_mode(
                        region=region,
                        option_positions=option_positions,
                        next_button_pos=next_button_pos,
                        interval=interval,
                        total_questions=total_questions,
                        model=model,
                        ocr_mode=ocr_mode,
                        auto_next=auto_next
                    )
                
            except Exception as e:
                self._log(f"答题过程出错: {str(e)}")
            
            finally:
                # 调用停止回调
                if stop_callback:
                    stop_callback()
        
        # 创建并启动答题线程
        self._answering_thread = threading.Thread(target=answering_thread, daemon=True)
        self._answering_thread.start()
    
    def _answering_loop_normal_mode(self, region: tuple, option_positions: dict,
                                    next_button_pos: tuple, interval: float,
                                    total_questions: int, model: str,
                                    ocr_mode: str, auto_next: bool) -> None:
        """
        普通模式答题循环（内部方法）
        
        固定区域答题，每题一个屏幕。
        """
        self._log("开始答题...")
        
        # 循环回答每个题目
        for i in range(1, total_questions + 1):
            # 检查停止标志
            if self._stop_flag:
                self._log("答题已停止")
                break
            
            # 判断是否为最后一题
            is_last = (i == total_questions)
            
            # 回答单个题目
            try:
                self._answer_single_question(
                    question_num=i,
                    region=region,
                    option_positions=option_positions,
                    next_button_pos=next_button_pos,
                    model=model,
                    ocr_mode=ocr_mode,
                    auto_next=auto_next,
                    is_last=is_last
                )
            except Exception as e:
                self._log(f"第 {i} 题出错: {str(e)}")
                # 继续下一题
                continue
            
            # 等待间隔时间（除非是最后一题）
            if not is_last and not self._stop_flag:
                time.sleep(interval)
        
        # 答题完成
        if not self._stop_flag:
            self._log(f"答题完成！共完成 {total_questions} 题")
    
    def _answering_loop_scroll_mode(self, region: tuple, option_positions: dict,
                                    next_button_pos: tuple, interval: float,
                                    total_questions: int, model: str,
                                    ocr_mode: str, auto_next: bool,
                                    scroll_overlap: int, scroll_delay: float) -> None:
        """
        滚动模式答题循环（内部方法）
        
        长卷子答题，需要滚动页面。
        """
        self._log("开始答题（滚动模式）...")
        
        # 计算滚动中心点（截图区域的中心）
        x1, y1, x2, y2 = region
        scroll_center = ((x1 + x2) // 2, (y1 + y2) // 2)
        region_height = y2 - y1
        
        # 已答题目集合
        answered_questions = set()
        
        # 循环直到答完所有题目
        while len(answered_questions) < total_questions:
            # 检查停止标志
            if self._stop_flag:
                self._log("答题已停止")
                break
            
            # 1. 截取当前区域
            try:
                screenshot = self.screenshot_manager.capture_region(region)
                self._log(f"截图成功，已答 {len(answered_questions)}/{total_questions} 题")
            except Exception as e:
                self._log(f"截图失败: {str(e)}")
                break
            
            # 2. OCR 识别（必须使用高精度模式获取位置信息）
            try:
                if ocr_mode != "accurate_basic":
                    self._log("警告：滚动模式需要使用高精度 OCR 模式")
                    ocr_mode = "accurate_basic"
                
                ocr_result = self.ocr_service.recognize_text(screenshot, mode=ocr_mode)
                
                if not isinstance(ocr_result, dict):
                    self._log("OCR 结果格式错误，需要高精度模式")
                    break
                
                question_text = ocr_result['text']
                words_result = ocr_result['words_result']
                
            except Exception as e:
                self._log(f"OCR 识别失败: {str(e)}")
                break
            
            # 3. 提取题号
            question_numbers = self._extract_question_numbers(words_result)
            self._log(f"识别到题号: {sorted(question_numbers.keys())}")
            
            if not question_numbers:
                self._log("未识别到题号，尝试滚动...")
                # 如果没有识别到题号，滚动默认距离
                scroll_distance = region_height - scroll_overlap
                self._scroll_page(scroll_distance, scroll_center, scroll_delay)
                continue
            
            # 4. 找出当前区域内未答的题目
            current_questions = sorted(question_numbers.keys())
            unanswered_in_view = [q for q in current_questions if q not in answered_questions]
            
            if not unanswered_in_view:
                self._log("当前区域内的题目已全部回答，滚动到下一区域...")
                # 计算滚动距离
                scroll_distance = self._calculate_scroll_distance(
                    question_numbers, region_height, scroll_overlap
                )
                self._scroll_page(scroll_distance, scroll_center, scroll_delay)
                continue
            
            # 5. 回答当前区域内的未答题目
            for question_num in unanswered_in_view:
                # 检查停止标志
                if self._stop_flag:
                    break
                
                # 检查是否已达到总题数
                if len(answered_questions) >= total_questions:
                    break
                
                try:
                    # 提取选项位置（如果需要）
                    if option_positions is None:
                        option_positions_temp = self._extract_option_positions(words_result, region)
                    else:
                        option_positions_temp = option_positions
                    
                    # AI 分析答案
                    answer = self.ai_service.analyze_question(question_text, model=model)
                    self._log(f"第 {question_num} 题：AI 分析完成，答案：{answer}")
                    
                    # 解析并点击答案
                    answer_options = self.parse_answer(answer)
                    self._log(f"第 {question_num} 题：解析答案：{answer_options}")
                    
                    for option in answer_options:
                        if option in option_positions_temp:
                            x, y = option_positions_temp[option]
                            self.click_position(x, y)
                            self._log(f"第 {question_num} 题：点击选项 {option} ({x}, {y})")
                        else:
                            self._log(f"第 {question_num} 题：警告 - 选项 {option} 未找到位置")
                    
                    # 标记为已答
                    answered_questions.add(question_num)
                    self._log(f"第 {question_num} 题：已完成")
                    
                    # 等待间隔
                    if not self._stop_flag:
                        time.sleep(interval)
                    
                except Exception as e:
                    self._log(f"第 {question_num} 题出错: {str(e)}")
                    # 标记为已答，避免重复尝试
                    answered_questions.add(question_num)
                    continue
            
            # 6. 如果还有未答题目，滚动到下一区域
            if len(answered_questions) < total_questions:
                scroll_distance = self._calculate_scroll_distance(
                    question_numbers, region_height, scroll_overlap
                )
                self._scroll_page(scroll_distance, scroll_center, scroll_delay)
        
        # 答题完成
        if not self._stop_flag:
            self._log(f"答题完成！共完成 {len(answered_questions)} 题")
    
    def stop_answering(self) -> None:
        """
        停止答题循环
        
        设置停止标志，答题线程会在当前题目完成后停止。
        """
        self._stop_flag = True
        self._log("正在停止答题...")
    
    def _answer_single_question(self, question_num: int, region: tuple,
                                option_positions: dict, next_button_pos: tuple,
                                model: str, ocr_mode: str, auto_next: bool,
                                is_last: bool) -> None:
        """
        回答单个题目（内部方法）
        
        执行完整的单题答题流程：
        1. 截图
        2. OCR 识别
        3. AI 分析
        4. 点击答案
        5. 点击下一题（如果不是最后一题且未启用自动跳转）
        
        Args:
            question_num: 题目编号
            region: 截图区域
            option_positions: 选项位置
            next_button_pos: 下一题按钮位置
            model: AI 模型
            ocr_mode: OCR 模式
            auto_next: 是否自动跳转（点击选项后自动跳转，无需点击下一题按钮）
            is_last: 是否为最后一题
            
        Raises:
            Exception: 任何步骤失败时抛出异常
        """
        self._log(f"正在处理第 {question_num} 题...")
        
        # 1. 截图
        try:
            screenshot = self.screenshot_manager.capture_region(region)
            self._log(f"第 {question_num} 题：截图成功")
        except Exception as e:
            raise Exception(f"截图失败: {str(e)}")
        
        # 2. OCR 识别
        try:
            ocr_result = self.ocr_service.recognize_text(screenshot, mode=ocr_mode)
            
            # 提取文字内容和位置信息
            if isinstance(ocr_result, dict):
                # 高精度模式：返回字典
                question_text = ocr_result['text']
                words_result = ocr_result['words_result']
                self._log(f"第 {question_num} 题：OCR 识别成功（高精度模式）")
                
                # 如果没有手动标记选项位置，从 OCR 结果中自动提取
                if option_positions is None:
                    option_positions = self._extract_option_positions(words_result, region)
                    self._log(f"第 {question_num} 题：自动提取选项位置：{list(option_positions.keys())}")
            else:
                # 基础模式：返回字符串
                question_text = ocr_result
                self._log(f"第 {question_num} 题：OCR 识别成功（基础模式）")
            
            self._log(f"题目内容：{question_text[:50]}...")  # 只显示前50个字符
        except Exception as e:
            raise Exception(f"OCR 识别失败: {str(e)}")
        
        # 3. AI 分析
        try:
            answer = self.ai_service.analyze_question(question_text, model=model)
            self._log(f"第 {question_num} 题：AI 分析完成，答案：{answer}")
        except Exception as e:
            raise Exception(f"AI 分析失败: {str(e)}")
        
        # 4. 解析答案并点击
        try:
            answer_options = self.parse_answer(answer)
            self._log(f"第 {question_num} 题：解析答案：{answer_options}")
            
            # 点击每个选项
            for option in answer_options:
                if option in option_positions:
                    x, y = option_positions[option]
                    self.click_position(x, y)
                    self._log(f"第 {question_num} 题：点击选项 {option} ({x}, {y})")
                else:
                    self._log(f"第 {question_num} 题：警告 - 选项 {option} 未标记位置")
        except Exception as e:
            raise Exception(f"点击答案失败: {str(e)}")
        
        # 5. 点击下一题按钮（如果不是最后一题且未启用自动跳转）
        if not is_last and not auto_next and next_button_pos:
            try:
                x, y = next_button_pos
                self.click_position(x, y, delay=0.5)
                self._log(f"第 {question_num} 题：点击下一题按钮")
            except Exception as e:
                raise Exception(f"点击下一题按钮失败: {str(e)}")
    
    def _log(self, message: str) -> None:
        """
        记录日志（内部方法）
        
        如果设置了日志回调函数，则调用它。
        
        Args:
            message: 日志消息
        """
        if self._log_callback:
            self._log_callback(message)
    
    @staticmethod
    def click_position(x: int, y: int, delay: float = 0.3) -> None:
        """
        点击屏幕坐标
        
        使用 pyautogui 点击指定的屏幕坐标，点击后等待指定的延迟时间。
        
        Args:
            x: X 坐标
            y: Y 坐标
            delay: 点击后延迟时间（秒），默认 0.3 秒
        """
        try:
            # 使用 pyautogui 点击坐标
            pyautogui.click(x, y)
            
            # 等待延迟时间
            if delay > 0:
                time.sleep(delay)
                
        except Exception as e:
            raise AutomationException(f"点击坐标 ({x}, {y}) 失败: {str(e)}")
    
    @staticmethod
    def parse_answer(answer: str) -> list:
        """
        解析答案字符串为选项列表
        
        支持多种答案格式：
        - 单选：'A' -> ['A']
        - 多选：'A,C' 或 'A, C' -> ['A', 'C']
        - 判断题：'对' -> ['对'], '错' -> ['错']
        
        Args:
            answer: AI 返回的答案（如 "A"、"A,C"、"对"）
            
        Returns:
            选项列表（如 ['A']、['A', 'C']、['对']）
        """
        if not answer:
            return []
        
        # 去除首尾空白
        answer = answer.strip()
        
        # 如果包含逗号，说明是多选题
        if ',' in answer:
            # 按逗号分割，去除每个选项的空白
            options = [opt.strip() for opt in answer.split(',')]
            # 过滤掉空字符串
            options = [opt for opt in options if opt]
            return options
        else:
            # 单选或判断题，直接返回列表
            return [answer]

    def _extract_option_positions(self, words_result: list, region: tuple) -> dict:
        """
        从 OCR 结果中提取选项位置（内部方法）
        
        识别选项标记（A、B、C、D 或 对、错）并计算其屏幕坐标。
        
        Args:
            words_result: OCR 返回的文字结果列表，每项包含 'words' 和 'location'
            region: 截图区域 (x1, y1, x2, y2)，用于计算绝对坐标
            
        Returns:
            选项位置字典 {'A': (x, y), 'B': (x, y), ...}
        """
        option_positions = {}
        option_markers = ['A', 'B', 'C', 'D', 'E', 'F', '对', '错']
        
        x1, y1, x2, y2 = region
        
        for item in words_result:
            text = item['words'].strip()
            location = item['location']
            
            # 检查是否为选项标记
            # 可能的格式：'A'、'A.'、'A、'、'A）'等
            for marker in option_markers:
                if text == marker or text.startswith(marker + '.') or \
                   text.startswith(marker + '、') or text.startswith(marker + '）') or \
                   text.startswith(marker + ')'):
                    # 计算选项的中心点（相对于截图区域的绝对坐标）
                    center_x = x1 + location['left'] + location['width'] // 2
                    center_y = y1 + location['top'] + location['height'] // 2
                    option_positions[marker] = (center_x, center_y)
                    break
        
        return option_positions

    def _extract_question_numbers(self, words_result: list) -> dict:
        """
        从 OCR 结果中提取题号及其位置（内部方法）
        
        识别题号标记（1. 2. 3. 或 1、2、3、等）并记录其 Y 坐标。
        
        Args:
            words_result: OCR 返回的文字结果列表，每项包含 'words' 和 'location'
            
        Returns:
            题号字典 {1: {'y': 120}, 2: {'y': 350}, ...}
        """
        import re
        
        question_numbers = {}
        
        for item in words_result:
            text = item['words'].strip()
            location = item['location']
            
            # 尝试匹配各种题号格式
            # 格式1: "1."、"2."、"3."
            match = re.match(r'^(\d+)\.$', text)
            if match:
                num = int(match.group(1))
                question_numbers[num] = {'y': location['top']}
                continue
            
            # 格式2: "1、"、"2、"、"3、"
            match = re.match(r'^(\d+)、$', text)
            if match:
                num = int(match.group(1))
                question_numbers[num] = {'y': location['top']}
                continue
            
            # 格式3: "（1）"、"（2）"、"（3）"
            match = re.match(r'^[（(](\d+)[）)]$', text)
            if match:
                num = int(match.group(1))
                question_numbers[num] = {'y': location['top']}
                continue
            
            # 格式4: "1）"、"2）"、"3）"
            match = re.match(r'^(\d+)[）)]$', text)
            if match:
                num = int(match.group(1))
                question_numbers[num] = {'y': location['top']}
                continue
            
            # 格式5: 文本开头包含题号，如 "1.下列选项..."
            match = re.match(r'^(\d+)[.、）)]', text)
            if match:
                num = int(match.group(1))
                if num not in question_numbers:  # 避免重复
                    question_numbers[num] = {'y': location['top']}
                continue
        
        return question_numbers
    
    def _calculate_scroll_distance(self, question_numbers: dict, region_height: int, 
                                   overlap: int) -> int:
        """
        计算智能滚动距离（内部方法）
        
        基于当前识别到的题号位置，计算合适的滚动距离。
        
        Args:
            question_numbers: 题号字典 {1: {'y': 120}, 2: {'y': 350}, ...}
            region_height: 截图区域高度
            overlap: 重叠区域高度（像素），防止漏题
            
        Returns:
            滚动距离（像素），负数表示向下滚动
        """
        if not question_numbers:
            # 如果没有识别到题号，使用默认滚动距离
            return region_height - overlap
        
        # 找到最后一道题的 Y 坐标
        last_question_y = max(q['y'] for q in question_numbers.values())
        
        # 滚动距离 = 最后一题位置 - 重叠区域
        scroll_distance = last_question_y - overlap
        
        # 确保至少滚动一定距离（区域高度的一半）
        min_scroll = region_height // 2
        scroll_distance = max(scroll_distance, min_scroll)
        
        # 确保不超过区域高度
        scroll_distance = min(scroll_distance, region_height - overlap)
        
        return scroll_distance
    
    def _scroll_page(self, distance: int, scroll_center: tuple, delay: float) -> None:
        """
        执行页面滚动（内部方法）
        
        在指定位置执行滚动操作。
        
        Args:
            distance: 滚动距离（像素），正数向下滚动
            scroll_center: 滚动中心点坐标 (x, y)
            delay: 滚动后等待时间（秒）
        """
        try:
            # 移动鼠标到滚动区域中心
            pyautogui.moveTo(scroll_center[0], scroll_center[1], duration=0.2)
            
            # 计算滚动次数（每次滚动约 120 像素）
            # pyautogui.scroll() 的参数：正数向上滚动，负数向下滚动
            scroll_clicks = -(distance // 120)
            
            if scroll_clicks != 0:
                # 执行滚动
                pyautogui.scroll(scroll_clicks)
                self._log(f"滚动页面：{distance} 像素（{scroll_clicks} 次滚动）")
                
                # 等待页面稳定
                time.sleep(delay)
            
        except Exception as e:
            raise AutomationException(f"滚动页面失败: {str(e)}")
