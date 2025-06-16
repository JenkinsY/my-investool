"""
配置文件，包含策略选择、数据获取等可配置选项
"""

import os

# 基础配置
BASE_CONFIG = {
    # 输出目录
    "output_dir": "results",
    
    # 日志目录
    "log_dir": "logs",
    
    # 缓存目录
    "cache_dir": "cache",
    
    # 缓存配置
    "use_cache": True,
    
    # API请求失败重试次数
    "retry_count": 3,
    
    # API请求随机延迟范围(秒)
    "request_delay_min": 0.1,
    "request_delay_max": 0.5,
    
    # 并发配置
    "max_workers": 8,  # 最大线程数，建议设置为CPU核心数的2-4倍
    "chunk_size": 10,  # 每批处理的股票数量
}

# 选股策略配置
STRATEGY_CONFIG = {
    # 启用的策略，可选：volume_up, landing_platform, high_narrow_flag, fundamental_filter, cigarette_butt
    # 设置为 "all" 表示使用所有策略
    "active_strategy": "volume_up",  # 默认只使用放量上涨策略，以提高执行速度
    
    # 各策略的自定义参数
    "volume_up": {
        "min_pct_change": 0.0,      # 最小涨幅
        "max_pct_change": 2.0,      # 最大涨幅
        "min_amount": 200000000,    # 最小成交额(2亿)
        "volume_ratio": 2.0,        # 成交量比(当日成交量/5日平均成交量)
    },
    
    "landing_platform": {
        "big_up_threshold": 9.5,    # 大涨阈值
        "max_diff_threshold": 3.0,  # 开盘收盘价差阈值
        "after_days_range": 5.0,    # 后续交易日涨跌幅范围
    },
    
    "high_narrow_flag": {
        "min_trading_days": 60,     # 最小交易天数
        "price_ratio": 1.9,         # 当日收盘价/最低价比值
        "big_up_threshold": 9.5,    # 大涨阈值
    },
    
    "fundamental_filter": {
        "max_pe": 20.0,             # 最大市盈率
        "min_pe": 0.0,              # 最小市盈率
        "max_pb": 10.0,             # 最大市净率
        "min_roe": 15.0,            # 最小净资产收益率
    },
    
    "cigarette_butt": {
        "max_pb": 0.5,              # 最大市净率
        "max_debt_ratio": 50.0,     # 最大资产负债率
        "min_positive_cash_flow": True,  # 正向经营现金流
    },
}

# 股票数据获取配置
DATA_CONFIG = {
    # 历史数据获取天数
    "history_days": 90,
    
    # 要处理的股票范围
    "stock_scope": {
        # 限制处理的股票数量，用于测试，None表示不限制
        "limit": None,
        
        # 排除的股票代码列表
        "exclude_stocks": [],
        
        # 只包含的股票代码列表，为空列表时表示处理所有股票
        "include_stocks": [],
    },
    
    # 股票列表数据配置
    "stock_list": {
        # 是否从API获取股票列表
        "enabled": True,
    },
    
    # 个股历史行情数据配置
    "stock_history": {
        # 是否从API获取历史数据
        "enabled": True,
        
        # 复权方式: "qfq"=前复权, "hfq"=后复权, ""=不复权
        "adjust": "qfq",
    },
    
    # 个股基本面数据配置
    "stock_fundamental": {
        # 是否从API获取基本面数据
        "enabled": False,
        
        # 是否获取资产负债表
        "load_balance_sheet": True,
        
        # 是否获取利润表
        "load_income_statement": True,
        
        # 是否获取现金流量表
        "load_cash_flow": True,
        
        # 是否获取估值指标
        "load_indicator": True,
    }
}

# 获取配置
def get_config():
    """获取合并后的配置"""
    config = {
        "base": BASE_CONFIG,
        "strategy": STRATEGY_CONFIG,
        "data": DATA_CONFIG,
    }
    return config

# 默认配置实例
CONFIG = get_config() 