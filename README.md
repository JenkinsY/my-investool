# A股自动选股程序

基于AKShare接口的A股自动选股程序，实现了多种选股策略。

## 功能特点

- 支持多种选股策略
- 可以通过命令行参数或配置文件选择策略
- 结果保存为CSV文件
- 数据缓存系统，提高多次运行效率
- 灵活的配置系统，支持参数定制

## 选股策略

1. **放量上涨**
   - 当日比前一天上涨小于2%或收盘价小于开盘价
   - 当日成交额不低于2亿
   - 当日成交量/5日平均成交量>=2

2. **停机坪**
   - 最近15日有涨幅大于9.5%，且必须是放量上涨
   - 紧接的下个交易日必须高开，收盘价必须上涨，且与开盘价不能大于等于相差3%
   - 接下2、3个交易日必须高开，收盘价必须上涨，且与开盘价不能大于等于相差3%，且每天涨跌幅在5%间

3. **高而窄的旗形**
   - 必须至少上市交易60日
   - 当日收盘价/之前24~10日的最低价>=1.9
   - 之前24~10日必须连续两天涨幅大于等于9.5%

4. **股票基本面选股**
   - 市盈率小于等于20，且大于0
   - 市净率小于等于10
   - 净资产收益率大于等于15

5. **烟蒂股**
   - 市净率 PB < 0.5
   - 市值 < 净流动资产 NCAV
   - 资产负债率 < 50%
   - 正向经营现金流

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行界面

选股程序提供了三种主要命令：`select`（选股）、`cache`（缓存管理）和`config`（配置管理）。

#### 选股命令

```bash
# 使用默认配置进行选股
python main.py select

# 指定配置文件进行选股
python main.py select --config my_config.json

# 命令行参数覆盖配置
python main.py select --strategy volume_up --days 60 --limit 100
```

参数说明：
- `--config`: 配置文件路径，不指定则使用默认配置
- `--strategy`: 选择策略，覆盖配置文件中的设置
- `--days`: 历史数据天数，覆盖配置文件中的设置
- `--output`: 输出结果文件夹路径，覆盖配置文件中的设置
- `--limit`: 限制处理的股票数量，覆盖配置文件中的设置

#### 缓存管理命令

```bash
# 清理所有缓存
python main.py cache --clear

# 清理30天前的缓存
python main.py cache --clear-days 30
```

#### 配置管理命令

```bash
# 保存默认配置到文件
python main.py config --save-default config.json

# 显示当前配置
python main.py config --show
```

### 配置文件

程序支持通过JSON配置文件来自定义各种参数。配置文件包含三个主要部分：

1. **基础配置 (base)**：控制输出目录、日志、缓存等基本设置
2. **策略配置 (strategy)**：控制选股策略及其参数
3. **数据配置 (data)**：控制数据获取方式和范围

可以通过以下命令生成默认配置文件：

```bash
python main.py config --save-default config.json
```

然后编辑生成的配置文件，按需修改参数。使用配置文件进行选股：

```bash
python main.py select --config config.json
```

### 配置文件示例

```json
{
  "base": {
    "output_dir": "results",
    "log_dir": "logs",
    "cache_dir": "cache",
    "use_cache": true,
    "retry_count": 3
  },
  "strategy": {
    "active_strategy": "all",
    "volume_up": {
      "min_pct_change": 0.0,
      "max_pct_change": 2.0,
      "min_amount": 200000000,
      "volume_ratio": 2.0
    },
    "landing_platform": {
      "big_up_threshold": 9.5,
      "max_diff_threshold": 3.0,
      "after_days_range": 5.0
    }
  },
  "data": {
    "history_days": 90,
    "stock_scope": {
      "limit": null,
      "exclude_stocks": [],
      "include_stocks": []
    }
  }
}
```

## 缓存系统

程序内置数据缓存系统，可以大幅提高多次运行的效率。缓存分为三类：

1. **股票列表缓存**：缓存当日获取的股票列表
2. **历史数据缓存**：缓存指定日期范围的历史数据
3. **基本面数据缓存**：缓存个股基本面数据，过期时间为1天

缓存默认存放在`cache`目录下，按不同类型分为子目录：
- `cache/list`: 存放股票列表缓存
- `cache/history`: 存放历史数据缓存
- `cache/fundamental`: 存放基本面数据缓存

## 项目结构

```
my-investool/
├── main.py                 # 主程序
├── config.py               # 默认配置
├── requirements.txt        # 依赖库
├── README.md               # 项目说明
├── test_cache.py           # 缓存测试脚本
├── test_data.py            # 数据测试脚本
├── strategies/             # 策略模块
│   ├── __init__.py
│   ├── volume_up.py        # 放量上涨策略
│   ├── landing_platform.py # 停机坪策略
│   ├── high_narrow_flag.py # 高而窄的旗形策略
│   ├── fundamental_filter.py # 基本面选股策略
│   └── cigarette_butt.py   # 烟蒂股策略
└── utils/                  # 工具模块
    ├── __init__.py
    ├── stock_data.py       # 股票数据获取工具
    ├── data_cache.py       # 数据缓存系统
    └── config_loader.py    # 配置加载器
```

## 测试

可以使用以下命令测试程序的各个组件：

```bash
# 测试数据获取和处理
python test_data.py

# 测试缓存系统
python test_cache.py
``` 