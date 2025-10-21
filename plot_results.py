#!/usr/bin/env python3
"""
Interactive Results Plotting Script
交互式结果绘图脚本

Usage:
    python plot_results.py results/btc_strategy_results_20250823_123456.csv
    python plot_results.py --latest
    python plot_results.py --compare results/file1.csv results/file2.csv
"""

import sys
import os
import argparse
import pandas as pd
import glob
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.visualization import StrategyVisualizer


class ResultsPlotter:
    """Interactive results plotting and analysis"""
    
    def __init__(self):
        self.visualizer = StrategyVisualizer()
        
    def find_latest_results(self, results_dir='results'):
        """Find the most recent results file"""
        if not os.path.exists(results_dir):
            print(f"❌ Results directory '{results_dir}' not found!")
            return None
        
        # Find all CSV files in results directory
        csv_files = glob.glob(os.path.join(results_dir, '*.csv'))
        
        if not csv_files:
            print(f"❌ No CSV results files found in '{results_dir}'!")
            return None
        
        # Sort by modification time (newest first)
        csv_files.sort(key=os.path.getmtime, reverse=True)
        latest_file = csv_files[0]
        
        print(f"📁 Found latest results file: {latest_file}")
        return latest_file
    
    def load_results(self, file_path):
        """Load results from CSV file"""
        try:
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return None
            
            df = pd.read_csv(file_path)
            print(f"📊 Loaded {len(df)} strategy results")
            print(f"🔄 Strategies: {', '.join(df['strategy'].unique())}")
            
            return df
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return None
    
    def plot_single_results(self, results_df, save_plots=False):
        """Plot results from a single results file"""
        
        # Filter successful strategies
        successful = results_df[results_df['status'] == 'Success'].copy()
        failed = results_df[results_df['status'] == 'Failed'].copy()
        
        if successful.empty:
            print("❌ No successful strategies to plot!")
            return
        
        # Create plots directory if needed
        if save_plots:
            os.makedirs('plots', exist_ok=True)
        
        print(f"\n📈 Plotting {len(successful)} successful strategies...")
        
        # Strategy comparison plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_file = f"plots/results_comparison_{timestamp}.html" if save_plots else None
        
        self.visualizer.plot_multiple_strategies(
            results_df=successful,
            save_as=plot_file,
            show_plot=True
        )
        
        if save_plots:
            print(f"💾 Plot saved: {plot_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 STRATEGY PERFORMANCE SUMMARY")
        print("="*60)
        
        # Sort by return
        successful_sorted = successful.sort_values('total_return_%', ascending=False)
        
        for _, row in successful_sorted.iterrows():
            print(f"🔸 {row['strategy'].upper():<15}")
            print(f"   Return:     {row['total_return_%']:>8.2f}%")
            print(f"   Sharpe:     {row['sharpe_ratio']:>8.4f}")
            print(f"   Drawdown:   {row['max_drawdown_%']:>8.2f}%")
            print(f"   Win Rate:   {row['win_rate_%']:>8.2f}%")
            print()
        
        # Best strategy
        if not successful_sorted.empty:
            best = successful_sorted.iloc[0]
            print(f"🏆 BEST STRATEGY: {best['strategy'].upper()}")
            print(f"   📈 Return: {best['total_return_%']:.2f}%")
            print(f"   📊 Sharpe: {best['sharpe_ratio']:.4f}")
        
        if not failed.empty:
            print(f"\n❌ FAILED STRATEGIES ({len(failed)}):")
            for _, row in failed.iterrows():
                error_msg = row.get('error', 'Unknown error')
                print(f"   - {row['strategy']}: {error_msg}")
    
    def compare_results(self, file_paths, save_plots=False):
        """Compare results from multiple files"""
        all_results = []
        
        for i, file_path in enumerate(file_paths):
            df = self.load_results(file_path)
            if df is not None:
                # Add file identifier
                file_name = os.path.basename(file_path)
                df['file'] = file_name
                df['run_id'] = i + 1
                all_results.append(df)
        
        if not all_results:
            print("❌ No valid results files to compare!")
            return
        
        # Combine all results
        combined_df = pd.concat(all_results, ignore_index=True)
        successful = combined_df[combined_df['status'] == 'Success'].copy()
        
        if successful.empty:
            print("❌ No successful strategies found across all files!")
            return
        
        print(f"\n📊 Comparing results from {len(file_paths)} files...")
        print(f"📈 Found {len(successful)} successful strategy runs")
        
        # Create comparison visualization
        if save_plots:
            os.makedirs('plots', exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_file = f"plots/multi_file_comparison_{timestamp}.html" if save_plots else None
        
        # Group by strategy and show evolution
        strategy_comparison = []
        for strategy in successful['strategy'].unique():
            strategy_data = successful[successful['strategy'] == strategy].copy()
            strategy_data = strategy_data.sort_values('run_id')
            
            print(f"\n🔸 {strategy.upper()} Performance Evolution:")
            for _, row in strategy_data.iterrows():
                print(f"   Run {row['run_id']} ({row['file']}): "
                      f"Return {row['total_return_%']:>7.2f}%, "
                      f"Sharpe {row['sharpe_ratio']:>6.4f}")
            
            strategy_comparison.append({
                'strategy': strategy,
                'runs': len(strategy_data),
                'avg_return': strategy_data['total_return_%'].mean(),
                'best_return': strategy_data['total_return_%'].max(),
                'avg_sharpe': strategy_data['sharpe_ratio'].mean(),
                'best_sharpe': strategy_data['sharpe_ratio'].max()
            })
        
        # Plot comparison
        if strategy_comparison:
            comparison_df = pd.DataFrame(strategy_comparison)
            self.visualizer.plot_multiple_strategies(
                results_df=comparison_df.rename(columns={
                    'avg_return': 'total_return_%',
                    'avg_sharpe': 'sharpe_ratio'
                }),
                save_as=plot_file,
                show_plot=True
            )
            
            if save_plots:
                print(f"💾 Comparison plot saved: {plot_file}")
    
    def interactive_analysis(self, results_df):
        """Interactive analysis mode"""
        successful = results_df[results_df['status'] == 'Success'].copy()
        
        if successful.empty:
            print("❌ No successful strategies for interactive analysis!")
            return
        
        print("\n🔍 INTERACTIVE ANALYSIS MODE")
        print("="*40)
        print("Available strategies:")
        
        strategies = successful['strategy'].unique()
        for i, strategy in enumerate(strategies, 1):
            strategy_data = successful[successful['strategy'] == strategy].iloc[0]
            print(f"{i:2d}. {strategy:<15} (Return: {strategy_data['total_return_%']:>7.2f}%)")
        
        print(f"\n0. Compare all strategies")
        print("q. Quit")
        
        while True:
            try:
                choice = input("\nSelect strategy to analyze (number/q): ").strip()
                
                if choice.lower() == 'q':
                    break
                elif choice == '0':
                    self.plot_single_results(results_df, save_plots=True)
                elif choice.isdigit() and 1 <= int(choice) <= len(strategies):
                    strategy_name = strategies[int(choice) - 1]
                    strategy_data = successful[successful['strategy'] == strategy_name]
                    
                    print(f"\n📊 Detailed analysis for {strategy_name.upper()}:")
                    row = strategy_data.iloc[0]
                    
                    for key, value in row.items():
                        if key not in ['strategy', 'status', 'file', 'run_id']:
                            print(f"   {key:<20}: {value}")
                    
                    # Ask if user wants to generate plots
                    plot_choice = input("Generate detailed plots? (y/n): ").strip().lower()
                    if plot_choice == 'y':
                        print("📈 Note: Detailed plots require original data and trade history.")
                        print("    Use 'python strategy_tester.py --strategy {strategy} --plot' for full visualization.")
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(description='Interactive Bitcoin Strategy Results Plotter')
    parser.add_argument('files', nargs='*', 
                       help='CSV results files to plot')
    parser.add_argument('--latest', action='store_true',
                       help='Plot the most recent results file')
    parser.add_argument('--compare', action='store_true',
                       help='Compare multiple results files')
    parser.add_argument('--save-plots', action='store_true',
                       help='Save plots to files')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive analysis mode')
    parser.add_argument('--results-dir', default='results',
                       help='Results directory (default: results)')
    
    args = parser.parse_args()
    
    plotter = ResultsPlotter()
    
    # Determine which files to process
    if args.latest:
        file_path = plotter.find_latest_results(args.results_dir)
        if not file_path:
            return
        results_df = plotter.load_results(file_path)
    elif args.files:
        if args.compare and len(args.files) > 1:
            plotter.compare_results(args.files, save_plots=args.save_plots)
            return
        else:
            results_df = plotter.load_results(args.files[0])
    else:
        # No files specified, try to find latest
        file_path = plotter.find_latest_results(args.results_dir)
        if not file_path:
            print("❌ No results files found. Run strategy_tester.py first!")
            return
        results_df = plotter.load_results(file_path)
    
    if results_df is None:
        return
    
    # Run analysis
    if args.interactive:
        plotter.interactive_analysis(results_df)
    else:
        plotter.plot_single_results(results_df, save_plots=args.save_plots)


if __name__ == '__main__':
    main()