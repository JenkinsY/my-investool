import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据获取模块
from utils.stock_data import get_stock_list, get_stock_history, get_stock_fundamentals, calculate_technical_indicators

def test_stock_list():
    """测试获取股票列表"""
    print("=== 测试获取股票列表 ===")
    stock_list = get_stock_list()
    print(f"获取到 {len(stock_list)} 只股票")
    print("前5只股票:")
    print(stock_list.head())
    print()

def test_stock_history():
    """测试获取股票历史数据"""
    print("=== 测试获取股票历史数据 ===")
    # 获取当前日期
    now = datetime.now()
    end_date = now.strftime("%Y%m%d")
    
    # 计算30天前的日期
    start_date = (now - timedelta(days=30)).strftime("%Y%m%d")
    
    # 测试几只常见股票
    test_symbols = ["000001", "600000", "300059"]
    
    for symbol in test_symbols:
        print(f"获取 {symbol} 的历史数据:")
        df = get_stock_history(symbol, start_date, end_date)
        if not df.empty:
            print(f"获取到 {len(df)} 条数据")
            print("数据列:", list(df.columns))
            print("前2条数据:")
            print(df.head(2))
        else:
            print(f"没有获取到 {symbol} 的历史数据")
        print()
        
        # 测试技术指标计算
        if not df.empty:
            print(f"计算 {symbol} 的技术指标:")
            tech_df = calculate_technical_indicators(df)
            print(f"计算后有 {len(tech_df.columns)} 个指标")
            print("指标列:", list(tech_df.columns))
            print()

def test_stock_fundamentals():
    """测试获取股票基本面数据"""
    print("=== 测试获取股票基本面数据 ===")
    # 测试几只常见股票
    test_symbols = ["000001", "600000", "300059"]
    
    for symbol in test_symbols:
        print(f"获取 {symbol} 的基本面数据:")
        fundamentals = get_stock_fundamentals(symbol)
        
        print("资产负债表列:", list(fundamentals['balance_sheet'].columns) if 'balance_sheet' in fundamentals and not fundamentals['balance_sheet'].empty else "空")
        print("利润表列:", list(fundamentals['income_statement'].columns) if 'income_statement' in fundamentals and not fundamentals['income_statement'].empty else "空")
        print("现金流量表列:", list(fundamentals['cash_flow'].columns) if 'cash_flow' in fundamentals and not fundamentals['cash_flow'].empty else "空")
        print("估值指标列:", list(fundamentals['indicator'].columns) if 'indicator' in fundamentals and not fundamentals['indicator'].empty else "空")
        print()

if __name__ == "__main__":
    # 测试股票列表获取
    test_stock_list()
    
    # 测试股票历史数据获取
    test_stock_history()
    
    # 测试股票基本面数据获取
    test_stock_fundamentals() 