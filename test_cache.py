"""
测试缓存功能
"""
import os
import sys
import logging
import time
import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入工具模块
from utils.stock_data import get_stock_list, get_stock_history, get_stock_fundamentals
from utils.data_cache import DataCache

def test_cache_stock_list():
    """测试股票列表缓存"""
    logger.info("=== 测试股票列表缓存 ===")
    
    # 第一次获取，会从API获取并缓存
    time_start = time.time()
    stock_list = get_stock_list()
    time_end = time.time()
    logger.info(f"首次获取股票列表: {len(stock_list)} 只，耗时 {time_end - time_start:.2f} 秒")
    
    # 第二次获取，应该从缓存获取
    time_start = time.time()
    stock_list2 = get_stock_list()
    time_end = time.time()
    logger.info(f"第二次获取股票列表: {len(stock_list2)} 只，耗时 {time_end - time_start:.2f} 秒")
    
    # 验证两次结果相同
    if len(stock_list) == len(stock_list2):
        logger.info("两次获取的股票列表相同，缓存工作正常")
    else:
        logger.warning("两次获取的股票列表不同，缓存可能有问题")
        
    logger.info("")

def test_cache_stock_history():
    """测试股票历史数据缓存"""
    logger.info("=== 测试股票历史数据缓存 ===")
    
    # 测试的股票代码
    test_symbols = ["000001", "600000"]
    
    # 获取日期范围
    end_date = datetime.datetime.now().strftime("%Y%m%d")
    start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y%m%d")
    
    for symbol in test_symbols:
        # 第一次获取，会从API获取并缓存
        time_start = time.time()
        df = get_stock_history(symbol, start_date, end_date)
        time_end = time.time()
        logger.info(f"首次获取 {symbol} 历史数据: {len(df)} 条，耗时 {time_end - time_start:.2f} 秒")
        
        # 第二次获取，应该从缓存获取
        time_start = time.time()
        df2 = get_stock_history(symbol, start_date, end_date)
        time_end = time.time()
        logger.info(f"第二次获取 {symbol} 历史数据: {len(df2)} 条，耗时 {time_end - time_start:.2f} 秒")
        
        # 验证两次结果相同
        if len(df) == len(df2):
            logger.info(f"{symbol} 两次获取的历史数据相同，缓存工作正常")
        else:
            logger.warning(f"{symbol} 两次获取的历史数据不同，缓存可能有问题")
            
    logger.info("")

def test_cache_stock_fundamentals():
    """测试股票基本面数据缓存"""
    logger.info("=== 测试股票基本面数据缓存 ===")
    
    # 测试的股票代码
    test_symbols = ["000001", "600000"]
    
    for symbol in test_symbols:
        # 第一次获取，会从API获取并缓存
        time_start = time.time()
        fundamentals = get_stock_fundamentals(symbol)
        time_end = time.time()
        
        # 检查基本面数据是否获取成功
        has_balance = 'balance_sheet' in fundamentals and not fundamentals['balance_sheet'].empty
        has_income = 'income_statement' in fundamentals and not fundamentals['income_statement'].empty
        has_cash_flow = 'cash_flow' in fundamentals and not fundamentals['cash_flow'].empty
        has_indicator = 'indicator' in fundamentals and not fundamentals['indicator'].empty
        
        logger.info(f"首次获取 {symbol} 基本面数据，耗时 {time_end - time_start:.2f} 秒")
        logger.info(f"资产负债表: {'有数据' if has_balance else '无数据'}")
        logger.info(f"利润表: {'有数据' if has_income else '无数据'}")
        logger.info(f"现金流量表: {'有数据' if has_cash_flow else '无数据'}")
        logger.info(f"估值指标: {'有数据' if has_indicator else '无数据'}")
        
        # 第二次获取，应该从缓存获取
        time_start = time.time()
        fundamentals2 = get_stock_fundamentals(symbol)
        time_end = time.time()
        
        # 检查基本面数据是否获取成功
        has_balance2 = 'balance_sheet' in fundamentals2 and not fundamentals2['balance_sheet'].empty
        has_income2 = 'income_statement' in fundamentals2 and not fundamentals2['income_statement'].empty
        has_cash_flow2 = 'cash_flow' in fundamentals2 and not fundamentals2['cash_flow'].empty
        has_indicator2 = 'indicator' in fundamentals2 and not fundamentals2['indicator'].empty
        
        logger.info(f"第二次获取 {symbol} 基本面数据，耗时 {time_end - time_start:.2f} 秒")
        logger.info(f"资产负债表: {'有数据' if has_balance2 else '无数据'}")
        logger.info(f"利润表: {'有数据' if has_income2 else '无数据'}")
        logger.info(f"现金流量表: {'有数据' if has_cash_flow2 else '无数据'}")
        logger.info(f"估值指标: {'有数据' if has_indicator2 else '无数据'}")
        
        # 验证两次结果一致性
        if has_balance == has_balance2 and has_income == has_income2 and has_cash_flow == has_cash_flow2 and has_indicator == has_indicator2:
            logger.info(f"{symbol} 两次获取的基本面数据一致，缓存工作正常")
        else:
            logger.warning(f"{symbol} 两次获取的基本面数据不一致，缓存可能有问题")
            
    logger.info("")

def test_clear_cache():
    """测试清理缓存"""
    logger.info("=== 测试清理缓存 ===")
    
    # 初始化缓存系统
    cache = DataCache()
    
    # 清理所有缓存
    logger.info("清理所有缓存...")
    cache.clear_all_cache()
    
    # 再次获取数据，应该从API获取
    logger.info("清理缓存后重新获取数据...")
    
    # 测试股票列表
    time_start = time.time()
    stock_list = get_stock_list()
    time_end = time.time()
    logger.info(f"清理缓存后获取股票列表: {len(stock_list)} 只，耗时 {time_end - time_start:.2f} 秒")
    
    # 测试股票历史数据
    symbol = "000001"
    end_date = datetime.datetime.now().strftime("%Y%m%d")
    start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y%m%d")
    
    time_start = time.time()
    df = get_stock_history(symbol, start_date, end_date)
    time_end = time.time()
    logger.info(f"清理缓存后获取 {symbol} 历史数据: {len(df)} 条，耗时 {time_end - time_start:.2f} 秒")

if __name__ == "__main__":
    # 测试股票列表缓存
    test_cache_stock_list()
    
    # 测试股票历史数据缓存
    test_cache_stock_history()
    
    # 测试股票基本面数据缓存
    test_cache_stock_fundamentals()
    
    # 测试清理缓存
    test_clear_cache() 