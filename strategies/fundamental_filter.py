"""
股票基本面选股策略

条件:
1）市盈率小于等于20，且大于0。
2）市净率小于等于10。
3）净资产收益率大于等于15。
"""

import pandas as pd
import numpy as np
import time
import random
import sys
import os

# 导入工具模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.stock_data import get_stock_fundamentals

def is_good_fundamental(symbol):
    """
    判断是否符合基本面选股策略
    
    Parameters:
    -----------
    symbol : str
        股票代码
    
    Returns:
    --------
    bool
        是否符合基本面选股策略
    """
    try:
        # 添加随机延迟，防止频繁请求被限制
        time.sleep(random.uniform(0.1, 0.5))
        
        # 获取基本面数据
        fundamentals = get_stock_fundamentals(symbol)
        
        # 如果数据为空，返回False
        if not fundamentals or 'indicator' not in fundamentals or fundamentals['indicator'].empty:
            return False
        
        # 获取最新的指标数据
        indicator = fundamentals['indicator']
        
        # 检查是否有必要的列
        required_columns = ['trade_date', 'pe', 'pb', 'roe']
        missing_columns = [col for col in required_columns if col not in indicator.columns]
        if missing_columns:
            print(f"股票 {symbol} 指标数据缺少必要的列: {missing_columns}")
            return False
        
        # 使用最新的数据（最后一行）
        latest_indicator = indicator.iloc[-1]
        
        # 1. 市盈率小于等于20，且大于0
        if not (0 < latest_indicator['pe'] <= 20):
            return False
        
        # 2. 市净率小于等于10
        if not (0 < latest_indicator['pb'] <= 10):
            return False
        
        # 3. 净资产收益率大于等于15
        if latest_indicator['roe'] < 15:
            return False
        
        # 所有条件都满足
        return True
    except Exception as e:
        print(f"检查股票 {symbol} 基本面数据时出错: {e}")
        return False 