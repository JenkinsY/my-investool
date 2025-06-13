import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import os
import logging
from utils.data_cache import DataCache

# 初始化日志
logger = logging.getLogger(__name__)

# 初始化缓存系统
cache = DataCache()

# API函数名映射
def get_stock_list():
    """
    获取A股股票列表，优先从缓存获取
    """
    try:
        # 先从缓存获取
        df = cache.get_stock_list()
        if df is not None and not df.empty:
            logger.info(f"从缓存获取股票列表成功，共 {len(df)} 只股票")
            return df
        
        # 如果缓存中没有，则从API获取
        logger.info("从API获取股票列表")
        stock_info_df = ak.stock_info_a_code_name()
        
        # 缓存股票列表
        if not stock_info_df.empty:
            cache.cache_stock_list(stock_info_df)
            logger.info(f"从API获取股票列表成功，共 {len(stock_info_df)} 只股票")
        
        return stock_info_df
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return pd.DataFrame()

def get_stock_history(symbol, start_date=None, end_date=None, adjust="qfq"):
    """
    获取个股历史行情数据，优先从缓存获取
    
    Parameters:
    -----------
    symbol : str
        股票代码，如 "000001"
    start_date : str
        开始日期，格式 "YYYYMMDD"，默认为None，表示取尽可能多的历史数据
    end_date : str
        结束日期，格式 "YYYYMMDD"，默认为None，表示取到今日
    adjust : str
        复权方式，"qfq"表示前复权，"hfq"表示后复权，""表示不复权
    
    Returns:
    --------
    pandas.DataFrame
        包含历史行情数据的DataFrame
    """
    try:
        # 如果未指定结束日期，则使用当前日期
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
            
        # 先从缓存获取
        df = cache.get_stock_history(symbol, start_date, end_date, adjust)
        if df is not None and not df.empty:
            logger.info(f"从缓存获取股票 {symbol} 历史数据成功")
            return df
        
        # 如果缓存中没有，则从API获取
        logger.info(f"从API获取股票 {symbol} 历史数据")
        # 添加随机延迟，防止频繁请求被限制
        time.sleep(random.uniform(0.1, 0.5))
        
        # 获取股票历史数据
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                              start_date=start_date, end_date=end_date, 
                              adjust=adjust)
        
        # 如果返回数据为空，直接返回空DataFrame
        if df.empty:
            logger.warning(f"股票 {symbol} 历史数据为空")
            return pd.DataFrame()
        
        # 标准化数据框: 重命名列为英文，便于后续处理
        column_mapping = {
            "日期": "date",
            "股票代码": "code",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "pct_chg",
            "涨跌额": "change",
            "换手率": "turnover"
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保日期列是datetime格式
        if "date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"])
        
        # 设置日期为索引
        if "date" in df.columns:
            df.set_index("date", inplace=True)
            
            # 按日期排序
            df.sort_index(inplace=True)
        
        # 缓存数据
        cache.cache_stock_history(df, symbol, start_date, end_date, adjust)
        
        return df
    except Exception as e:
        logger.error(f"获取股票 {symbol} 历史数据失败: {e}")
        return pd.DataFrame()

def get_stock_fundamentals(symbol):
    """
    获取个股基本面数据，优先从缓存获取
    
    Parameters:
    -----------
    symbol : str
        股票代码，如 "000001"
    
    Returns:
    --------
    dict
        包含基本面数据的字典
    """
    try:
        # 先从缓存获取
        fundamentals = cache.get_stock_fundamental(symbol)
        if fundamentals is not None and len(fundamentals) > 0:
            logger.info(f"从缓存获取股票 {symbol} 基本面数据成功")
            return fundamentals
            
        # 如果缓存中没有，则从API获取
        logger.info(f"从API获取股票 {symbol} 基本面数据")
        # 添加随机延迟，防止频繁请求被限制
        time.sleep(random.uniform(0.1, 0.5))
        
        # 适配股票代码格式：为上海股票添加SH前缀，为深圳股票添加SZ前缀
        if symbol.startswith("6"):
            formatted_symbol = f"SH{symbol}"
        else:
            formatted_symbol = f"SZ{symbol}"
            
        try:
            # 获取个股资产负债表
            balance_sheet = ak.stock_balance_sheet_by_report_em(symbol=formatted_symbol)
        except Exception as e:
            logger.warning(f"获取股票 {symbol} 资产负债表失败: {e}")
            balance_sheet = pd.DataFrame()
        
        try:
            # 获取个股利润表
            income_statement = ak.stock_profit_sheet_by_report_em(symbol=formatted_symbol)
        except Exception as e:
            logger.warning(f"获取股票 {symbol} 利润表失败: {e}")
            income_statement = pd.DataFrame()
        
        try:
            # 获取个股现金流量表
            cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol=formatted_symbol)
        except Exception as e:
            logger.warning(f"获取股票 {symbol} 现金流量表失败: {e}")
            cash_flow = pd.DataFrame()
        
        try:
            # 获取市盈率、市净率等估值指标
            # 注意：这里使用stock_a_indicator_lg代替原来的stock_a_lg_indicator
            indicator_df = ak.stock_a_indicator_lg(symbol=symbol)
        except Exception as e:
            logger.warning(f"获取股票 {symbol} 估值指标失败: {e}")
            indicator_df = pd.DataFrame()
        
        # 构建基本面数据字典
        fundamentals = {
            'balance_sheet': balance_sheet,
            'income_statement': income_statement,
            'cash_flow': cash_flow,
            'indicator': indicator_df
        }
        
        # 缓存数据
        cache.cache_stock_fundamental(fundamentals, symbol)
        
        return fundamentals
    except Exception as e:
        logger.error(f"获取股票 {symbol} 基本面数据失败: {e}")
        return {}

def calculate_technical_indicators(df):
    """
    计算技术指标
    
    Parameters:
    -----------
    df : pandas.DataFrame
        股票历史数据
    
    Returns:
    --------
    pandas.DataFrame
        添加了技术指标的DataFrame
    """
    # 确保DataFrame不为空
    if df.empty:
        return df
    
    # 确保必要的列都存在
    required_columns = ['open', 'close', 'high', 'low', 'volume', 'amount', 'pct_chg']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"缺少必要的列: {missing_columns}，无法计算技术指标")
        return df
    
    # 复制DataFrame，避免修改原始数据
    df = df.copy()
    
    # 计算移动平均线
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma30'] = df['close'].rolling(window=30).mean()
    df['ma60'] = df['close'].rolling(window=60).mean()
    
    # 计算成交量均线
    df['volume_ma5'] = df['volume'].rolling(window=5).mean()
    df['volume_ma10'] = df['volume'].rolling(window=10).mean()
    
    # 计算相对前一日的变化
    df['pre_close'] = df['close'].shift(1)
    df['pre_open'] = df['open'].shift(1)
    df['pre_volume'] = df['volume'].shift(1)
    df['pre_amount'] = df['amount'].shift(1)
    
    # 计算成交量比例
    df['volume_ratio'] = df['volume'] / df['volume_ma5']
    
    # 计算近期最高最低价格
    for period in [5, 10, 20, 30, 60]:
        df[f'highest_{period}d'] = df['high'].rolling(window=period).max()
        df[f'lowest_{period}d'] = df['low'].rolling(window=period).min()
    
    # 计算价格与最低价格的距离比例
    for period in [10, 20, 30, 60]:
        df[f'price_to_lowest_{period}d'] = df['close'] / df[f'lowest_{period}d']
    
    # 计算之前交易日的涨跌幅序列
    for i in range(1, 16):
        df[f'pct_chg_{i}d'] = df['pct_chg'].shift(i)
    
    return df

def clear_cache(days=None):
    """
    清理缓存
    
    Parameters:
    -----------
    days : int or None
        如果指定天数，则清理超过指定天数的缓存
        如果不指定，则清理所有缓存
    """
    if days is not None:
        logger.info(f"清理 {days} 天前的缓存")
        cache.clear_expired_cache(days)
    else:
        logger.info("清理所有缓存")
        cache.clear_all_cache() 