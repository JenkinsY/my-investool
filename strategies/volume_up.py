"""
放量上涨策略
"""

import pandas as pd
import numpy as np
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)

def is_volume_up(df, min_pct_change=0.0, max_pct_change=2.0, min_amount=200000000, volume_ratio=2.0):
    """
    判断是否符合放量上涨策略
    
    策略说明：
    1. 当日比前一天上涨小于2%（参数可调整）或收盘价小于开盘价
    2. 当日成交额不低于2亿（参数可调整）
    3. 当日成交量/5日平均成交量>=2（参数可调整）
    
    Parameters:
    -----------
    df : pandas.DataFrame
        股票历史数据
    min_pct_change : float
        最小涨幅，默认为0.0
    max_pct_change : float
        最大涨幅，默认为2.0
    min_amount : float
        最小成交额，默认为2亿
    volume_ratio : float
        成交量比值，默认为2.0
    
    Returns:
    --------
    bool
        是否符合放量上涨策略
    """
    # 确保数据不为空且包含足够的行
    if df.empty or len(df) < 6:
        return False
    
    try:
        # 获取最新一天的数据
        latest_day = df.iloc[-1]
        
        # 条件1: 当日比前一天上涨小于max_pct_change%或收盘价小于开盘价
        condition1 = (latest_day['pct_chg'] >= min_pct_change and latest_day['pct_chg'] <= max_pct_change) or latest_day['close'] < latest_day['open']
        
        # 条件2: 当日成交额不低于min_amount
        condition2 = latest_day['amount'] >= min_amount
        
        # 条件3: 当日成交量/5日平均成交量>=volume_ratio
        condition3 = latest_day['volume_ratio'] >= volume_ratio
        
        # 检查所有条件
        if condition1 and condition2 and condition3:
            return True
        
        return False
    except Exception as e:
        logger.error(f"放量上涨策略执行出错: {e}")
        return False 