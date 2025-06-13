"""
配置加载器模块，用于加载和验证用户配置
"""

import os
import json
import logging
import copy
from pathlib import Path

# 导入默认配置
from config import CONFIG as DEFAULT_CONFIG

# 获取日志记录器
logger = logging.getLogger(__name__)

class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, config_file=None):
        """
        初始化配置加载器
        
        Parameters:
        -----------
        config_file : str
            配置文件路径，默认为None，表示使用默认配置
        """
        # 默认配置
        self.default_config = copy.deepcopy(DEFAULT_CONFIG)
        
        # 用户配置
        self.user_config = {}
        
        # 最终配置（默认配置 + 用户配置）
        self.config = copy.deepcopy(self.default_config)
        
        # 如果指定了配置文件，则加载用户配置
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
    
    def load_config(self, config_file):
        """
        加载用户配置
        
        Parameters:
        -----------
        config_file : str
            配置文件路径
        """
        try:
            # 读取用户配置文件
            with open(config_file, 'r', encoding='utf-8') as f:
                self.user_config = json.load(f)
            
            # 合并配置
            self._merge_config()
            
            logger.info(f"从 {config_file} 加载配置成功")
        except Exception as e:
            logger.error(f"加载配置文件 {config_file} 失败: {e}")
            # 出错时使用默认配置
            self.config = copy.deepcopy(self.default_config)
    
    def _merge_config(self):
        """合并默认配置和用户配置"""
        # 使用深拷贝确保原始默认配置不被修改
        merged_config = copy.deepcopy(self.default_config)
        
        # 递归合并配置
        self._merge_dict(merged_config, self.user_config)
        
        # 更新最终配置
        self.config = merged_config
    
    def _merge_dict(self, dict1, dict2):
        """
        递归合并两个字典
        
        Parameters:
        -----------
        dict1 : dict
            目标字典，将被修改
        dict2 : dict
            源字典，不会被修改
        """
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                # 如果两个都是字典，递归合并
                self._merge_dict(dict1[key], value)
            else:
                # 否则直接覆盖
                dict1[key] = value
    
    def save_config(self, config_file):
        """
        保存当前配置到文件
        
        Parameters:
        -----------
        config_file : str
            配置文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # 写入配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"配置保存到 {config_file} 成功")
        except Exception as e:
            logger.error(f"保存配置到 {config_file} 失败: {e}")
    
    def save_default_config(self, config_file):
        """
        保存默认配置到文件
        
        Parameters:
        -----------
        config_file : str
            配置文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # 写入配置文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.default_config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"默认配置保存到 {config_file} 成功")
        except Exception as e:
            logger.error(f"保存默认配置到 {config_file} 失败: {e}")
    
    def get_config(self):
        """
        获取当前配置
        
        Returns:
        --------
        dict
            当前配置
        """
        return self.config
    
    def get_base_config(self):
        """获取基础配置"""
        return self.config["base"]
    
    def get_strategy_config(self):
        """获取策略配置"""
        return self.config["strategy"]
    
    def get_data_config(self):
        """获取数据配置"""
        return self.config["data"]
    
    def get_active_strategy(self):
        """获取当前激活的策略"""
        return self.config["strategy"]["active_strategy"]
    
    def get_strategy_params(self, strategy_name):
        """
        获取指定策略的参数
        
        Parameters:
        -----------
        strategy_name : str
            策略名称
            
        Returns:
        --------
        dict
            策略参数
        """
        if strategy_name in self.config["strategy"]:
            return self.config["strategy"][strategy_name]
        return {}


# 创建默认的配置加载器实例
config_loader = ConfigLoader()

# 导出配置获取函数
def get_config():
    """获取当前配置"""
    return config_loader.get_config()

def get_base_config():
    """获取基础配置"""
    return config_loader.get_base_config()

def get_strategy_config():
    """获取策略配置"""
    return config_loader.get_strategy_config()

def get_data_config():
    """获取数据配置"""
    return config_loader.get_data_config()

def load_config(config_file):
    """加载指定的配置文件"""
    config_loader.load_config(config_file)
    return config_loader.get_config()

def save_default_config(config_file="config.json"):
    """保存默认配置到文件"""
    config_loader.save_default_config(config_file) 