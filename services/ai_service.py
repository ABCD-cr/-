"""
AI 服务模块

此模块封装 DeepSeek AI API 调用，提供题目分析功能。
"""

from openai import OpenAI
from utils.exceptions import AIException


class AIService:
    """
    AI 服务类
    
    封装 DeepSeek AI API 调用，提供题目分析功能。
    支持 deepseek-chat 和 deepseek-reasoner 两种模型。
    """
    
    # 支持的模型列表
    SUPPORTED_MODELS = ["deepseek-chat", "deepseek-reasoner"]
    
    # DeepSeek API 基础 URL
    BASE_URL = "https://api.deepseek.com"
    
    def __init__(self, config_manager):
        """
        初始化 AI 服务
        
        Args:
            config_manager: 配置管理器实例
            
        Raises:
            AIException: 如果配置管理器为 None
        """
        if config_manager is None:
            raise AIException("配置管理器不能为 None")
        
        self.config_manager = config_manager
        self._client = None
    
    def _get_client(self):
        """
        获取 OpenAI 客户端实例（懒加载）
        
        Returns:
            OpenAI 客户端实例
            
        Raises:
            AIException: 如果 API Key 未配置
        """
        if self._client is None:
            api_key = self.config_manager.get('api_key')
            if not api_key:
                raise AIException("DeepSeek API Key 未配置")
            
            try:
                self._client = OpenAI(
                    api_key=api_key,
                    base_url=self.BASE_URL
                )
            except Exception as e:
                raise AIException(f"创建 OpenAI 客户端失败: {str(e)}")
        
        return self._client
    
    def analyze_question(self, question_text: str, model: str = "deepseek-chat") -> str:
        """
        分析题目并返回答案
        
        Args:
            question_text: 题目文字内容
            model: 使用的模型名称（"deepseek-chat" 或 "deepseek-reasoner"）
            
        Returns:
            答案选项（如 "A"、"A,C"、"对"、"错"）
            
        Raises:
            AIException: AI 分析失败时抛出
        """
        # 验证输入
        if not question_text or not isinstance(question_text, str):
            raise AIException("题目文字不能为空且必须是字符串")
        
        # 验证模型
        if model not in self.SUPPORTED_MODELS:
            raise AIException(f"不支持的模型: {model}。支持的模型: {', '.join(self.SUPPORTED_MODELS)}")
        
        try:
            # 获取客户端
            client = self._get_client()
            
            # 构建消息
            messages = self._build_messages(question_text)
            
            # 调用 API
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False
            )
            
            # 提取答案
            answer = response.choices[0].message.content.strip()
            
            if not answer:
                raise AIException("AI 返回了空答案")
            
            return answer
            
        except AIException:
            # 重新抛出 AIException
            raise
        except Exception as e:
            # 捕获其他异常并转换为 AIException
            error_msg = str(e)
            
            # 识别常见错误类型
            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                raise AIException(f"认证失败: 请检查 API Key - {error_msg}")
            elif "connection" in error_msg.lower() or "network" in error_msg.lower():
                raise AIException(f"网络连接失败: {error_msg}")
            elif "timeout" in error_msg.lower():
                raise AIException(f"请求超时: {error_msg}")
            else:
                raise AIException(f"AI 分析失败: {error_msg}")
    
    def _build_messages(self, question_text: str) -> list:
        """
        构建 API 请求消息（内部方法）
        
        构建包含系统提示词和用户问题的消息列表。
        系统提示词指导 AI 只返回答案选项，不做解释。
        
        Args:
            question_text: 题目文字
            
        Returns:
            消息列表，格式为 [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
        """
        system_prompt = "你是一个答题助手，请分析题目并给出答案。只回答选项字母或判断结果，不要解释。"
        
        user_prompt = f"题目内容：\n{question_text}\n\n请直接回答正确选项（单选回答如：A，多选回答如：A,C，判断题回答：对 或 错）"
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
        
        return messages
