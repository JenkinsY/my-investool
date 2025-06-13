"""
停机坪策略

条件:
1）最近15日有涨幅大于9.5%，且必须是放量上涨。
2）紧接的下个交易日必须高开，收盘价必须上涨，且与开盘价不能大于等于相差3%。
3）接下2、3个交易日必须高开，收盘价必须上涨，且与开盘价不能大于等于相差3%，且每天涨跌幅在5%间。
"""

import pandas as pd
import numpy as np
import sys
import os

# 导入放量上涨策略
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from strategies.volume_up import is_volume_up

def is_landing_platform(df):
    """
    判断是否符合停机坪策略
    
    Parameters:
    -----------
    df : pandas.DataFrame
        股票历史数据，需要包含计算好的技术指标
    
    Returns:
    --------
    bool
        是否符合停机坪策略
    """
    # 如果数据不足，返回False
    if df.empty or len(df) < 20:
        return False

    # 复制最后20天的数据进行分析
    recent_df = df.iloc[-20:].copy()
    
    # 找出15日内涨幅大于9.5%的交易日
    big_up_days = recent_df[(recent_df['pct_chg'] > 9.5)]
    
    # 如果没有符合条件的大涨日，则返回False
    if big_up_days.empty:
        return False
    
    # 对每个大涨日进行分析
    for index, big_day in big_up_days.iterrows():
        # 获取大涨日的位置
        big_day_loc = recent_df.index.get_loc(index)
        
        # 如果大涨日后面没有足够的交易日，则跳过
        if big_day_loc + 3 >= len(recent_df):
            continue
        
        # 检查大涨日是否是放量上涨
        # 构造一个临时DataFrame来检查
        temp_df = df[df.index <= index].iloc[-10:]
        if not is_volume_up(temp_df):
            continue
        
        # 检查紧接的下个交易日
        next_day = recent_df.iloc[big_day_loc + 1]
        
        # 2）紧接的下个交易日必须高开，收盘价必须上涨，且与开盘价不能大于等于相差3%
        if (next_day['open'] <= big_day['close'] or  # 高开
            next_day['close'] <= next_day['open'] or  # 收盘上涨
            abs(next_day['close'] - next_day['open']) / next_day['open'] >= 0.03):  # 开盘与收盘价差小于3%
            continue
        
        # 检查接下来的2、3个交易日
        valid_platform = True
        for i in range(2, 4):  # 第2、3个交易日
            if big_day_loc + i >= len(recent_df):
                valid_platform = False
                break
                
            day = recent_df.iloc[big_day_loc + i]
            prev_day = recent_df.iloc[big_day_loc + i - 1]
            
            # 3）接下2、3个交易日必须高开，收盘价必须上涨，且与开盘价不能大于等于相差3%，且每天涨跌幅在5%间
            if (day['open'] <= prev_day['close'] or  # 高开
                day['close'] <= day['open'] or  # 收盘上涨
                abs(day['close'] - day['open']) / day['open'] >= 0.03 or  # 开盘与收盘价差小于3%
                abs(day['pct_chg']) > 5):  # 涨跌幅在5%间
                valid_platform = False
                break
        
        # 如果找到符合条件的停机坪，返回True
        if valid_platform:
            return True
    
    # 没有符合条件的停机坪
    return False 