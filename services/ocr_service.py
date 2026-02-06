"""
OCR 服务模块

此模块封装百度 OCR API 调用，提供图像文字识别功能。
支持两种 OCR 模式：
1. 基础模式 (general_basic) - 只返回文字内容
2. 高精度模式 (accurate_basic) - 返回文字内容和位置信息
"""

import requests
from urllib.parse import quote
from PIL import Image
from typing import Union, List, Dict
from utils.exceptions import OCRException
from utils.image_utils import image_to_base64


class OCRService:
    """
    OCR 服务类
    
    封装百度 OCR API 调用。
    支持基础模式和高精度模式。
    """
    
    # OCR 模式常量
    MODE_BASIC = "general_basic"  # 基础模式：只返回文字
    MODE_ACCURATE = "accurate_basic"  # 高精度模式：返回文字和位置
    
    def __init__(self, config_manager):
        """
        初始化 OCR 服务
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        # 为两种模式分别缓存 Access Token
        self._access_token_basic = None
        self._access_token_accurate = None
    
    def recognize_text(self, image: Image.Image, mode: str = MODE_BASIC) -> Union[str, Dict]:
        """
        识别图像中的文字
        
        Args:
            image: PIL Image 对象
            mode: OCR 模式
                  - MODE_BASIC (general_basic): 只返回文字内容（字符串）
                  - MODE_ACCURATE (accurate_basic): 返回文字和位置信息（字典）
            
        Returns:
            - 基础模式: 识别出的文字内容（多行文字用换行符分隔）
            - 高精度模式: 字典，包含 'text' 和 'words_result' 键
              {
                  'text': '完整文字内容',
                  'words_result': [
                      {
                          'words': '文字内容',
                          'location': {
                              'left': x坐标,
                              'top': y坐标,
                              'width': 宽度,
                              'height': 高度
                          }
                      },
                      ...
                  ]
              }
            
        Raises:
            OCRException: OCR 识别失败时抛出
        """
        # 验证模式
        if mode not in [self.MODE_BASIC, self.MODE_ACCURATE]:
            raise OCRException(f"不支持的 OCR 模式: {mode}")
        
        try:
            # 获取 Access Token（根据模式使用不同的凭证）
            access_token = self._get_access_token(mode)
            
            # 将图像转换为 base64
            image_base64 = self._image_to_base64(image)
            
            # 调用百度 OCR API
            url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/{mode}?access_token={access_token}"
            payload = f'image={quote(image_base64)}'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            response = requests.post(url, headers=headers, data=payload)
            result = response.json()
            
            # 检查是否有错误
            if 'error_code' in result:
                error_msg = result.get('error_msg', '未知错误')
                error_code = result.get('error_code')
                raise OCRException(f"OCR 识别失败: {error_code} - {error_msg}")
            
            # 提取识别的文字
            if 'words_result' in result:
                words_result = result['words_result']
                
                # 基础模式：只返回文字
                if mode == self.MODE_BASIC:
                    text = '\n'.join([item['words'] for item in words_result])
                    return text
                
                # 高精度模式：返回文字和位置信息
                else:
                    text = '\n'.join([item['words'] for item in words_result])
                    return {
                        'text': text,
                        'words_result': words_result
                    }
            else:
                raise OCRException(f"OCR 识别失败: 响应格式错误 - {result}")
                
        except OCRException:
            # 重新抛出 OCRException
            raise
        except requests.exceptions.RequestException as e:
            # 网络连接错误
            raise OCRException(f"网络连接失败: {str(e)}")
        except Exception as e:
            # 其他错误
            raise OCRException(f"OCR 识别失败: {str(e)}")
    
    def clear_token_cache(self) -> None:
        """
        清除缓存的 Access Token
        
        当 API 凭证更新时调用此方法。
        """
        self._access_token_basic = None
        self._access_token_accurate = None
    
    def _get_access_token(self, mode: str) -> str:
        """
        获取百度 OCR Access Token（内部方法）
        
        根据 OCR 模式使用不同的 API 凭证。
        如果已缓存 Token，直接返回；否则请求新的 Token。
        
        Args:
            mode: OCR 模式 (MODE_BASIC 或 MODE_ACCURATE)
        
        Returns:
            Access Token 字符串
            
        Raises:
            OCRException: 获取 Token 失败时抛出
        """
        # 根据模式选择对应的缓存和配置键
        if mode == self.MODE_BASIC:
            cached_token = self._access_token_basic
            api_key_name = 'baidu_basic_api_key'
            secret_key_name = 'baidu_basic_secret_key'
        else:  # MODE_ACCURATE
            cached_token = self._access_token_accurate
            api_key_name = 'baidu_accurate_api_key'
            secret_key_name = 'baidu_accurate_secret_key'
        
        # 如果已有缓存的 Token，直接返回
        if cached_token:
            return cached_token
        
        try:
            # 从配置管理器获取 API Key 和 Secret Key
            api_key = self.config_manager.get(api_key_name)
            secret_key = self.config_manager.get(secret_key_name)
            
            if not api_key or not secret_key:
                mode_name = "基础模式" if mode == self.MODE_BASIC else "高精度模式"
                raise OCRException(f"认证失败: 请检查百度 OCR {mode_name} API Key 和 Secret Key")
            
            # 请求 Access Token
            url = "https://aip.baidubce.com/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": api_key,
                "client_secret": secret_key
            }
            
            response = requests.post(url, params=params)
            result = response.json()
            
            # 检查是否有错误
            if 'error' in result:
                error_msg = result.get('error_description', result.get('error', '未知错误'))
                raise OCRException(f"认证失败: {error_msg}")
            
            # 获取 Access Token
            access_token = result.get('access_token')
            if not access_token:
                raise OCRException(f"认证失败: 无法获取 Access Token - {result}")
            
            # 缓存 Token
            if mode == self.MODE_BASIC:
                self._access_token_basic = access_token
            else:
                self._access_token_accurate = access_token
            
            return access_token
            
        except OCRException:
            # 重新抛出 OCRException
            raise
        except requests.exceptions.RequestException as e:
            # 网络连接错误
            raise OCRException(f"网络连接失败: {str(e)}")
        except Exception as e:
            # 其他错误
            raise OCRException(f"获取 Access Token 失败: {str(e)}")
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """
        将图像转换为 base64 编码（内部方法）
        
        Args:
            image: PIL Image 对象
            
        Returns:
            base64 编码的图像字符串
        """
        return image_to_base64(image, format="PNG")
