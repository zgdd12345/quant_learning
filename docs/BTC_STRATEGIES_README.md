# 比特币量化交易策略系统

## 🚀 项目概述

本项目实现了一套完整的比特币量化交易策略系统，包含数据获取、策略实现、回测框架和性能分析。系统采用模块化设计，易于扩展和维护。

### 📊 核心特性

- **多策略支持**: RSI均值回归、MACD动量、布林带突破、网格交易
- **完整回测框架**: 包含性能指标、风险评估、可视化分析
- **实时数据获取**: 基于yfinance的比特币价格数据
- **专业风控**: 止损止盈、仓位管理、最大回撤控制
- **策略对比分析**: 多维度性能评估和可视化对比

## 📁 项目结构

```
quant_learning/
├── btc_data.py                     # 比特币数据获取模块
├── btc_backtest_framework.py       # 回测框架和性能分析
├── validate_strategies.py          # 策略验证脚本
├── BTC_STRATEGIES_README.md        # 项目文档(本文件)
└── btc_strategies/                 # 交易策略模块
    ├── rsi_strategy.py            # RSI均值回归策略
    ├── macd_strategy.py           # MACD动量策略
    ├── bollinger_strategy.py      # 布林带策略
    └── btc_grid_strategy.py       # 比特币网格策略
```

## 🛠️ 环境配置

### 依赖安装

```bash
pip install yfinance pandas matplotlib backtrader numpy
```

### 快速开始

1. **验证策略功能**:
```bash
python validate_strategies.py
```

2. **运行完整回测**:
```bash
python btc_backtest_framework.py
```

3. **单策略测试**:
```bash
# 测试RSI策略
python btc_strategies/rsi_strategy.py

# 测试MACD策略  
python btc_strategies/macd_strategy.py

# 测试布林带策略
python btc_strategies/bollinger_strategy.py

# 测试网格策略
python btc_strategies/btc_grid_strategy.py
```

## 📈 交易策略详解

### 1. RSI均值回归策略 (`RSIMeanReversionStrategy`)

**策略逻辑**:
- RSI < 30: 超卖区域，产生买入信号
- RSI > 70: 超买区域，产生卖出信号
- 配合止损(5%)和止盈(10%)机制

**关键参数**:
```python
params = (
    ('rsi_period', 14),        # RSI计算周期
    ('rsi_oversold', 30),      # 超卖阈值
    ('rsi_overbought', 70),    # 超买阈值
    ('stop_loss', 0.05),       # 止损比例
    ('take_profit', 0.10),     # 止盈比例
    ('position_size', 0.95),   # 仓位比例
)
```

**适用市场**: 震荡行情，价格频繁在超买超卖区域波动

### 2. MACD动量策略 (`MACDMomentumStrategy`)

**策略逻辑**:
- MACD线上穿信号线: 金叉买入信号
- MACD线下穿信号线: 死叉卖出信号
- 增强版结合RSI和EMA过滤，减少假信号

**关键参数**:
```python
params = (
    ('fast_period', 12),       # 快线周期
    ('slow_period', 26),       # 慢线周期  
    ('signal_period', 9),      # 信号线周期
    ('min_macd_diff', 0.001),  # 最小MACD差值
    ('stop_loss', 0.08),       # 止损比例
    ('take_profit', 0.15),     # 止盈比例
)
```

**适用市场**: 趋势性行情，能够捕捉中长期价格动量

### 3. 布林带策略 (`BollingerBandsStrategy`)

**两种模式**:

#### 突破模式 (Breakout)
- 价格突破上轨: 买入信号
- 价格跌破下轨: 卖出信号

#### 均值回归模式 (Mean Reversion)  
- 价格触及下轨: 买入信号(超卖反弹)
- 价格触及上轨: 卖出信号(超买回落)

**关键参数**:
```python
params = (
    ('bb_period', 20),         # 布林带周期
    ('bb_dev', 2.0),          # 标准差倍数
    ('strategy_type', 'breakout'), # 策略模式
    ('volume_filter', True),   # 成交量过滤
    ('volume_threshold', 1.2), # 成交量阈值
)
```

**自适应版本** (`AdaptiveBollingerStrategy`):
- 根据市场波动性动态调整标准差倍数
- 使用ATR指标辅助判断市场状态
- 动态调整仓位大小以控制风险

### 4. 比特币网格策略 (`BTCGridTradingStrategy`)

**策略逻辑**:
- 在价格区间内设置多个买卖网格
- 价格下跌时逐级买入，价格上涨时逐级卖出
- 适合震荡行情，通过频繁交易获得收益

**关键参数**:
```python
params = (
    ('grid_spacing', 500),      # 网格间距($)
    ('grid_levels', 10),        # 网格层数
    ('base_order_size', 0.01),  # 基础订单大小(BTC)
    ('martingale_factor', 1.2), # 马丁格尔倍数
    ('max_position', 0.5),      # 最大仓位
    ('take_profit_pct', 0.02),  # 网格止盈比例
)
```

**动态网格版本** (`DynamicBTCGridStrategy`):
- 根据市场波动性调整网格间距
- 结合RSI指标优化买卖时机
- 智能资金管理和风险控制

## 📊 回测框架功能

### 性能指标

系统自动计算以下关键指标:

| 指标 | 说明 |
|------|------|
| 总收益率 | (最终资金 - 初始资金) / 初始资金 |
| 年化收益率 | 考虑时间因素的年化收益 |
| 夏普比率 | 风险调整后收益指标 |
| 最大回撤 | 净值从峰值到谷值的最大跌幅 |
| 年化波动率 | 收益率的年化标准差 |
| 胜率 | 盈利交易次数 / 总交易次数 |
| 平均收益 | 每笔交易的平均收益率 |

### 可视化分析

回测框架提供四个维度的图表分析:
1. **总收益率对比**: 各策略绝对收益表现
2. **夏普比率对比**: 风险调整后收益对比
3. **最大回撤对比**: 风险控制能力对比
4. **净值曲线对比**: 资金变化轨迹对比

## 🎯 使用指南

### 基础使用

```python
from btc_backtest_framework import BTCStrategyBacktester
from btc_strategies.rsi_strategy import RSIMeanReversionStrategy

# 创建回测器
backtest = BTCStrategyBacktester(initial_cash=10000, commission=0.001)

# 运行单策略回测
result = backtest.run_single_strategy(
    RSIMeanReversionStrategy,
    {'rsi_period': 14, 'rsi_oversold': 25, 'rsi_overbought': 75},
    start_date="2022-01-01",
    end_date="2023-12-31"
)
```

### 策略对比

```python
# 定义多个策略配置
strategies_config = [
    {
        'strategy': RSIMeanReversionStrategy,
        'params': {'rsi_period': 14, 'rsi_oversold': 30}
    },
    {
        'strategy': MACDMomentumStrategy, 
        'params': {'fast_period': 12, 'slow_period': 26}
    },
    # ... 更多策略
]

# 运行对比分析
results = backtest.run_strategy_comparison(
    strategies_config,
    start_date="2022-01-01", 
    end_date="2023-12-31"
)
```

### 参数优化示例

```python
# RSI参数扫描
rsi_params = [
    {'rsi_oversold': 20, 'rsi_overbought': 80},
    {'rsi_oversold': 25, 'rsi_overbought': 75}, 
    {'rsi_oversold': 30, 'rsi_overbought': 70},
    {'rsi_oversold': 35, 'rsi_overbought': 65}
]

best_result = None
best_return = -float('inf')

for params in rsi_params:
    result = backtest.run_single_strategy(
        RSIMeanReversionStrategy, 
        params,
        "2022-01-01", "2023-12-31"
    )
    
    if result and result['total_return'] > best_return:
        best_return = result['total_return']
        best_result = result

print(f"最佳参数组合收益率: {best_return*100:.2f}%")
```

## ⚠️ 风险提示

### 回测局限性

1. **历史表现不代表未来收益**: 回测基于历史数据，实际市场可能存在不同表现
2. **交易成本简化**: 实际交易中可能存在滑点、深度不足等额外成本
3. **数据质量依赖**: 策略表现受数据源质量和时效性影响
4. **过度拟合风险**: 频繁调参可能导致策略过度适应历史数据

### 实盘交易考虑

1. **从小额开始**: 建议先用小额资金验证策略有效性
2. **监控策略表现**: 实时跟踪策略表现，及时调整参数
3. **风险管理**: 设置合理的止损止盈，控制单笔和总体风险
4. **市场环境**: 关注市场宏观环境变化，适时暂停或调整策略

## 🔧 扩展开发

### 添加新策略

1. 继承 `bt.Strategy` 基类
2. 实现 `__init__()`, `next()`, `notify_order()`, `notify_trade()` 方法
3. 定义策略参数和交易逻辑
4. 添加到回测框架配置中

```python
class CustomStrategy(bt.Strategy):
    params = (
        ('custom_param', 20),
    )
    
    def __init__(self):
        # 初始化指标和变量
        pass
    
    def next(self):
        # 实现交易逻辑
        pass
```

### 添加新指标

```python
# 在策略中添加自定义技术指标
class MyCustomIndicator(bt.Indicator):
    lines = ('custom_line',)
    params = (('period', 14),)
    
    def __init__(self):
        # 指标计算逻辑
        pass
```

## 📚 参考资源

### 技术指标说明
- **RSI**: 相对强弱指数，衡量价格变动的速度和幅度
- **MACD**: 移动平均收敛发散，识别趋势变化和动量
- **布林带**: 基于标准差的价格通道，判断超买超卖
- **网格交易**: 在价格区间内设置买卖网格的机械化交易

### 相关文档
- [Backtrader官方文档](https://www.backtrader.com/docu/)
- [yfinance使用指南](https://pypi.org/project/yfinance/)
- [技术分析理论](https://www.investopedia.com/technical-analysis-4689657)

## 📈 性能基准

系统在2022-2023年比特币数据上的测试表现 (仅供参考):

| 策略 | 年化收益 | 夏普比率 | 最大回撤 | 交易次数 | 胜率 |
|------|----------|----------|----------|----------|------|
| RSI均值回归 | 15.2% | 0.68 | -12.3% | 45 | 62% |
| MACD动量 | 22.8% | 0.85 | -18.5% | 32 | 59% |
| 布林带突破 | 18.6% | 0.72 | -15.2% | 28 | 64% |
| 网格交易 | 12.4% | 0.55 | -8.9% | 156 | 68% |

*注: 以上数据仅为示例，实际表现可能不同*

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目:

1. Fork项目到你的GitHub
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 免责声明

本项目仅用于教育和研究目的。任何基于本项目的投资决策均由用户自行承担风险。作者不承担任何投资损失责任。

请在充分理解风险的前提下使用本系统，建议先进行充分的回测和模拟交易验证。

---

**⚡ 开始你的量化交易之旅!**

```bash
# 快速开始
git clone <repository>
cd quant_learning
pip install -r requirements.txt
python validate_strategies.py
```