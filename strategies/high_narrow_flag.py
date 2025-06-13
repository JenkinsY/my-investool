"""
高而窄的旗形策略

条件:
1）必须至少上市交易60日。
2）当日收盘价/之前24~10日的最低价>=1.9。
3）之前24~10日必须连续两天涨幅大于等于9.5%。
"""

import pandas as pd
import numpy as np

def is_high_narrow_flag(df):
    """
    判断是否符合高而窄的旗形策略
    
    Parameters:
    -----------
    df : pandas.DataFrame
        股票历史数据，需要包含计算好的技术指标
    
    Returns:
    --------
    bool
        是否符合高而窄的旗形策略
    """
    # 如果数据不足，返回False
    if df.empty or len(df) < 60:  # 条件1：至少上市交易60日
        return False
    
    # 获取最新交易日数据
    latest = df.iloc[-1]
    
    # 获取之前24~10日的数据
    period_start = -24
    period_end = -10
    period_data = df.iloc[period_start:period_end]
    
    # 如果区间数据不足，返回False
    if len(period_data) < abs(period_start - period_end):
        return False
    
    # 条件2：当日收盘价/之前24~10日的最低价>=1.9
    period_lowest = period_data['low'].min()
    if latest['close'] / period_lowest < 1.9:
        return False
    
    # 条件3：之前24~10日必须连续两天涨幅大于等于9.5%
    # 在区间内找出涨幅大于等于9.5%的交易日
    big_up_days = period_data[period_data['pct_chg'] >= 9.5]
    
    # 如果大涨日少于2天，返回False
    if len(big_up_days) < 2:
        return False
    
    # 检查是否存在连续两天涨幅大于等于9.5%的情况
    for i in range(len(period_data) - 1):
        if period_data.iloc[i]['pct_chg'] >= 9.5 and period_data.iloc[i + 1]['pct_chg'] >= 9.5:
            return True
    
    return False 