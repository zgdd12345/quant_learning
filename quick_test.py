#!/usr/bin/env python3
"""
Quick Bitcoin Strategy Test Script
快速比特币策略测试脚本

Usage:
    python quick_test.py
    python quick_test.py --plot
    python quick_test.py --save-plots
"""

import sys
import os
import argparse
import yfinance as yf
import backtrader as bt

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import all working strategies
from src.strategies.bollinger_strategy import BollingerBandsStrategy
from src.strategies.rsi_strategy import RSIMeanReversionStrategy  
from src.strategies.macd_strategy import MACDMomentumStrategy

# Import visualization tools
from src.utils.visualization import StrategyVisualizer

def quick_test(plot=False, save_plots=False):
    """Run a quick test of the top 3 strategies on Bitcoin"""
    
    # Test parameters
    symbol = "BTC-USD"  # Bitcoin
    start_date = "2020-01-01"
    end_date = "2024-01-01"
    
    print("=" * 60)
    print("快速策略回测 - 比特币 (2020-2024)")
    print("=" * 60)
    
    # Download data
    print(f"正在下载 {symbol} 数据...")
    data = yf.download(symbol, start=start_date, end=end_date, progress=False)
    
    # Handle multi-level columns
    if hasattr(data.columns, 'get_level_values'):
        data.columns = data.columns.get_level_values(0)
    data.columns = [col.title() for col in data.columns]
    
    strategies = [
        ('布林带策略', BollingerBandsStrategy),
        ('RSI策略', RSIMeanReversionStrategy),
        ('MACD策略', MACDMomentumStrategy),
    ]
    
    results = []
    visualizer = StrategyVisualizer()
    
    # Create plots directory if needed
    if save_plots:
        os.makedirs('plots', exist_ok=True)
    
    for name, strategy_class in strategies:
        print(f"\n--- 测试 {name} ---")
        
        # Create Cerebro engine
        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy_class, print_log=False)  # Disable logs for quick test
        
        # Add data
        bt_data = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(bt_data)
        
        # Set initial cash and commission
        cerebro.broker.setcash(100000.0)
        cerebro.broker.setcommission(commission=0.001)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        start_value = cerebro.broker.getvalue()
        
        try:
            # Run backtest
            result = cerebro.run()[0]
            end_value = cerebro.broker.getvalue()
            
            # Extract metrics
            sharpe_ratio = result.analyzers.sharpe.get_analysis().get('sharperatio', 0)
            if sharpe_ratio is None:
                sharpe_ratio = 0
                
            drawdown = result.analyzers.drawdown.get_analysis()
            trade_analyzer = result.analyzers.trades.get_analysis()
            
            total_return = (end_value - start_value) / start_value * 100
            max_drawdown = drawdown.get('max', {}).get('drawdown', 0)
            total_trades = trade_analyzer.get('total', {}).get('total', 0)
            winning_trades = trade_analyzer.get('won', {}).get('total', 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            results.append({
                'strategy': name,
                'return': total_return,
                'sharpe': sharpe_ratio,
                'drawdown': max_drawdown,
                'trades': total_trades,
                'win_rate': win_rate,
                'final_value': end_value
            })
            
            print(f"✅ 总收益率: {total_return:.2f}%")
            print(f"   夏普比率: {sharpe_ratio:.4f}")
            print(f"   最大回撤: {max_drawdown:.2f}%")
            print(f"   胜率: {win_rate:.1f}%")
            print(f"   交易次数: {total_trades}")
            print(f"   期末价值: ${end_value:,.2f}")
            
            # Generate plots if requested
            if (plot or save_plots) and hasattr(result, 'get_visualization_data'):
                try:
                    viz_data = result.get_visualization_data()
                    strategy_name = strategy_class.__name__.replace('Strategy', '').lower()
                    
                    # Plot file names
                    plot_file_perf = f"plots/quick_{strategy_name}_performance.html" if save_plots else None
                    
                    print(f"   📊 生成图表...")
                    
                    # Performance plot
                    visualizer.plot_strategy_performance(
                        data=data,
                        trades=viz_data.get('trade_points', []),
                        strategy_name=f"Quick Test - {name}",
                        save_as=plot_file_perf,
                        show_plot=plot
                    )
                    
                    if save_plots:
                        print(f"   💾 图表已保存: {plot_file_perf}")
                        
                except Exception as e:
                    print(f"   ⚠️ 图表生成错误: {e}")
            
        except Exception as e:
            print(f"❌ 策略失败: {e}")
            results.append({
                'strategy': name,
                'error': str(e)
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("策略排名 (按收益率)")
    print("=" * 60)
    
    successful_results = [r for r in results if 'error' not in r]
    successful_results.sort(key=lambda x: x['return'], reverse=True)
    
    for i, result in enumerate(successful_results, 1):
        print(f"{i}. {result['strategy']:<12} 收益: {result['return']:>8.2f}%  夏普: {result['sharpe']:>7.4f}  回撤: {result['drawdown']:>6.2f}%")
    
    if successful_results:
        best = successful_results[0]
        print(f"\n🏆 最佳策略: {best['strategy']}")
        print(f"   期末资金: ${best['final_value']:,.2f}")
        print(f"   累计收益: ${best['final_value'] - 100000:,.2f}")
        
        print(f"\n📊 比特币价格变化:")
        btc_start = data['Close'].iloc[0]
        btc_end = data['Close'].iloc[-1]
        btc_return = (btc_end - btc_start) / btc_start * 100
        print(f"   开始价格: ${btc_start:,.2f}")
        print(f"   结束价格: ${btc_end:,.2f}")
        print(f"   买入持有收益: {btc_return:.2f}%")
    
    # Generate comparison plot if requested
    if (plot or save_plots) and successful_results:
        try:
            import pandas as pd
            from datetime import datetime
            
            # Convert results to DataFrame format expected by visualizer
            df_results = pd.DataFrame(successful_results)
            df_results = df_results.rename(columns={
                'return': 'total_return_%',
                'sharpe': 'sharpe_ratio',
                'drawdown': 'max_drawdown_%',
                'win_rate': 'win_rate_%',
                'trades': 'total_trades'
            })
            # Add status column
            df_results['status'] = 'Success'
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_file = f"plots/quick_test_comparison_{timestamp}.html" if save_plots else None
            
            print(f"\n📊 生成策略对比图表...")
            visualizer.plot_multiple_strategies(
                results_df=df_results,
                save_as=plot_file,
                show_plot=plot
            )
            
            if save_plots:
                print(f"💾 对比图表已保存: {plot_file}")
                
        except Exception as e:
            print(f"⚠️ 对比图表生成错误: {e}")

def main():
    parser = argparse.ArgumentParser(description='Quick Bitcoin Strategy Test')
    parser.add_argument('--plot', action='store_true',
                       help='Display interactive plots')
    parser.add_argument('--save-plots', action='store_true',
                       help='Save plots to files')
    
    args = parser.parse_args()
    quick_test(plot=args.plot, save_plots=args.save_plots)

if __name__ == '__main__':
    main()