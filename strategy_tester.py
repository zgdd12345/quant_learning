#!/usr/bin/env python3
"""
Bitcoin Strategy Backtesting Framework
比特币策略回测框架

Usage:
    python strategy_tester.py --strategy all --start 2020-01-01 --end 2024-01-01
    python strategy_tester.py --strategy bollinger --start 2022-01-01
    python strategy_tester.py --list-strategies
"""

import sys
import os
import argparse
import pandas as pd
import yfinance as yf
import backtrader as bt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import all strategies
from src.strategies.strategy import MyStrategy
from src.strategies.bollinger_strategy import BollingerBandsStrategy
from src.strategies.enhanced_bollinger_strategy import EnhancedBollingerBandsStrategy
from src.strategies.rsi_strategy import RSIMeanReversionStrategy
from src.strategies.macd_strategy import MACDMomentumStrategy
from src.strategies.grid import GridTradingStrategyBase

# Import visualization tools
from src.utils.visualization import StrategyVisualizer
from src.utils.enhanced_visualization import EnhancedStrategyVisualizer

class StrategyTester:
    """Strategy backtesting framework"""
    
    def __init__(self):
        self.strategies = {
            'mystrategy': MyStrategy,
            'bollinger': BollingerBandsStrategy,
            'enhanced_bollinger': EnhancedBollingerBandsStrategy,
            'rsi': RSIMeanReversionStrategy,
            'macd': MACDMomentumStrategy,
            'grid': GridTradingStrategyBase,
        }
        
        self.results = []
        self.visualizer = StrategyVisualizer()
        self.enhanced_visualizer = EnhancedStrategyVisualizer()
        
    def get_btc_data(self, start_date, end_date):
        """Download BTC data from yfinance"""
        symbol = "BTC-USD"
        try:
            print(f"Downloading Bitcoin data from {start_date} to {end_date}")
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if data.empty:
                raise ValueError(f"No Bitcoin data found for period {start_date} to {end_date}")
            
            # Handle multi-level columns from yfinance
            if isinstance(data.columns, pd.MultiIndex):
                # Flatten the column names by taking the first level
                data.columns = data.columns.get_level_values(0)
            
            # Ensure standard column names
            data.columns = [col.title() for col in data.columns]
            
            print(f"Downloaded {len(data)} Bitcoin bars")
            print(f"Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
            return data
            
        except Exception as e:
            print(f"Error downloading Bitcoin data: {e}")
            return None
    
    def run_single_strategy(self, strategy_name, data, plot=False, save_plots=False, **kwargs):
        """Run a single strategy backtest"""
        
        if strategy_name not in self.strategies:
            print(f"Strategy '{strategy_name}' not found!")
            return None
            
        strategy_class = self.strategies[strategy_name]
        
        # Create Cerebro engine
        cerebro = bt.Cerebro()
        
        # Add strategy
        cerebro.addstrategy(strategy_class, **kwargs)
        
        # Convert pandas DataFrame to Backtrader data feed
        bt_data = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(bt_data)
        
        # Set initial cash
        cerebro.broker.setcash(100000.0)
        
        # Set commission
        cerebro.broker.setcommission(commission=0.001)
        
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown') 
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
        # Record starting value
        start_value = cerebro.broker.getvalue()
        print(f'Starting Portfolio Value: {start_value:.2f}')
        
        # Run strategy
        try:
            results = cerebro.run()
            strat = results[0]
            
            # Get final value
            end_value = cerebro.broker.getvalue()
            
            # Extract analyzer results
            sharpe_ratio = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0)
            if sharpe_ratio is None:
                sharpe_ratio = 0
                
            drawdown = strat.analyzers.drawdown.get_analysis()
            returns_analyzer = strat.analyzers.returns.get_analysis()
            trade_analyzer = strat.analyzers.trades.get_analysis()
            
            # Calculate metrics
            total_return = (end_value - start_value) / start_value * 100
            max_drawdown = drawdown.get('max', {}).get('drawdown', 0)
            
            # Get trade statistics
            total_trades = trade_analyzer.get('total', {}).get('total', 0)
            winning_trades = trade_analyzer.get('won', {}).get('total', 0)
            losing_trades = trade_analyzer.get('lost', {}).get('total', 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            result = {
                'strategy': strategy_name,
                'start_value': start_value,
                'end_value': end_value,
                'total_return_%': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown_%': max_drawdown,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate_%': win_rate,
                'status': 'Success'
            }
            
            print(f'Final Portfolio Value: {end_value:.2f}')
            print(f'Total Return: {total_return:.2f}%')
            print(f'Sharpe Ratio: {sharpe_ratio:.4f}')
            print(f'Max Drawdown: {max_drawdown:.2f}%')
            print(f'Total Trades: {total_trades}')
            print(f'Win Rate: {win_rate:.2f}%')
            
            # Generate plots if requested
            if plot or save_plots:
                try:
                    # Check if strategy supports enhanced visualization
                    use_enhanced = (strategy_name == 'enhanced_bollinger' or 
                                  hasattr(strat, 'get_enhanced_visualization_data'))
                    
                    if use_enhanced and hasattr(strat, 'get_enhanced_visualization_data'):
                        print(f"\n🚀 Generating enhanced plots for {strategy_name}...")
                        
                        # Get enhanced visualization data
                        viz_data = strat.get_enhanced_visualization_data()
                        plot_data = data.copy()
                        plot_trades = viz_data.get('trade_points', [])
                        
                        # Use enhanced visualizer with Backtrader integration
                        self.enhanced_visualizer.plot_with_backtrader_and_custom(
                            cerebro, strat, plot_data, plot_trades,
                            {'portfolio_values': viz_data.get('portfolio_values')},
                            strategy_name,
                            indicators=viz_data.get('indicator_data'),
                            save_as=f"plots/{strategy_name}_enhanced" if save_plots else None,
                            show_plot=plot
                        )
                        
                    elif hasattr(strat, 'get_visualization_data'):
                        # Use traditional visualization
                        viz_data = strat.get_visualization_data()
                        
                        # Prepare plotting data
                        plot_data = data.copy()
                        plot_trades = viz_data.get('trade_points', [])
                        
                        # Plot file names
                        plot_file_perf = f"plots/{strategy_name}_performance.html" if save_plots else None
                        plot_file_tech = f"plots/{strategy_name}_indicators.html" if save_plots else None
                        plot_file_dash = f"plots/{strategy_name}_dashboard.html" if save_plots else None
                        
                        # Create plots
                        print(f"\n📊 Generating plots for {strategy_name}...")
                        
                        # Performance plot
                        self.visualizer.plot_strategy_performance(
                            data=plot_data, 
                            trades=plot_trades, 
                            strategy_name=strategy_name,
                            save_as=plot_file_perf,
                            show_plot=plot
                        )
                        
                        # Technical indicators plot
                        self.visualizer.plot_technical_indicators(
                            data=viz_data.get('indicator_data'),
                            strategy_name=strategy_name,
                            save_as=plot_file_tech,
                            show_plot=plot
                        )
                        
                        # Interactive dashboard
                        self.visualizer.create_interactive_dashboard(
                            data=plot_data,
                            trades=plot_trades,
                            strategy_results=result,
                            strategy_name=strategy_name,
                            save_as=plot_file_dash
                        )
                        
                        if save_plots:
                            print(f"📁 Plots saved: {plot_file_perf}, {plot_file_tech}, {plot_file_dash}")
                    
                    else:
                        # Fallback: Use Backtrader's native plotting only
                        print(f"\n📊 Using Backtrader native plotting for {strategy_name}...")
                        self.enhanced_visualizer.plot_backtrader_strategy(
                            cerebro, strat, strategy_name,
                            save_as=f"plots/{strategy_name}_backtrader" if save_plots else None,
                            show_plot=plot
                        )
                            
                except Exception as e:
                    print(f"⚠️  Error generating plots: {e}")
                    # Fallback to basic Backtrader plot
                    try:
                        print("📊 Attempting fallback to Backtrader native plot...")
                        cerebro.plot(style='candlestick', volume=False)
                    except Exception as e2:
                        print(f"⚠️  Error with fallback plot: {e2}")
            
            return result
            
        except Exception as e:
            print(f"Error running strategy '{strategy_name}': {e}")
            return {
                'strategy': strategy_name,
                'status': 'Failed',
                'error': str(e)
            }
    
    def run_all_strategies(self, data, plot=False, save_plots=False, **kwargs):
        """Run all available strategies"""
        print("\n" + "="*60)
        print("RUNNING ALL STRATEGIES")
        print("="*60)
        
        # Create plots directory if needed
        if save_plots:
            import os
            os.makedirs('plots', exist_ok=True)
        
        results = []
        for strategy_name in self.strategies.keys():
            print(f"\n--- Testing Strategy: {strategy_name.upper()} ---")
            result = self.run_single_strategy(
                strategy_name, data, plot=plot, save_plots=save_plots, **kwargs
            )
            if result:
                results.append(result)
                self.results.append(result)
        
        return results
    
    def generate_report(self, results, start_date, end_date, plot_comparison=False, save_plots=False):
        """Generate performance comparison report"""
        print("\n" + "="*80)
        print(f"BITCOIN STRATEGY PERFORMANCE REPORT")
        print(f"Period: {start_date} to {end_date}")
        print("="*80)
        
        if not results:
            print("No results to display!")
            return
        
        # Create DataFrame for easier formatting
        df_results = pd.DataFrame(results)
        
        # Filter successful strategies
        successful = df_results[df_results['status'] == 'Success'].copy()
        failed = df_results[df_results['status'] == 'Failed'].copy()
        
        if not successful.empty:
            # Sort by total return
            successful = successful.sort_values('total_return_%', ascending=False)
            
            print("\n📈 SUCCESSFUL STRATEGIES:")
            print("-" * 80)
            
            # Format and display results
            for _, row in successful.iterrows():
                print(f"🔸 {row['strategy'].upper():<15}")
                print(f"   Total Return:    {row['total_return_%']:>8.2f}%")
                print(f"   Sharpe Ratio:    {row['sharpe_ratio']:>8.4f}")
                print(f"   Max Drawdown:    {row['max_drawdown_%']:>8.2f}%")
                print(f"   Win Rate:        {row['win_rate_%']:>8.2f}%")
                print(f"   Total Trades:    {row['total_trades']:>8.0f}")
                print()
            
            # Best strategy
            best_strategy = successful.iloc[0]
            print(f"🏆 BEST PERFORMING STRATEGY: {best_strategy['strategy'].upper()}")
            print(f"   Return: {best_strategy['total_return_%']:.2f}%")
            print(f"   Sharpe: {best_strategy['sharpe_ratio']:.4f}")
        
        if not failed.empty:
            print(f"\n❌ FAILED STRATEGIES ({len(failed)}):")
            print("-" * 40)
            for _, row in failed.iterrows():
                print(f"   {row['strategy']}: {row.get('error', 'Unknown error')}")
        
        # Create results directory if needed
        import os
        os.makedirs('results', exist_ok=True)
        
        # Save results to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"results/btc_strategy_results_{timestamp}.csv"
        df_results.to_csv(results_file, index=False)
        print(f"\n💾 Bitcoin results saved to: {results_file}")
        
        # Generate strategy comparison plot if requested
        if (plot_comparison or save_plots) and not successful.empty:
            try:
                plot_file = f"plots/strategy_comparison_{timestamp}.html" if save_plots else None
                print(f"\n📊 Generating strategy comparison plot...")
                self.visualizer.plot_multiple_strategies(
                    results_df=successful,
                    save_as=plot_file,
                    show_plot=plot_comparison
                )
                if save_plots:
                    print(f"📁 Comparison plot saved: {plot_file}")
            except Exception as e:
                print(f"⚠️  Error generating comparison plot: {e}")
        
        return successful, failed
    
    def list_strategies(self):
        """List all available strategies"""
        print("\n📋 AVAILABLE STRATEGIES:")
        print("-" * 40)
        for i, (name, strategy_class) in enumerate(self.strategies.items(), 1):
            doc = strategy_class.__doc__
            description = doc.split('\n')[1].strip() if doc else "No description"
            print(f"{i:2d}. {name:<15} - {description}")
        print()


def main():
    parser = argparse.ArgumentParser(description='Bitcoin Strategy Backtesting Framework')
    parser.add_argument('--strategy', '-s', default='all', 
                       help='Strategy to test (default: all)')
    parser.add_argument('--start', default='2020-01-01',
                       help='Start date (default: 2020-01-01)')
    parser.add_argument('--end', default='2024-01-01',
                       help='End date (default: 2024-01-01)')
    parser.add_argument('--cash', type=float, default=100000.0,
                       help='Initial cash (default: 100000)')
    parser.add_argument('--commission', type=float, default=0.001,
                       help='Commission rate (default: 0.001)')
    parser.add_argument('--list-strategies', action='store_true',
                       help='List all available strategies')
    parser.add_argument('--plot', action='store_true',
                       help='Display interactive plots')
    parser.add_argument('--save-plots', action='store_true',
                       help='Save plots to files')
    
    args = parser.parse_args()
    
    tester = StrategyTester()
    
    if args.list_strategies:
        tester.list_strategies()
        return
    
    # Get Bitcoin data
    data = tester.get_btc_data(args.start, args.end)
    if data is None:
        return
    
    # Run strategies
    if args.strategy.lower() == 'all':
        results = tester.run_all_strategies(
            data, plot=args.plot, save_plots=args.save_plots
        )
        tester.generate_report(
            results, args.start, args.end, 
            plot_comparison=args.plot, save_plots=args.save_plots
        )
    else:
        result = tester.run_single_strategy(
            args.strategy.lower(), data, 
            plot=args.plot, save_plots=args.save_plots
        )
        if result:
            tester.generate_report(
                [result], args.start, args.end, 
                plot_comparison=args.plot, save_plots=args.save_plots
            )


if __name__ == '__main__':
    main()