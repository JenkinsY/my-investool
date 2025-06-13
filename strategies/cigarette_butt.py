"""
烟蒂股策略

条件:
1）市净率 PB < 0.5
2）市值 < 净流动资产 NCAV
3）资产负债率 < 50%
4）正向经营现金流
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

def is_cigarette_butt(symbol):
    """
    判断是否符合烟蒂股策略
    
    Parameters:
    -----------
    symbol : str
        股票代码
    
    Returns:
    --------
    bool
        是否符合烟蒂股策略
    """
    try:
        # 添加随机延迟，防止频繁请求被限制
        time.sleep(random.uniform(0.1, 0.5))
        
        # 获取基本面数据
        fundamentals = get_stock_fundamentals(symbol)
        
        # 如果数据为空，返回False
        if not fundamentals:
            return False
            
        # 1. 市净率 PB < 0.5
        if ('indicator' not in fundamentals or 
            fundamentals['indicator'].empty or 
            'pb' not in fundamentals['indicator'].columns):
            return False
        
        # 使用最新的数据（最后一行）
        latest_indicator = fundamentals['indicator'].iloc[-1]
        if latest_indicator['pb'] >= 0.5:
            return False
            
        # 获取资产负债表数据
        if ('balance_sheet' not in fundamentals or 
            fundamentals['balance_sheet'].empty):
            return False
            
        # 获取最新的资产负债表数据
        if len(fundamentals['balance_sheet']) > 0:
            balance = fundamentals['balance_sheet'].iloc[0]
        else:
            return False
        
        # 查找资产负债表中是否有所需的列
        required_balance_cols = ['TOTAL_ASSETS', 'TOTAL_CURRENT_ASSETS', 'TOTAL_LIABILITIES']
        
        # 检查列名（大小写不敏感）
        balance_cols = [col.upper() for col in fundamentals['balance_sheet'].columns]
        
        # 找到实际的列名
        total_assets_col = None
        total_current_assets_col = None
        total_liabilities_col = None
        
        for col in fundamentals['balance_sheet'].columns:
            if 'TOTAL_ASSET' in col.upper() and 'CURRENT' not in col.upper():
                total_assets_col = col
            elif 'CURRENT_ASSET' in col.upper() and 'TOTAL' in col.upper():
                total_current_assets_col = col
            elif 'LIABILIT' in col.upper() and 'TOTAL' in col.upper():
                total_liabilities_col = col
        
        if not total_assets_col or not total_current_assets_col or not total_liabilities_col:
            print(f"股票 {symbol} 缺少资产负债表必要的列")
            return False
            
        # 2. 市值 < 净流动资产 NCAV
        # 净流动资产 = 流动资产 - 总负债
        # 计算净流动资产
        ncav = balance[total_current_assets_col] - balance[total_liabilities_col]
        
        # 获取市值
        if 'total_mv' in latest_indicator:
            market_cap = latest_indicator['total_mv']
        else:
            # 如果没有直接的市值数据，用股价乘以总股本计算
            print(f"股票 {symbol} 没有市值数据，无法检查NCAV条件")
            return False
        
        # 市值 < 净流动资产
        if market_cap >= ncav:
            return False
            
        # 3. 资产负债率 < 50%
        # 资产负债率 = 总负债 / 总资产
        if balance[total_liabilities_col] / balance[total_assets_col] >= 0.5:
            return False
            
        # 4. 正向经营现金流
        if ('cash_flow' not in fundamentals or 
            fundamentals['cash_flow'].empty):
            return False
        
        # 查找现金流量表中是否有所需的列
        cash_flow_col = None
        for col in fundamentals['cash_flow'].columns:
            if 'CASH_FLOW' in col.upper() and 'OPERATE' in col.upper():
                cash_flow_col = col
                break
        
        if not cash_flow_col:
            print(f"股票 {symbol} 缺少现金流量表必要的列")
            return False
        
        # 获取最新的现金流量表数据
        if len(fundamentals['cash_flow']) > 0:
            cash_flow = fundamentals['cash_flow'].iloc[0]
            if cash_flow[cash_flow_col] <= 0:
                return False
        else:
            return False
            
        # 所有条件都满足
        return True
    except Exception as e:
        print(f"检查股票 {symbol} 烟蒂股条件时出错: {e}")
        return False 