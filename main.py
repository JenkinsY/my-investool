import os
import pandas as pd
import datetime
import argparse
from tqdm import tqdm
import sys
import logging
import time
import traceback
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Lock

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入工具模块
from utils.stock_data import get_stock_list, get_stock_history, calculate_technical_indicators, clear_cache, get_stock_fundamentals
from utils.config_loader import get_config, get_base_config, get_strategy_config, get_data_config, load_config, save_default_config

# 导入策略模块
from strategies.volume_up import is_volume_up
from strategies.landing_platform import is_landing_platform
from strategies.high_narrow_flag import is_high_narrow_flag
from strategies.fundamental_filter import is_good_fundamental
from strategies.cigarette_butt import is_cigarette_butt

# 全局变量用于线程安全的结果收集
results_lock = Lock()
progress_lock = Lock()

# 设置日志
def setup_logger(log_dir="logs"):
    """设置日志"""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 获取当前时间
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 设置日志
    log_file = os.path.join(log_dir, f"stock_selector_{now}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='A股自动选股程序')
    
    # 创建子命令解析器
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 选股命令
    select_parser = subparsers.add_parser("select", help="选股")
    select_parser.add_argument('--config', type=str, default=None, 
                      help='配置文件路径，不指定则使用默认配置')
    select_parser.add_argument('--strategy', type=str,
                      choices=['all', 'volume_up', 'landing_platform', 'high_narrow_flag', 'fundamental_filter', 'cigarette_butt'], 
                      default=None, help='选择策略，覆盖配置文件中的设置')
    select_parser.add_argument('--days', type=int, default=None, 
                      help='历史数据天数，覆盖配置文件中的设置')
    select_parser.add_argument('--output', type=str, default=None, 
                      help='输出结果文件夹路径，覆盖配置文件中的设置')
    select_parser.add_argument('--limit', type=int, default=None, 
                      help='限制处理的股票数量，覆盖配置文件中的设置')
    
    # 缓存管理命令
    cache_parser = subparsers.add_parser("cache", help="缓存管理")
    cache_parser.add_argument('--clear', action='store_true',
                     help='清除所有缓存')
    cache_parser.add_argument('--clear-days', type=int, default=None,
                     help='清除指定天数前的缓存，例如: --clear-days 30')
    
    # 配置管理命令
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument('--save-default', type=str, default="config.json",
                      help='保存默认配置到指定文件')
    config_parser.add_argument('--show', action='store_true',
                      help='显示当前配置')
    
    return parser.parse_args()

def process_single_stock(row, start_date, end_date, adjust, active_strategy, strategy_config, data_config, base_config, logger):
    """处理单只股票的函数"""
    symbol = row['code']
    name = row['name']
    local_results = {
        'volume_up': [],
        'landing_platform': [],
        'high_narrow_flag': [],
        'fundamental_filter': [],
        'cigarette_butt': []
    }
    
    try:
        # 获取历史数据
        retry = 0
        df = pd.DataFrame()
        
        # 如果没有获取到自定义数据，从API获取
        while retry < base_config["retry_count"] and df.empty:
            df = get_stock_history(symbol, start_date=start_date, end_date=end_date, adjust=adjust)
            if df.empty:
                retry += 1
                time.sleep(1)  # 等待1秒后重试
        
        # 如果数据为空，跳过
        if df.empty:
            logger.warning(f"获取股票 {symbol}({name}) 历史数据失败，跳过")
            return None
            
        # 计算技术指标
        df = calculate_technical_indicators(df)
        
        # 运行策略
        # 放量上涨策略
        if active_strategy == 'all' or active_strategy == 'volume_up':
            volume_params = strategy_config["volume_up"]
            if is_volume_up(df, 
                           min_pct_change=volume_params["min_pct_change"],
                           max_pct_change=volume_params["max_pct_change"],
                           min_amount=volume_params["min_amount"],
                           volume_ratio=volume_params["volume_ratio"]):
                local_results['volume_up'].append({'code': symbol, 'name': name})
                logger.info(f"股票 {symbol}({name}) 符合放量上涨策略")
                
        # 停机坪策略
        if active_strategy == 'all' or active_strategy == 'landing_platform':
            landing_params = strategy_config["landing_platform"]
            if is_landing_platform(df,
                                 big_up_threshold=landing_params["big_up_threshold"],
                                 max_diff_threshold=landing_params["max_diff_threshold"],
                                 after_days_range=landing_params["after_days_range"]):
                local_results['landing_platform'].append({'code': symbol, 'name': name})
                logger.info(f"股票 {symbol}({name}) 符合停机坪策略")
                
        # 高而窄的旗形策略
        if active_strategy == 'all' or active_strategy == 'high_narrow_flag':
            flag_params = strategy_config["high_narrow_flag"]
            if is_high_narrow_flag(df,
                                 min_trading_days=flag_params["min_trading_days"],
                                 price_ratio=flag_params["price_ratio"],
                                 big_up_threshold=flag_params["big_up_threshold"]):
                local_results['high_narrow_flag'].append({'code': symbol, 'name': name})
                logger.info(f"股票 {symbol}({name}) 符合高而窄的旗形策略")
                
        # 基本面选股策略
        if active_strategy == 'all' or active_strategy == 'fundamental_filter':
            if not data_config["stock_fundamental"]["enabled"]:
                logger.info(f"基本面数据获取已禁用，跳过股票 {symbol} 的基本面选股")
            else:
                fundamental_params = strategy_config["fundamental_filter"]
                if is_good_fundamental(symbol,
                                    max_pe=fundamental_params["max_pe"],
                                    min_pe=fundamental_params["min_pe"],
                                    max_pb=fundamental_params["max_pb"],
                                    min_roe=fundamental_params["min_roe"]):
                    local_results['fundamental_filter'].append({'code': symbol, 'name': name})
                    logger.info(f"股票 {symbol}({name}) 符合基本面选股策略")
                
        # 烟蒂股策略
        if active_strategy == 'all' or active_strategy == 'cigarette_butt':
            if not data_config["stock_fundamental"]["enabled"]:
                logger.info(f"基本面数据获取已禁用，跳过股票 {symbol} 的烟蒂股选股")
            else:
                cigarette_params = strategy_config["cigarette_butt"]
                if is_cigarette_butt(symbol,
                                  max_pb=cigarette_params["max_pb"],
                                  max_debt_ratio=cigarette_params["max_debt_ratio"],
                                  min_positive_cash_flow=cigarette_params["min_positive_cash_flow"]):
                    local_results['cigarette_butt'].append({'code': symbol, 'name': name})
                    logger.info(f"股票 {symbol}({name}) 符合烟蒂股策略")
        
        return local_results
    except Exception as e:
        logger.error(f"处理股票 {symbol}({name}) 时出错: {e}")
        logger.error(traceback.format_exc())
        return None

def select_stocks(args, logger):
    """选股主函数"""
    logger.info("开始运行A股自动选股程序")
    
    # 加载配置
    if args.config:
        logger.info(f"从配置文件 {args.config} 加载配置")
        load_config(args.config)
    
    # 获取配置
    base_config = get_base_config()
    strategy_config = get_strategy_config()
    data_config = get_data_config()
    
    # 命令行参数覆盖配置
    if args.strategy:
        strategy_config["active_strategy"] = args.strategy
        logger.info(f"命令行参数覆盖策略为: {args.strategy}")
    
    if args.days:
        data_config["history_days"] = args.days
        logger.info(f"命令行参数覆盖历史数据天数为: {args.days}")
    
    if args.output:
        base_config["output_dir"] = args.output
        logger.info(f"命令行参数覆盖输出目录为: {args.output}")
    
    if args.limit is not None:
        data_config["stock_scope"]["limit"] = args.limit
        logger.info(f"命令行参数覆盖股票处理数量限制为: {args.limit}")
    
    # 创建输出目录
    output_dir = base_config["output_dir"]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 如果禁用缓存，先清理缓存
    if not base_config["use_cache"]:
        logger.info("禁用缓存，清理所有缓存")
        clear_cache()
    
    # 获取股票列表
    logger.info("获取股票列表...")
    try:
        stock_list = get_stock_list()
        
        if stock_list.empty:
            logger.error("获取股票列表失败，程序终止")
            return
            
        logger.info(f"获取股票列表成功，共 {len(stock_list)} 只股票")
    except Exception as e:
        logger.error(f"获取股票列表时出错: {e}")
        logger.error(traceback.format_exc())
        return
    
    # 处理排除和包含的股票
    exclude_stocks = data_config["stock_scope"]["exclude_stocks"]
    include_stocks = data_config["stock_scope"]["include_stocks"]
    
    if exclude_stocks:
        stock_list = stock_list[~stock_list['code'].isin(exclude_stocks)]
        logger.info(f"排除 {len(exclude_stocks)} 只股票后，剩余 {len(stock_list)} 只股票")
    
    if include_stocks:
        stock_list = stock_list[stock_list['code'].isin(include_stocks)]
        logger.info(f"只处理指定的 {len(include_stocks)} 只股票")
    
    # 限制处理的股票数量
    limit = data_config["stock_scope"]["limit"]
    if limit:
        stock_list = stock_list.head(limit)
        logger.info(f"限制处理 {limit} 只股票")
    
    # 获取当前日期
    now = datetime.datetime.now()
    end_date = now.strftime("%Y%m%d")
    
    # 计算开始日期
    history_days = data_config["history_days"]
    start_date = (now - datetime.timedelta(days=history_days)).strftime("%Y%m%d")
    
    # 初始化结果字典
    results = {
        'volume_up': [],
        'landing_platform': [],
        'high_narrow_flag': [],
        'fundamental_filter': [],
        'cigarette_butt': []
    }
    
    # 获取活跃策略
    active_strategy = strategy_config["active_strategy"]
    
    # 历史数据调整方式
    adjust = data_config["stock_history"]["adjust"]
    
    # 记录开始时间
    start_time = time.time()
    
    # 统计处理成功和失败的股票数
    success_count = 0
    fail_count = 0
    
    # 使用线程池并发处理股票
    max_workers = base_config["max_workers"]
    chunk_size = base_config["chunk_size"]
    
    logger.info(f"开始并发处理股票，线程数: {max_workers}，每批处理数量: {chunk_size}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_stock = {
            executor.submit(
                process_single_stock,
                row,
                start_date,
                end_date,
                adjust,
                active_strategy,
                strategy_config,
                data_config,
                base_config,
                logger
            ): row for _, row in stock_list.iterrows()
        }
        
        # 使用tqdm显示进度
        with tqdm(total=len(future_to_stock), desc="处理进度") as pbar:
            for future in as_completed(future_to_stock):
                stock = future_to_stock[future]
                try:
                    local_results = future.result()
                    if local_results:
                        with results_lock:
                            for strategy, stocks in local_results.items():
                                results[strategy].extend(stocks)
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    logger.error(f"处理股票 {stock['code']}({stock['name']}) 时出错: {e}")
                    fail_count += 1
                finally:
                    pbar.update(1)
    
    # 记录结束时间
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 保存结果
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    for strategy, stock_list in results.items():
        if stock_list:
            df = pd.DataFrame(stock_list)
            output_file = os.path.join(output_dir, f"{strategy}_{current_date}.csv")
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"策略 {strategy} 选出 {len(stock_list)} 只股票，已保存至 {output_file}")
        else:
            logger.info(f"策略 {strategy} 未选出股票")
    
    logger.info(f"选股完成！处理成功: {success_count} 只，失败: {fail_count} 只，耗时: {elapsed_time:.2f}秒")

def manage_cache(args, logger):
    """缓存管理函数"""
    if args.clear:
        logger.info("清理所有缓存")
        clear_cache()
    elif args.clear_days is not None:
        logger.info(f"清理 {args.clear_days} 天前的缓存")
        clear_cache(args.clear_days)
    else:
        logger.info("没有指定缓存管理操作")

def manage_config(args, logger):
    """配置管理函数"""
    if args.save_default:
        logger.info(f"保存默认配置到 {args.save_default}")
        save_default_config(args.save_default)
    
    if args.show:
        logger.info("当前配置:")
        config = get_config()
        print(json.dumps(config, indent=2, ensure_ascii=False))

def main():
    """主程序"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 获取默认配置中的日志目录
    log_dir = get_base_config()["log_dir"]
    
    # 设置日志
    logger = setup_logger(log_dir)
    
    # 根据命令执行相应的功能
    if args.command == "select":
        select_stocks(args, logger)
    elif args.command == "cache":
        manage_cache(args, logger)
    elif args.command == "config":
        manage_config(args, logger)
    else:
        # 默认执行选股
        logger.info("未指定命令，默认执行选股")
        select_stocks(args, logger)

if __name__ == "__main__":
    main() 