#!/usr/bin/env python3
"""
Test Enhanced Plotting Functionality
测试增强绘图功能

This script demonstrates the differences between traditional plotting and enhanced Backtrader plotting.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import yfinance as yf
import backtrader as bt
from src.strategies.bollinger_strategy import BollingerBandsStrategy
from src.strategies.enhanced_bollinger_strategy import EnhancedBollingerBandsStrategy
from src.utils.enhanced_visualization import EnhancedStrategyVisualizer

def test_traditional_vs_enhanced():
    """Compare traditional Bollinger strategy with enhanced version"""
    
    # Download Bitcoin data
    print("📊 Downloading Bitcoin data...")
    data = yf.download("BTC-USD", start="2023-10-01", end="2023-12-31", progress=False)
    
    # Handle multi-level columns
    if hasattr(data.columns, 'get_level_values'):
        data.columns = data.columns.get_level_values(0)
    data.columns = [col.title() for col in data.columns]
    
    strategies_to_test = [
        ('Traditional Bollinger', BollingerBandsStrategy),
        ('Enhanced Bollinger', EnhancedBollingerBandsStrategy)
    ]
    
    visualizer = EnhancedStrategyVisualizer()
    
    for strategy_name, strategy_class in strategies_to_test:
        print(f"\n{'='*60}")
        print(f"Testing {strategy_name}")
        print(f"{'='*60}")
        
        # Create Cerebro engine
        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy_class, print_log=False)
        
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
        print(f'Starting Portfolio Value: {start_value:.2f}')
        
        # Run backtest
        try:
            results = cerebro.run()
            strat = results[0]
            end_value = cerebro.broker.getvalue()
            
            # Extract metrics
            sharpe_ratio = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0)
            if sharpe_ratio is None:
                sharpe_ratio = 0
                
            drawdown = strat.analyzers.drawdown.get_analysis()
            trade_analyzer = strat.analyzers.trades.get_analysis()
            
            total_return = (end_value - start_value) / start_value * 100
            max_drawdown = drawdown.get('max', {}).get('drawdown', 0)
            total_trades = trade_analyzer.get('total', {}).get('total', 0)
            winning_trades = trade_analyzer.get('won', {}).get('total', 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            print(f'Final Portfolio Value: {end_value:.2f}')
            print(f'Total Return: {total_return:.2f}%')
            print(f'Sharpe Ratio: {sharpe_ratio:.4f}')
            print(f'Max Drawdown: {max_drawdown:.2f}%')
            print(f'Total Trades: {total_trades}')
            print(f'Win Rate: {win_rate:.2f}%')
            
            # Generate plots using different methods
            strategy_safe_name = strategy_name.lower().replace(' ', '_')
            
            if hasattr(strat, 'get_enhanced_visualization_data'):
                print(f"🚀 Using enhanced visualization for {strategy_name}")
                
                # Get enhanced visualization data
                viz_data = strat.get_enhanced_visualization_data()
                plot_trades = viz_data.get('trade_points', [])
                
                # Use enhanced visualizer with Backtrader integration
                visualizer.plot_with_backtrader_and_custom(
                    cerebro, strat, data, plot_trades,
                    {'portfolio_values': viz_data.get('portfolio_values')},
                    strategy_name,
                    indicators=viz_data.get('indicator_data'),
                    save_as=f"plots/{strategy_safe_name}_test",
                    show_plot=False
                )
                
            else:
                print(f"📊 Using Backtrader native plotting for {strategy_name}")
                
                # Use Backtrader's native plotting
                visualizer.plot_backtrader_strategy(
                    cerebro, strat, strategy_name,
                    save_as=f"plots/{strategy_safe_name}_backtrader",
                    show_plot=False
                )
            
        except Exception as e:
            print(f"❌ Error testing {strategy_name}: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Testing Complete!")
    print("📁 Check the 'plots/' directory for generated visualizations.")
    print(f"{'='*60}")

def test_backtrader_native_plot():
    """Test pure Backtrader native plotting functionality"""
    print("\n" + "="*60)
    print("Testing Backtrader Native Plot Features")
    print("="*60)
    
    # Simple test with enhanced strategy
    data = yf.download("BTC-USD", start="2023-11-01", end="2023-12-31", progress=False)
    
    # Handle multi-level columns
    if hasattr(data.columns, 'get_level_values'):
        data.columns = data.columns.get_level_values(0)
    data.columns = [col.title() for col in data.columns]
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(EnhancedBollingerBandsStrategy, print_log=False)
    
    bt_data = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(bt_data)
    
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)
    
    print("Running backtest...")
    results = cerebro.run()
    
    print("📊 Generating Backtrader native plot...")
    try:
        # Test different plot styles
        figs = cerebro.plot(
            style='candlestick',
            volume=True,
            plotdist=0.1,
            barup='#26A69A',
            bardown='#EF5350',
            volup='#26A69A',
            voldown='#EF5350',
            grid=True,
            returnfig=True
        )
        
        if figs:
            print("✅ Backtrader plot generated successfully!")
            # Save the plot
            fig = figs[0][0]
            fig.suptitle('Enhanced Bollinger Strategy - Native Backtrader Plot', 
                        fontsize=14, fontweight='bold')
            fig.savefig('plots/backtrader_native_test.png', dpi=300, bbox_inches='tight')
            print("💾 Plot saved as: plots/backtrader_native_test.png")
        
    except Exception as e:
        print(f"⚠️ Error with Backtrader plot: {e}")

if __name__ == '__main__':
    print("🚀 Starting Enhanced Plotting Test Suite")
    print("="*60)
    
    # Test traditional vs enhanced
    test_traditional_vs_enhanced()
    
    # Test native Backtrader plotting
    test_backtrader_native_plot()
    
    print("\n🎉 All tests completed!")