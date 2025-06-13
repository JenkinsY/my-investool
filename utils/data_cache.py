"""
数据缓存模块，用于缓存股票数据，避免重复请求
"""

import os
import pandas as pd
import json
import pickle
import datetime
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)

class DataCache:
    """数据缓存类"""
    
    def __init__(self, cache_dir="cache"):
        """
        初始化缓存系统
        
        Parameters:
        -----------
        cache_dir : str
            缓存目录，默认为"cache"
        """
        self.cache_dir = cache_dir
        self._create_cache_dirs()
        
    def _create_cache_dirs(self):
        """创建缓存目录结构"""
        # 主缓存目录
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # 股票历史数据缓存目录
        history_dir = os.path.join(self.cache_dir, "history")
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        # 基本面数据缓存目录
        fundamental_dir = os.path.join(self.cache_dir, "fundamental")
        if not os.path.exists(fundamental_dir):
            os.makedirs(fundamental_dir)
        
        # 股票列表缓存目录
        list_dir = os.path.join(self.cache_dir, "list")
        if not os.path.exists(list_dir):
            os.makedirs(list_dir)
    
    def _get_history_cache_path(self, symbol, start_date, end_date, adjust):
        """
        获取股票历史数据的缓存路径
        
        Parameters:
        -----------
        symbol : str
            股票代码
        start_date : str
            开始日期
        end_date : str
            结束日期
        adjust : str
            复权方式
            
        Returns:
        --------
        str
            缓存文件路径
        """
        # 文件名格式：股票代码_开始日期_结束日期_复权方式.pkl
        file_name = f"{symbol}_{start_date}_{end_date}_{adjust}.pkl"
        return os.path.join(self.cache_dir, "history", file_name)
    
    def _get_fundamental_cache_path(self, symbol):
        """
        获取股票基本面数据的缓存路径
        
        Parameters:
        -----------
        symbol : str
            股票代码
            
        Returns:
        --------
        str
            缓存文件路径
        """
        # 文件名格式：股票代码.pkl
        file_name = f"{symbol}.pkl"
        return os.path.join(self.cache_dir, "fundamental", file_name)
    
    def _get_stock_list_cache_path(self):
        """
        获取股票列表的缓存路径
        
        Returns:
        --------
        str
            缓存文件路径
        """
        # 文件名格式：stock_list_日期.pkl
        today = datetime.datetime.now().strftime("%Y%m%d")
        file_name = f"stock_list_{today}.pkl"
        return os.path.join(self.cache_dir, "list", file_name)
    
    def get_stock_history(self, symbol, start_date=None, end_date=None, adjust="qfq"):
        """
        获取股票历史数据（先从缓存获取，如果没有则返回None）
        
        Parameters:
        -----------
        symbol : str
            股票代码
        start_date : str
            开始日期
        end_date : str
            结束日期
        adjust : str
            复权方式
            
        Returns:
        --------
        pandas.DataFrame or None
            股票历史数据，如果缓存中不存在则返回None
        """
        cache_path = self._get_history_cache_path(symbol, start_date, end_date, adjust)
        
        if os.path.exists(cache_path):
            try:
                logger.info(f"从缓存获取股票 {symbol} 历史数据")
                with open(cache_path, 'rb') as f:
                    df = pickle.load(f)
                return df
            except Exception as e:
                logger.error(f"读取股票 {symbol} 历史数据缓存出错: {e}")
                # 删除损坏的缓存文件
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                return None
        else:
            return None
    
    def cache_stock_history(self, df, symbol, start_date=None, end_date=None, adjust="qfq"):
        """
        缓存股票历史数据
        
        Parameters:
        -----------
        df : pandas.DataFrame
            股票历史数据
        symbol : str
            股票代码
        start_date : str
            开始日期
        end_date : str
            结束日期
        adjust : str
            复权方式
        """
        if df is None or df.empty:
            logger.warning(f"股票 {symbol} 历史数据为空，不进行缓存")
            return
        
        cache_path = self._get_history_cache_path(symbol, start_date, end_date, adjust)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(df, f)
            logger.info(f"股票 {symbol} 历史数据缓存成功")
        except Exception as e:
            logger.error(f"缓存股票 {symbol} 历史数据出错: {e}")
    
    def get_stock_fundamental(self, symbol):
        """
        获取股票基本面数据（先从缓存获取，如果没有则返回None）
        
        Parameters:
        -----------
        symbol : str
            股票代码
            
        Returns:
        --------
        dict or None
            股票基本面数据，如果缓存中不存在则返回None
        """
        cache_path = self._get_fundamental_cache_path(symbol)
        
        if os.path.exists(cache_path):
            try:
                logger.info(f"从缓存获取股票 {symbol} 基本面数据")
                with open(cache_path, 'rb') as f:
                    fundamentals = pickle.load(f)
                
                # 检查缓存是否过期（超过1天）
                if 'timestamp' in fundamentals:
                    cache_time = datetime.datetime.fromtimestamp(fundamentals['timestamp'])
                    now = datetime.datetime.now()
                    if (now - cache_time).days > 0:
                        logger.info(f"股票 {symbol} 基本面数据缓存已过期")
                        return None
                    # 移除时间戳
                    del fundamentals['timestamp']
                
                return fundamentals
            except Exception as e:
                logger.error(f"读取股票 {symbol} 基本面数据缓存出错: {e}")
                # 删除损坏的缓存文件
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                return None
        else:
            return None
    
    def cache_stock_fundamental(self, fundamentals, symbol):
        """
        缓存股票基本面数据
        
        Parameters:
        -----------
        fundamentals : dict
            股票基本面数据
        symbol : str
            股票代码
        """
        if fundamentals is None or len(fundamentals) == 0:
            logger.warning(f"股票 {symbol} 基本面数据为空，不进行缓存")
            return
        
        cache_path = self._get_fundamental_cache_path(symbol)
        
        try:
            # 添加时间戳
            fundamentals_with_timestamp = fundamentals.copy()
            fundamentals_with_timestamp['timestamp'] = datetime.datetime.now().timestamp()
            
            with open(cache_path, 'wb') as f:
                pickle.dump(fundamentals_with_timestamp, f)
            logger.info(f"股票 {symbol} 基本面数据缓存成功")
        except Exception as e:
            logger.error(f"缓存股票 {symbol} 基本面数据出错: {e}")
    
    def get_stock_list(self):
        """
        获取股票列表（先从缓存获取，如果没有则返回None）
        
        Returns:
        --------
        pandas.DataFrame or None
            股票列表，如果缓存中不存在则返回None
        """
        cache_path = self._get_stock_list_cache_path()
        
        if os.path.exists(cache_path):
            try:
                logger.info("从缓存获取股票列表")
                with open(cache_path, 'rb') as f:
                    df = pickle.load(f)
                return df
            except Exception as e:
                logger.error(f"读取股票列表缓存出错: {e}")
                # 删除损坏的缓存文件
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                return None
        else:
            return None
    
    def cache_stock_list(self, df):
        """
        缓存股票列表
        
        Parameters:
        -----------
        df : pandas.DataFrame
            股票列表
        """
        if df is None or df.empty:
            logger.warning("股票列表为空，不进行缓存")
            return
        
        cache_path = self._get_stock_list_cache_path()
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(df, f)
            logger.info("股票列表缓存成功")
        except Exception as e:
            logger.error(f"缓存股票列表出错: {e}")
    
    def clear_expired_cache(self, days=30):
        """
        清理过期的缓存文件
        
        Parameters:
        -----------
        days : int
            过期天数，默认30天
        """
        now = datetime.datetime.now()
        count = 0
        
        # 遍历所有缓存目录
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # 获取文件修改时间
                file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                # 如果文件超过指定天数未修改，则删除
                if (now - file_time).days > days:
                    try:
                        os.remove(file_path)
                        count += 1
                    except Exception as e:
                        logger.error(f"删除过期缓存文件 {file_path} 出错: {e}")
        
        logger.info(f"清理了 {count} 个过期缓存文件")
    
    def clear_all_cache(self):
        """清理所有缓存"""
        # 股票历史数据缓存
        history_dir = os.path.join(self.cache_dir, "history")
        if os.path.exists(history_dir):
            for file in os.listdir(history_dir):
                os.remove(os.path.join(history_dir, file))
        
        # 基本面数据缓存
        fundamental_dir = os.path.join(self.cache_dir, "fundamental")
        if os.path.exists(fundamental_dir):
            for file in os.listdir(fundamental_dir):
                os.remove(os.path.join(fundamental_dir, file))
        
        # 股票列表缓存
        list_dir = os.path.join(self.cache_dir, "list")
        if os.path.exists(list_dir):
            for file in os.listdir(list_dir):
                os.remove(os.path.join(list_dir, file))
        
        logger.info("所有缓存已清理") 