# 比特币量化交易策略回测框架

## 项目概述
本项目是一个专门用于比特币交易策略回测的完整框架，集成了策略开发、回测分析、可视化展示等功能。

## 项目结构
```
quant_learning/
├── src/                      # 核心代码目录
│   ├── strategies/           # 交易策略模块
│   │   ├── bollinger_strategy.py  # 布林带策略
│   │   ├── rsi_strategy.py        # RSI均值回归策略  
│   │   ├── macd_strategy.py       # MACD动量策略
│   │   └── grid.py               # 网格交易策略
│   ├── indicators/           # 技术指标模块
│   │   └── __init__.py
│   ├── data/                # 数据处理模块
│   │   └── __init__.py
│   └── utils/               # 工具模块
│       └── visualization.py  # 可视化工具
├── plots/                   # 图表输出目录
├── results/                 # 回测结果目录
├── strategy_tester.py       # 主策略测试器
├── quick_test.py           # 快速测试脚本
├── plot_results.py         # 结果可视化脚本
├── run_strategies.sh       # 便捷运行脚本
├── requirements.txt        # 依赖包列表
├── test_enhanced_plotting.py # 增强绘图功能测试
├── view_plots.py           # 图表查看器
└── README.md              # 项目说明
```

## 核心功能

### 1. 交易策略
- **布林带策略 (BollingerBandsStrategy)**: 基于价格通道突破的趋势跟踪策略
- **RSI策略 (RSIMeanReversionStrategy)**: 基于超买超卖信号的均值回归策略
- **MACD策略 (MACDMomentumStrategy)**: 基于动量指标的趋势跟踪策略

### 2. 可视化功能
- **Backtrader原生绘图**：利用Backtrader内置绘图功能，支持蜡烛图、技术指标、买卖信号
- **策略性能图表**：价格走势、买卖点标记、收益曲线
- **技术指标图表**：各类技术指标的可视化展示  
- **策略对比分析**：多策略性能对比图表
- **交互式仪表板**：基于Plotly的综合分析面板
- **增强可视化**：结合Backtrader和自定义图表的双重可视化体验

### 3. 回测框架
- 基于Backtrader的专业回测引擎
- 支持手续费、滑点等真实交易成本
- 完整的风险管理（止损、止盈）
- 详细的交易统计和分析

## 使用方法

### 快速开始
```bash
# 激活conda环境
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate quant

# 快速测试（无图表）
python quick_test.py

# 快速测试（生成图表）
python quick_test.py --save-plots

# 运行单个策略
python strategy_tester.py --strategy bollinger --save-plots

# 运行所有策略
python strategy_tester.py --strategy all --save-plots
```

### 使用便捷脚本
```bash
bash run_strategies.sh
```
脚本提供交互式菜单，包含：
1. 快速测试 (Top 3策略，2020-2024)
2. 全策略测试 
3. 自定义时间测试
4. 查看可用策略
5. 单策略测试
6. 长期测试 (2017-2024)
7. 可视化测试
8. 分析已保存结果

### 结果分析
```bash
# 分析最新结果
python plot_results.py --latest

# 交互式分析
python plot_results.py --latest --interactive

# 对比多个结果文件
python plot_results.py --compare file1.csv file2.csv

# 查看所有生成的图表
python view_plots.py --summary

# 交互式图表查看器
python view_plots.py
```

### 增强绘图功能测试
```bash
# 测试增强绘图功能
python test_enhanced_plotting.py

# 使用增强布林带策略（集成Backtrader原生绘图）
python strategy_tester.py --strategy enhanced_bollinger --save-plots
```

## 依赖包
主要依赖包已在requirements.txt中定义：
- `yfinance`: 获取比特币价格数据
- `backtrader`: 回测框架
- `pandas`: 数据处理
- `numpy`: 数值计算
- `matplotlib`: 静态图表
- `plotly`: 交互式图表
- `seaborn`: 统计可视化
- `kaleido`: 图表导出

安装依赖：
```bash
conda install plotly seaborn -c conda-forge
pip install kaleido
```

## 输出文件

### 图表文件 (plots/ 目录)
- `*_performance.png`: 策略性能图表
- `*_indicators.png`: 技术指标图表  
- `*_comparison.html`: 策略对比图表
- `*_dashboard.html`: 交互式仪表板
- `*_backtrader.png`: Backtrader原生绘图
- `*_enhanced_*.png/html`: 增强版可视化图表

### 数据文件 (results/ 目录)
- `btc_strategy_results_*.csv`: 回测结果CSV文件

## 策略参数优化

### 布林带策略参数
- `bb_period`: 布林带周期 (默认: 20)
- `bb_dev`: 标准差倍数 (默认: 2.0)
- `stop_loss`: 止损比例 (默认: 0.10)
- `take_profit`: 止盈比例 (默认: 0.15)

### RSI策略参数
- `rsi_period`: RSI周期 (默认: 14)
- `rsi_oversold`: 超卖阈值 (默认: 30)
- `rsi_overbought`: 超买阈值 (默认: 70)
- `stop_loss`: 止损比例 (默认: 0.05)
- `take_profit`: 止盈比例 (默认: 0.10)

### MACD策略参数
- `fast_period`: 快线周期 (默认: 12)
- `slow_period`: 慢线周期 (默认: 26)
- `signal_period`: 信号线周期 (默认: 9)
- `stop_loss`: 止损比例 (默认: 0.08)
- `take_profit`: 止盈比例 (默认: 0.12)

## 注意事项
1. 本项目仅用于教育和研究目的，不构成投资建议
2. 回测结果不保证未来表现
3. 实际交易需考虑更多因素（滑点、流动性等）
4. 建议在模拟环境充分测试后再考虑实盘应用

## 数据来源
- 比特币价格数据来源：Yahoo Finance (yfinance)
- 数据更新：实时获取最新数据
- 支持时间范围：2010年至今

## 性能基准
基于2020-2024年比特币数据的快速测试结果：
- **布林带策略**: 97.28%收益，夏普比率0.61，最大回撤45.23%
- **MACD策略**: 34.33%收益，夏普比率0.35，最大回撤57.46% 
- **RSI策略**: 15.44%收益，夏普比率0.23，最大回撤45.99%
- **比特币持有**: 487.00%收益

*注：以上为历史回测数据，不代表未来表现*

## 更新日志
- 2025-01-24: **增强绘图功能** - 集成Backtrader原生绘图，创建增强版可视化工具
- 2025-01-24: 添加增强版布林带策略，支持更丰富的技术指标绘图
- 2025-01-24: 创建图表查看器和绘图功能测试套件
- 2025-01-24: 修复可视化依赖问题，完善图表生成功能
- 2025-01-24: 统一数据格式，修复技术指标图表显示问题
- 2025-01-24: 添加交互式便捷脚本和结果分析工具