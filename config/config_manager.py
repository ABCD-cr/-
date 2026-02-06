"""
配置管理模块

此模块负责应用配置和 API 凭证的持久化存储。
"""

import json
import os
from typing import Any, Optional
from utils.exceptions import ConfigException


class ConfigManager:
    """
    配置管理器类
    
    负责加载、保存和管理应用配置。
    """
    
    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 "config.json"
        """
        self.config_file = config_file
        self._config = self.load_config()
    
    def load_config(self) -> dict:
        """
        加载配置文件
        
        Returns:
            dict: 包含所有配置项的字典
                {
                    'api_key': str,
                    'baidu_api_key': str,
                    'baidu_secret_key': str
                }
        """
        # 如果配置文件不存在，返回空字典
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config if isinstance(config, dict) else {}
        except json.JSONDecodeError:
            # 配置文件格式错误，返回空字典
            return {}
        except Exception as e:
            # 其他读取错误，返回空字典
            return {}
    
    def save_config(self, config: dict) -> None:
        """
        保存配置到文件
        
        Args:
            config: 配置字典
            
        Raises:
            ConfigException: 配置文件写入失败时抛出
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            # 更新内存中的配置
            self._config = config
        except Exception as e:
            raise ConfigException(f"配置文件写入失败: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self._config[key] = value
        # 自动保存到文件
        self.save_config(self._config)
    
    @staticmethod
    def mask_api_key(key: str) -> str:
        """
        遮蔽 API Key 显示（前4位+星号+后4位）
        
        Args:
            key: 完整的 API Key
            
        Returns:
            遮蔽后的 API Key
        """
        if not key or not isinstance(key, str):
            return ""
        
        key_len = len(key)
        
        # 如果 API Key 长度小于等于 8，只显示前几位
        if key_len <= 8:
            if key_len <= 4:
                return "*" * key_len
            else:
                return key[:4] + "*" * (key_len - 4)
        
        # 长度大于 8：前4位 + 星号 + 后4位
        prefix = key[:4]
        suffix = key[-4:]
        middle_len = key_len - 8
        
        return f"{prefix}{'*' * middle_len}{suffix}"
