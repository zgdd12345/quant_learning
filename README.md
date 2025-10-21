# Bitcoin Quantitative Trading Project

A Python-based Bitcoin quantitative trading project featuring modular architecture for backtesting trading strategies using the Backtrader framework, custom technical indicators, and Bitcoin-focused data handling (BTC-USD via yfinance and Binance API).

## Project Structure

```
├── src/                        # Source code root
│   ├── strategies/             # Trading strategy implementations
│   ├── indicators/             # Custom technical indicators  
│   ├── data/                   # Data handling modules
│   ├── utils/                  # Utility modules
│   └── tests/                  # Test files
├── examples/                   # Example usage and demos
├── docs/                      # Documentation
├── results/                   # Test results and outputs
└── requirements.txt           # Project dependencies
```

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Running Examples
```bash
# Run Bitcoin moving average backtest
python examples/backtest.py

# Run OOP-based Bitcoin strategy testing  
python examples/test.py

# Download Bitcoin data from Binance
python src/data/btc_binance_data.py
```

### Using Strategies
```python
from src.strategies.strategy import MyStrategy
from src.strategies.grid import GridTradingStrategyBase
from src.indicators.gridindicator import GridIndicator
```

## Features

- **Bitcoin Trading Strategies**: Moving Average, Grid Trading, Bollinger Bands, MACD, RSI
- **Custom Technical Indicators**: Derivative indicators, Grid indicators
- **Bitcoin Data Sources**: yfinance (BTC-USD), Binance API
- **Comprehensive Backtesting**: Built on Backtrader framework
- **Modular Architecture**: Easy to extend and customize

## Documentation

See `docs/CLAUDE.md` for detailed development guidelines and architecture overview.

## Testing

Test files are organized in `src/tests/`. Run comprehensive tests with:
```bash
python src/tests/comprehensive_strategy_test.py
```

## Results

Bitcoin backtest results and analysis reports are stored in the `results/` directory.

## Quick Start

```bash
# Quick Bitcoin strategy test
python quick_test.py

# Interactive menu
./run_strategies.sh

# Full Bitcoin strategy test
python strategy_tester.py --strategy all --start 2020-01-01 --end 2024-01-01
```