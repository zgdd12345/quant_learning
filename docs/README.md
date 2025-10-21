# Quantitative Trading Learning Project

A comprehensive Python-based quantitative trading system for learning strategy development, backtesting, and technical analysis. Features modular design with data acquisition, custom indicators, trading strategies, and backtesting frameworks.

## 🚀 Features

- **Multi-Asset Support**: Stock data (via yfinance) and cryptocurrency data (via Binance API)
- **Custom Technical Indicators**: Derivative indicators and dynamic grid indicators
- **Advanced Trading Strategies**: Moving average crossover and dynamic grid trading
- **Backtesting Framework**: Integrated with Backtrader for comprehensive strategy testing
- **Modular Architecture**: Clean separation of data, indicators, strategies, and backtesting

## 📁 Project Structure

```
quant_learning/
├── README.md                      # Project documentation
├── backtest.py                   # Simple moving average backtest
├── test.py                       # OOP-based strategy testing framework
├── dataset.py                    # Stock data acquisition (yfinance)
├── data.py                       # Cryptocurrency data download (Binance)
├── myindicator.py               # Custom derivative indicators
├── test.ipynb                   # Jupyter notebook for analysis
├── strategy/                    # Trading strategies module
│   ├── strategy.py             # MA + volume derivative strategy
│   └── grid.py                 # Dynamic grid trading strategy
└── indicator/                  # Technical indicators module
    └── gridindicator.py        # Dynamic grid indicator based on SMA
```

## 📊 Core Modules

### 1. Data Acquisition
- **dataset.py**: Stock data via yfinance with real-time monitoring
- **data.py**: Cryptocurrency historical data from Binance API

### 2. Technical Indicators
- **myindicator.py**: Custom derivative indicators (price/volume derivatives)
- **indicator/gridindicator.py**: Dynamic grid indicator based on SMA

### 3. Trading Strategies
- **strategy/strategy.py**: Combined MA + volume derivative strategy
- **strategy/grid.py**: Dynamic grid trading with risk management

### 4. Backtesting Framework
- **backtest.py**: Simple moving average strategy backtester
- **test.py**: Object-oriented strategy testing framework

## ⚡ Quick Start

### Installation

```bash
pip install yfinance pandas matplotlib backtrader ccxt requests
```

### 1. Stock Analysis

```python
# Run moving average strategy backtest
python backtest.py

# Use OOP testing framework
python test.py
```

### 2. Cryptocurrency Data

```python
# Download BTC/USDT data (modify data.py for CLI args)
python data.py
```

### 3. Advanced Backtesting

```python
import backtrader as bt
from strategy.grid import GridTradingStrategyBase

cerebro = bt.Cerebro()
cerebro.addstrategy(GridTradingStrategyBase, 
                   grid_space=100, 
                   max_layers=5)
cerebro.run()
```

## 🎯 Trading Strategies

### Moving Average Strategy
- **Logic**: Dual moving average crossover signals
- **Features**: Configurable short/long periods with visualization
- **File**: `backtest.py`, `test.py`

### Grid Trading Strategy  
- **Logic**: Dynamic grid placement based on SMA
- **Features**: Multi-layer trading with risk management
- **File**: `strategy/grid.py`
- **Parameters**: Grid spacing, volume per layer, max layers

### Derivative Indicator Strategy
- **Logic**: Combines price MA with volume rate of change
- **Features**: Enhanced signal quality through indicator combination
- **File**: `strategy/strategy.py`

## ⚙️ Configuration Examples

### Stock Analysis Configuration
```python
config = {
    'stock_name': 'Maotai',
    'symbol': '600519.SS',
    'start_date': '2023-05-01',
    'end_date': '2025-04-01',
    'long': 50,    # Long-term MA
    'short': 10    # Short-term MA
}
```

### Grid Strategy Parameters
```python
params = {
    'grid_space': 100,        # Grid spacing
    'volume_per_layer': 100,  # Volume per layer
    'max_layers': 5,          # Maximum layers
    'period': 20              # SMA period
}
```

## 🛠️ Technical Features

1. **Modular Architecture**: Clean separation of data, indicators, strategies, and backtesting
2. **Multi-Asset Support**: Stocks (yfinance) and cryptocurrencies (ccxt/Binance API)
3. **Custom Indicators**: Innovative derivative indicators for technical analysis
4. **Dynamic Strategies**: Adaptive grid trading with multi-layer execution
5. **Comprehensive Visualization**: Built-in matplotlib charts and Backtrader plotting

## 📈 Code Quality Improvements Recommended

### High Priority
- Remove hardcoded proxy settings from `dataset.py:7-8`
- Add error handling for API calls
- Fix signal logic inconsistency in `test.py:35-36`

### Medium Priority
- Clean up commented code blocks
- Add type hints and docstrings
- Implement proper logging
- Create requirements.txt
- Add unit tests

### Configuration Management
```python
# Use environment variables instead of hardcoded values
import os

PROXY_HTTP = os.getenv('HTTP_PROXY')
PROXY_HTTPS = os.getenv('HTTPS_PROXY')
```

## ⚠️ Important Notes

- **Educational Purpose**: This project is for learning and research only
- **Risk Management**: Test thoroughly before any live trading
- **Compliance**: Follow relevant financial regulations and exchange rules
- **Data Security**: Never commit API keys or sensitive data

## 🤝 Contributing

Contributions welcome! Please submit issues and pull requests to help improve this quantitative trading learning project.

## 📄 License

This project is for educational purposes. Please ensure compliance with relevant financial regulations when using for any trading activities.