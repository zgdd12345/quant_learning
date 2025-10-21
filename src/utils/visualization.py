"""
Bitcoin Strategy Visualization Utilities
比特币策略可视化工具

This module provides comprehensive visualization tools for Bitcoin trading strategy analysis,
including performance charts, trade points, technical indicators, and comparative analysis.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class StrategyVisualizer:
    """Bitcoin strategy visualization toolkit"""
    
    def __init__(self, save_path="."):
        """
        Initialize visualizer
        
        Args:
            save_path: Directory to save plots
        """
        self.save_path = save_path
        self.colors = {
            'buy': '#2E7D32',      # Green
            'sell': '#D32F2F',     # Red  
            'price': '#1565C0',    # Blue
            'strategy': '#FF6F00', # Orange
            'baseline': '#424242'  # Gray
        }
        
        # Create save directory if it doesn't exist
        import os
        os.makedirs(save_path, exist_ok=True)
    
    def plot_strategy_performance(self, data, trades, strategy_name, 
                                save_as=None, show_plot=True):
        """
        Plot strategy performance with buy/sell points
        
        Args:
            data: DataFrame with OHLCV data and indicators
            trades: List of trade dictionaries with buy/sell points
            strategy_name: Name of the strategy
            save_as: Filename to save plot
            show_plot: Whether to display plot
        """
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
        
        # Prepare data
        if isinstance(data.index, pd.DatetimeIndex):
            dates = data.index
        else:
            dates = pd.to_datetime(data.index)
        
        # Plot 1: Price and trade points
        ax1.plot(dates, data['Close'], label='BTC Price', 
                color=self.colors['price'], linewidth=1.5, alpha=0.8)
        
        # Add buy/sell points
        if trades:
            buy_dates, buy_prices = [], []
            sell_dates, sell_prices = [], []
            
            for trade in trades:
                if trade['type'] == 'buy':
                    buy_dates.append(trade['date'])
                    buy_prices.append(trade['price'])
                elif trade['type'] == 'sell':
                    sell_dates.append(trade['date'])
                    sell_prices.append(trade['price'])
            
            if buy_dates:
                ax1.scatter(buy_dates, buy_prices, color=self.colors['buy'], 
                           marker='^', s=100, alpha=0.8, label='Buy Points', zorder=5)
            if sell_dates:
                ax1.scatter(sell_dates, sell_prices, color=self.colors['sell'], 
                           marker='v', s=100, alpha=0.8, label='Sell Points', zorder=5)
        
        ax1.set_title(f'{strategy_name} - Bitcoin Price & Trade Points', fontsize=14, pad=20)
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Strategy vs Buy & Hold Performance
        initial_price = data['Close'].iloc[0]
        buy_hold_returns = data['Close'] / initial_price
        
        # Calculate strategy returns (placeholder - should be provided by strategy)
        strategy_returns = buy_hold_returns.copy()  # Placeholder
        
        ax2.plot(dates, buy_hold_returns, label='Buy & Hold BTC', 
                color=self.colors['baseline'], linewidth=2)
        ax2.plot(dates, strategy_returns, label=f'{strategy_name} Strategy', 
                color=self.colors['strategy'], linewidth=2)
        
        ax2.set_title('Performance Comparison', fontsize=14, pad=20)
        ax2.set_ylabel('Cumulative Returns', fontsize=12)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Drawdown
        running_max = strategy_returns.expanding().max()
        drawdown = (strategy_returns - running_max) / running_max * 100
        
        ax3.fill_between(dates, drawdown, 0, color='red', alpha=0.3)
        ax3.plot(dates, drawdown, color='red', linewidth=1)
        ax3.set_title('Strategy Drawdown', fontsize=14, pad=20)
        ax3.set_ylabel('Drawdown (%)', fontsize=12)
        ax3.set_xlabel('Date', fontsize=12)
        ax3.grid(True, alpha=0.3)
        
        # Format x-axis
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_as:
            # Use save_as as direct filename if it contains extension, otherwise add PNG
            if save_as.endswith('.html'):
                png_file = save_as.replace('.html', '.png')
            else:
                png_file = f"{save_as}.png"
            plt.savefig(png_file, dpi=300, bbox_inches='tight')
            print(f"📊 Plot saved: {png_file}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_technical_indicators(self, data, strategy_name, indicators=None, 
                                 save_as=None, show_plot=True):
        """
        Plot technical indicators used by strategy
        
        Args:
            data: DataFrame with price and indicator data
            strategy_name: Name of the strategy  
            indicators: Dict of indicator configurations
            save_as: Filename to save plot
            show_plot: Whether to display plot
        """
        fig = plt.figure(figsize=(15, 10))
        
        if isinstance(data.index, pd.DatetimeIndex):
            dates = data.index
        else:
            dates = pd.to_datetime(data.index)
        
        # Determine layout based on strategy
        if 'bollinger' in strategy_name.lower():
            self._plot_bollinger_bands(fig, dates, data)
        elif 'macd' in strategy_name.lower():
            self._plot_macd_indicators(fig, dates, data)
        elif 'rsi' in strategy_name.lower():
            self._plot_rsi_indicators(fig, dates, data)
        else:
            # Generic price + moving averages
            self._plot_generic_indicators(fig, dates, data)
        
        plt.suptitle(f'{strategy_name} - Technical Indicators', fontsize=16, y=0.95)
        plt.tight_layout()
        
        if save_as:
            if save_as.endswith('.html'):
                png_file = save_as.replace('.html', '_indicators.png')
            else:
                png_file = f"{save_as}_indicators.png"
            plt.savefig(png_file, dpi=300, bbox_inches='tight')
            print(f"📊 Indicators plot saved: {png_file}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def _plot_bollinger_bands(self, fig, dates, data):
        """Plot Bollinger Bands indicators"""
        ax1 = plt.subplot(2, 1, 1)
        
        # Price and Bollinger Bands
        ax1.plot(dates, data['Close'], label='BTC Price', color=self.colors['price'])
        
        if 'bb_upper' in data.columns:
            ax1.plot(dates, data['bb_upper'], 'r--', alpha=0.7, label='BB Upper')
            ax1.plot(dates, data['bb_middle'], 'g-', alpha=0.7, label='BB Middle') 
            ax1.plot(dates, data['bb_lower'], 'r--', alpha=0.7, label='BB Lower')
            ax1.fill_between(dates, data['bb_upper'], data['bb_lower'], 
                           alpha=0.1, color='gray', label='BB Channel')
        
        ax1.set_ylabel('Price ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Bollinger Band Width
        ax2 = plt.subplot(2, 1, 2)
        if 'bb_width' in data.columns:
            ax2.plot(dates, data['bb_width'], color='purple', label='BB Width')
            ax2.fill_between(dates, data['bb_width'], alpha=0.3, color='purple')
        
        ax2.set_ylabel('BB Width')
        ax2.set_xlabel('Date')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    def _plot_macd_indicators(self, fig, dates, data):
        """Plot MACD indicators"""
        ax1 = plt.subplot(3, 1, 1)
        ax1.plot(dates, data['Close'], label='BTC Price', color=self.colors['price'])
        ax1.set_ylabel('Price ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # MACD Line
        ax2 = plt.subplot(3, 1, 2)
        if 'macd' in data.columns and 'macd_signal' in data.columns:
            ax2.plot(dates, data['macd'], label='MACD', color='blue')
            ax2.plot(dates, data['macd_signal'], label='Signal', color='red')
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax2.set_ylabel('MACD')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # MACD Histogram
        ax3 = plt.subplot(3, 1, 3)
        if 'macd_hist' in data.columns:
            colors = ['green' if x >= 0 else 'red' for x in data['macd_hist']]
            ax3.bar(dates, data['macd_hist'], color=colors, alpha=0.7)
        ax3.set_ylabel('MACD Histogram')
        ax3.set_xlabel('Date')
        ax3.grid(True, alpha=0.3)
    
    def _plot_rsi_indicators(self, fig, dates, data):
        """Plot RSI indicators"""
        ax1 = plt.subplot(2, 1, 1)
        ax1.plot(dates, data['Close'], label='BTC Price', color=self.colors['price'])
        ax1.set_ylabel('Price ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # RSI
        ax2 = plt.subplot(2, 1, 2)
        if 'rsi' in data.columns:
            ax2.plot(dates, data['rsi'], label='RSI', color='purple')
            ax2.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Overbought (70)')
            ax2.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Oversold (30)')
            ax2.fill_between(dates, 70, 100, alpha=0.1, color='red')
            ax2.fill_between(dates, 0, 30, alpha=0.1, color='green')
        
        ax2.set_ylabel('RSI')
        ax2.set_xlabel('Date')
        ax2.set_ylim(0, 100)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    def _plot_generic_indicators(self, fig, dates, data):
        """Plot generic price and moving averages"""
        ax = plt.subplot(1, 1, 1)
        ax.plot(dates, data['Close'], label='BTC Price', color=self.colors['price'])
        
        # Look for common moving average columns
        ma_columns = [col for col in data.columns if 'MA' in col or 'sma' in col.lower()]
        colors = ['red', 'green', 'orange', 'purple']
        
        for i, col in enumerate(ma_columns[:4]):
            color = colors[i % len(colors)]
            ax.plot(dates, data[col], label=col, color=color, alpha=0.7)
        
        ax.set_ylabel('Price ($)')
        ax.set_xlabel('Date')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def plot_multiple_strategies(self, results_df, save_as=None, show_plot=True):
        """
        Plot comparison of multiple strategies
        
        Args:
            results_df: DataFrame with strategy comparison results
            save_as: Filename to save plot
            show_plot: Whether to display plot
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Filter successful strategies
        successful = results_df[results_df['status'] == 'Success'].copy()
        
        if successful.empty:
            print("No successful strategies to plot")
            return
        
        # 1. Total Returns Bar Chart
        ax1.bar(successful['strategy'], successful['total_return_%'], 
                color=sns.color_palette("husl", len(successful)))
        ax1.set_title('Total Returns by Strategy', fontsize=14)
        ax1.set_ylabel('Return (%)')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Sharpe Ratio Comparison
        ax2.bar(successful['strategy'], successful['sharpe_ratio'],
                color=sns.color_palette("viridis", len(successful)))
        ax2.set_title('Sharpe Ratio by Strategy', fontsize=14)
        ax2.set_ylabel('Sharpe Ratio')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Max Drawdown
        ax3.bar(successful['strategy'], successful['max_drawdown_%'], 
                color=sns.color_palette("Reds_r", len(successful)))
        ax3.set_title('Maximum Drawdown by Strategy', fontsize=14)
        ax3.set_ylabel('Max Drawdown (%)')
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. Win Rate vs Return Scatter
        ax4.scatter(successful['win_rate_%'], successful['total_return_%'],
                   s=successful['total_trades']*10, alpha=0.7,
                   c=range(len(successful)), cmap='plasma')
        for i, row in successful.iterrows():
            ax4.annotate(row['strategy'], (row['win_rate_%'], row['total_return_%']),
                        xytext=(5, 5), textcoords='offset points', fontsize=9)
        ax4.set_title('Win Rate vs Returns (Size = # Trades)', fontsize=14)
        ax4.set_xlabel('Win Rate (%)')
        ax4.set_ylabel('Total Return (%)')
        ax4.grid(True, alpha=0.3)
        
        plt.suptitle('Bitcoin Strategy Performance Comparison', fontsize=16, y=0.95)
        plt.tight_layout()
        
        if save_as:
            if save_as.endswith('.html'):
                png_file = save_as.replace('.html', '.png')
            else:
                png_file = f"{save_as}.png"
            plt.savefig(png_file, dpi=300, bbox_inches='tight')
            print(f"📊 Comparison plot saved: {png_file}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def create_interactive_dashboard(self, data, trades, strategy_results, 
                                   strategy_name, save_as=None):
        """
        Create interactive Plotly dashboard
        
        Args:
            data: DataFrame with OHLCV and indicators
            trades: List of trade records
            strategy_results: Dict with strategy performance metrics
            strategy_name: Name of the strategy
            save_as: Filename to save HTML dashboard
        """
        # Create subplot layout
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Price & Trade Points', 'Performance Comparison', 
                          'Technical Indicators', 'Trade Statistics'),
            row_heights=[0.4, 0.25, 0.25, 0.1]
        )
        
        # Prepare dates
        if isinstance(data.index, pd.DatetimeIndex):
            dates = data.index
        else:
            dates = pd.to_datetime(data.index)
        
        # 1. Price chart with candlesticks
        fig.add_trace(
            go.Candlestick(
                x=dates,
                open=data['Open'],
                high=data['High'], 
                low=data['Low'],
                close=data['Close'],
                name='BTC Price'
            ),
            row=1, col=1
        )
        
        # Add trade points
        if trades:
            buy_dates = [t['date'] for t in trades if t['type'] == 'buy']
            buy_prices = [t['price'] for t in trades if t['type'] == 'buy']
            sell_dates = [t['date'] for t in trades if t['type'] == 'sell']  
            sell_prices = [t['price'] for t in trades if t['type'] == 'sell']
            
            if buy_dates:
                fig.add_trace(
                    go.Scatter(x=buy_dates, y=buy_prices, mode='markers',
                             marker=dict(symbol='triangle-up', size=15, color='green'),
                             name='Buy Points'),
                    row=1, col=1
                )
            
            if sell_dates:
                fig.add_trace(
                    go.Scatter(x=sell_dates, y=sell_prices, mode='markers',
                             marker=dict(symbol='triangle-down', size=15, color='red'),
                             name='Sell Points'),
                    row=1, col=1
                )
        
        # 2. Performance comparison
        initial_price = data['Close'].iloc[0]
        buy_hold = data['Close'] / initial_price
        
        fig.add_trace(
            go.Scatter(x=dates, y=buy_hold, name='Buy & Hold BTC', 
                      line=dict(color='gray')),
            row=2, col=1
        )
        
        # 3. Add technical indicators based on strategy
        self._add_interactive_indicators(fig, dates, data, strategy_name)
        
        # Update layout
        fig.update_layout(
            title=f'{strategy_name} - Interactive Analysis Dashboard',
            height=1000,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )
        
        # Update y-axis labels
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Cumulative Returns", row=2, col=1)
        fig.update_yaxes(title_text="Indicator Value", row=3, col=1)
        
        if save_as:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{save_as}_dashboard_{timestamp}.html"
            fig.write_html(f"{self.save_path}/{filename}")
            print(f"📊 Interactive dashboard saved: {self.save_path}/{filename}")
        
        return fig
    
    def _add_interactive_indicators(self, fig, dates, data, strategy_name):
        """Add strategy-specific indicators to interactive chart"""
        
        if 'bollinger' in strategy_name.lower():
            # Bollinger Bands
            if 'bb_upper' in data.columns:
                fig.add_trace(
                    go.Scatter(x=dates, y=data['bb_upper'], name='BB Upper',
                             line=dict(color='red', dash='dash')),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(x=dates, y=data['bb_lower'], name='BB Lower',
                             line=dict(color='red', dash='dash'), 
                             fill='tonexty', fillcolor='rgba(255,0,0,0.1)'),
                    row=1, col=1
                )
        
        elif 'macd' in strategy_name.lower():
            # MACD indicators
            if 'macd' in data.columns:
                fig.add_trace(
                    go.Scatter(x=dates, y=data['macd'], name='MACD',
                             line=dict(color='blue')),
                    row=3, col=1
                )
            if 'macd_signal' in data.columns:
                fig.add_trace(
                    go.Scatter(x=dates, y=data['macd_signal'], name='Signal',
                             line=dict(color='red')),
                    row=3, col=1
                )
        
        elif 'rsi' in strategy_name.lower():
            # RSI indicator
            if 'rsi' in data.columns:
                fig.add_trace(
                    go.Scatter(x=dates, y=data['rsi'], name='RSI',
                             line=dict(color='purple')),
                    row=3, col=1
                )
                # Add RSI levels
                fig.add_hline(y=70, line_dash="dash", line_color="red", 
                            annotation_text="Overbought", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green",
                            annotation_text="Oversold", row=3, col=1)
    
    def plot_monthly_returns_heatmap(self, trades, strategy_name, 
                                   save_as=None, show_plot=True):
        """
        Create monthly returns heatmap
        
        Args:
            trades: List of completed trades
            strategy_name: Name of the strategy
            save_as: Filename to save plot
            show_plot: Whether to display plot
        """
        if not trades:
            print("No trades data available for heatmap")
            return
        
        # Convert trades to DataFrame
        trades_df = pd.DataFrame(trades)
        trades_df['date'] = pd.to_datetime(trades_df['date'])
        trades_df['year'] = trades_df['date'].dt.year
        trades_df['month'] = trades_df['date'].dt.month
        
        # Calculate monthly returns
        monthly_returns = trades_df.groupby(['year', 'month'])['pnl_pct'].sum().unstack(fill_value=0)
        
        # Create heatmap
        plt.figure(figsize=(12, 8))
        sns.heatmap(monthly_returns, annot=True, fmt='.1f', cmap='RdYlGn',
                   center=0, cbar_kws={'label': 'Monthly Return (%)'})
        
        plt.title(f'{strategy_name} - Monthly Returns Heatmap', fontsize=14, pad=20)
        plt.ylabel('Year')
        plt.xlabel('Month')
        
        if save_as:
            if save_as.endswith('.html'):
                png_file = save_as.replace('.html', '_heatmap.png')
            else:
                png_file = f"{save_as}_heatmap.png"
            plt.savefig(png_file, dpi=300, bbox_inches='tight')
            print(f"📊 Heatmap saved: {png_file}")
        
        if show_plot:
            plt.show()
        else:
            plt.close()


def quick_plot_strategy(data, trades, strategy_name, show_indicators=True):
    """
    Quick plotting function for immediate visualization
    
    Args:
        data: DataFrame with OHLCV data
        trades: List of trade records
        strategy_name: Strategy name
        show_indicators: Whether to show technical indicators
    """
    visualizer = StrategyVisualizer()
    
    # Main performance plot
    visualizer.plot_strategy_performance(data, trades, strategy_name, 
                                       save_as=None, show_plot=True)
    
    # Technical indicators if requested
    if show_indicators:
        visualizer.plot_technical_indicators(data, strategy_name,
                                           save_as=None, show_plot=True)