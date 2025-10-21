"""
Enhanced Bitcoin Strategy Visualization with Backtrader Integration
增强版比特币策略可视化工具（集成Backtrader绘图功能）

This module provides enhanced visualization tools that leverage Backtrader's native plotting
capabilities along with custom interactive visualizations.
"""

import backtrader as bt
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
import os
import io
import base64
warnings.filterwarnings('ignore')

# Custom Backtrader plot styling
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class BacktraderPlotMixin:
    """Mixin class to add enhanced plotting capabilities to Backtrader strategies"""
    
    def setup_plotlines(self):
        """Setup custom plot lines for indicators"""
        # This should be called in strategy __init__
        self.plotinfo.subplot = False  # Plot on main price panel
        
        # Define custom plot lines for buy/sell signals
        if not hasattr(self, 'buy_signal'):
            self.buy_signal = bt.indicators.CrossOver(self.data.close, self.data.close)
            self.buy_signal.plotinfo.plot = False
            
        if not hasattr(self, 'sell_signal'):  
            self.sell_signal = bt.indicators.CrossOver(self.data.close, self.data.close)
            self.sell_signal.plotinfo.plot = False


class EnhancedStrategyVisualizer:
    """Enhanced Bitcoin strategy visualization toolkit with Backtrader integration"""
    
    def __init__(self, save_path="plots"):
        """
        Initialize enhanced visualizer
        
        Args:
            save_path: Directory to save plots
        """
        self.save_path = save_path
        self.colors = {
            'buy': '#2E7D32',      # Green
            'sell': '#D32F2F',     # Red  
            'price': '#1565C0',    # Blue
            'strategy': '#FF6F00', # Orange
            'baseline': '#424242', # Gray
            'indicator': '#9C27B0' # Purple
        }
        
        # Create save directory
        os.makedirs(save_path, exist_ok=True)
    
    def plot_backtrader_strategy(self, cerebro, strategy_result, strategy_name,
                               save_as=None, show_plot=True, plot_volume=True,
                               plot_indicators=True):
        """
        Use Backtrader's native plotting with enhanced styling
        
        Args:
            cerebro: Backtrader cerebro engine instance
            strategy_result: Strategy result from cerebro.run()
            strategy_name: Name of the strategy
            save_as: Filename to save plot
            show_plot: Whether to display plot
            plot_volume: Whether to plot volume
            plot_indicators: Whether to plot indicators
        """
        try:
            # Configure plot settings
            plot_config = {
                'style': 'candlestick',  # Use candlestick charts
                'volume': plot_volume,
                'plotdist': 0.1,  # Distance between subplots
                'barup': '#26A69A',    # Green candles  
                'bardown': '#EF5350',  # Red candles
                'volup': '#26A69A',    # Volume up color
                'voldown': '#EF5350',  # Volume down color
                'grid': True
            }
            
            # Apply custom styling to strategy
            if hasattr(strategy_result, 'plotinfo'):
                strategy_result.plotinfo.plotname = strategy_name
                
            # Plot using Backtrader
            figs = cerebro.plot(
                style=plot_config['style'],
                volume=plot_config['volume'],
                plotdist=plot_config['plotdist'],
                barup=plot_config['barup'],
                bardown=plot_config['bardown'],
                volup=plot_config['volup'],
                voldown=plot_config['voldown'],
                grid=plot_config['grid'],
                returnfig=True
            )
            
            # Enhance the plot
            if figs and len(figs) > 0:
                fig = figs[0][0]
                
                # Adjust figure size and DPI
                fig.set_size_inches(16, 10)
                fig.suptitle(f'{strategy_name} - Backtrader Analysis', 
                           fontsize=16, fontweight='bold', y=0.98)
                
                # Enhance subplot titles and formatting
                for ax in fig.get_axes():
                    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
                    ax.tick_params(axis='both', which='major', labelsize=10)
                    
                    # Format x-axis for better date display
                    if hasattr(ax, 'xaxis'):
                        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                        ax.tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                
                # Save plot
                if save_as:
                    if save_as.endswith('.html'):
                        png_file = save_as.replace('.html', '_backtrader.png')
                    else:
                        png_file = f"{save_as}_backtrader.png"
                    
                    fig.savefig(png_file, dpi=300, bbox_inches='tight',
                              facecolor='white', edgecolor='none')
                    print(f"📊 Backtrader plot saved: {png_file}")
                
                # Show plot
                if show_plot:
                    plt.show()
                else:
                    plt.close(fig)
            
            return figs
            
        except Exception as e:
            print(f"⚠️ Error creating Backtrader plot: {e}")
            return None
    
    def create_interactive_dashboard(self, data, trades, strategy_results, 
                                   strategy_name, indicators=None, save_as=None):
        """
        Create comprehensive interactive dashboard using Plotly
        
        Args:
            data: DataFrame with OHLCV data
            trades: List of trade dictionaries  
            strategy_results: Strategy performance metrics
            strategy_name: Name of the strategy
            indicators: Dictionary of indicator data
            save_as: Filename to save dashboard
        """
        # Create subplots with multiple rows
        subplot_titles = [
            f'{strategy_name} - Price & Trade Points',
            'Technical Indicators',
            'Portfolio Value & Drawdown', 
            'Trade Analysis'
        ]
        
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=subplot_titles,
            specs=[
                [{"secondary_y": True}],  # Price chart with volume
                [{"secondary_y": True}],  # Indicators  
                [{"secondary_y": True}],  # Portfolio metrics
                [{"type": "bar"}]         # Trade analysis
            ],
            vertical_spacing=0.08,
            row_heights=[0.4, 0.25, 0.25, 0.1]
        )
        
        # Prepare data
        if isinstance(data.index, pd.DatetimeIndex):
            dates = data.index
        else:
            dates = pd.to_datetime(data.index) if hasattr(data, 'index') else data.get('date', [])
        
        # 1. Candlestick chart with trades
        if 'Open' in data.columns and 'High' in data.columns:
            candlestick = go.Candlestick(
                x=dates,
                open=data['Open'],
                high=data['High'], 
                low=data['Low'],
                close=data['Close'],
                name='BTC Price',
                increasing_line_color='#26A69A',
                decreasing_line_color='#EF5350'
            )
            fig.add_trace(candlestick, row=1, col=1)
        else:
            # Fallback to line chart
            fig.add_trace(
                go.Scatter(x=dates, y=data.get('Close', []), 
                          mode='lines', name='BTC Price', 
                          line=dict(color=self.colors['price'])),
                row=1, col=1
            )
        
        # Add trade points
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
                fig.add_trace(
                    go.Scatter(x=buy_dates, y=buy_prices, mode='markers',
                              marker=dict(symbol='triangle-up', size=12, 
                                        color=self.colors['buy']),
                              name='Buy Points'), 
                    row=1, col=1
                )
            
            if sell_dates:
                fig.add_trace(
                    go.Scatter(x=sell_dates, y=sell_prices, mode='markers',
                              marker=dict(symbol='triangle-down', size=12,
                                        color=self.colors['sell']),
                              name='Sell Points'),
                    row=1, col=1
                )
        
        # Add volume on secondary y-axis
        if 'Volume' in data.columns:
            fig.add_trace(
                go.Bar(x=dates, y=data['Volume'], name='Volume',
                      marker_color='rgba(128,128,128,0.3)',
                      yaxis='y2'),
                row=1, col=1, secondary_y=True
            )
        
        # 2. Technical indicators
        if indicators is not None:
            indicator_data = indicators
            if isinstance(indicator_data, pd.DataFrame):
                # Plot strategy-specific indicators
                if strategy_name.lower().startswith('bollinger'):
                    if 'bb_upper' in indicator_data.columns:
                        fig.add_trace(
                            go.Scatter(x=dates, y=indicator_data['bb_upper'],
                                     name='BB Upper', line=dict(color='red', dash='dash')),
                            row=2, col=1
                        )
                    if 'bb_middle' in indicator_data.columns:
                        fig.add_trace(
                            go.Scatter(x=dates, y=indicator_data['bb_middle'],
                                     name='BB Middle', line=dict(color='blue')),
                            row=2, col=1
                        )
                    if 'bb_lower' in indicator_data.columns:
                        fig.add_trace(
                            go.Scatter(x=dates, y=indicator_data['bb_lower'],
                                     name='BB Lower', line=dict(color='red', dash='dash')),
                            row=2, col=1
                        )
                
                elif strategy_name.lower().startswith('rsi'):
                    if 'rsi' in indicator_data.columns:
                        fig.add_trace(
                            go.Scatter(x=dates, y=indicator_data['rsi'],
                                     name='RSI', line=dict(color=self.colors['indicator'])),
                            row=2, col=1
                        )
                        # Add RSI levels
                        fig.add_hline(y=70, line_dash="dash", line_color="red", 
                                    annotation_text="Overbought", row=2, col=1)
                        fig.add_hline(y=30, line_dash="dash", line_color="green",
                                    annotation_text="Oversold", row=2, col=1)
                
                elif strategy_name.lower().startswith('macd'):
                    if 'macd' in indicator_data.columns:
                        fig.add_trace(
                            go.Scatter(x=dates, y=indicator_data['macd'],
                                     name='MACD', line=dict(color='blue')),
                            row=2, col=1
                        )
                    if 'macd_signal' in indicator_data.columns:
                        fig.add_trace(
                            go.Scatter(x=dates, y=indicator_data['macd_signal'],
                                     name='Signal', line=dict(color='red')),
                            row=2, col=1
                        )
                    if 'macd_hist' in indicator_data.columns:
                        fig.add_trace(
                            go.Bar(x=dates, y=indicator_data['macd_hist'],
                                  name='Histogram', marker_color='gray'),
                            row=2, col=1
                        )
        
        # 3. Portfolio metrics
        if 'portfolio_values' in strategy_results:
            portfolio_data = strategy_results['portfolio_values']
            if isinstance(portfolio_data, pd.DataFrame):
                fig.add_trace(
                    go.Scatter(x=portfolio_data['date'], y=portfolio_data['value'],
                              name='Portfolio Value', 
                              line=dict(color=self.colors['strategy'])),
                    row=3, col=1
                )
                
                # Calculate and plot drawdown
                running_max = portfolio_data['value'].expanding().max()
                drawdown = (portfolio_data['value'] - running_max) / running_max * 100
                
                fig.add_trace(
                    go.Scatter(x=portfolio_data['date'], y=drawdown,
                              name='Drawdown %', fill='tonexty',
                              line=dict(color='red'), yaxis='y2'),
                    row=3, col=1, secondary_y=True
                )
        
        # 4. Trade analysis
        if trades:
            trade_pnl = []
            trade_dates = []
            trade_types = []
            
            for i, trade in enumerate(trades):
                if 'pnl' in trade:
                    trade_pnl.append(trade['pnl'])
                    trade_dates.append(f"Trade {i+1}")
                    trade_types.append('Profit' if trade['pnl'] > 0 else 'Loss')
            
            if trade_pnl:
                colors = ['green' if pnl > 0 else 'red' for pnl in trade_pnl]
                fig.add_trace(
                    go.Bar(x=trade_dates, y=trade_pnl, name='Trade P&L',
                          marker_color=colors),
                    row=4, col=1
                )
        
        # Update layout
        fig.update_layout(
            title=f'{strategy_name} - Comprehensive Analysis Dashboard',
            height=1200,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            template='plotly_white'
        )
        
        # Update y-axes labels
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", secondary_y=True, row=1, col=1)
        fig.update_yaxes(title_text="Indicator Value", row=2, col=1)
        fig.update_yaxes(title_text="Portfolio ($)", row=3, col=1)
        fig.update_yaxes(title_text="Drawdown %", secondary_y=True, row=3, col=1)
        fig.update_yaxes(title_text="P&L ($)", row=4, col=1)
        
        # Save and show
        if save_as:
            html_file = save_as if save_as.endswith('.html') else f"{save_as}.html"
            fig.write_html(html_file)
            print(f"📊 Interactive dashboard saved: {html_file}")
        
        return fig
    
    def create_strategy_comparison_plot(self, results_df, save_as=None, show_plot=True):
        """
        Create interactive strategy comparison using Plotly
        
        Args:
            results_df: DataFrame with strategy comparison results
            save_as: Filename to save plot
            show_plot: Whether to display plot
        """
        # Create subplots for different metrics
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Total Return Comparison',
                'Risk-Adjusted Performance (Sharpe Ratio)',
                'Maximum Drawdown',
                'Win Rate Analysis'
            ],
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "bar"}]
            ]
        )
        
        strategies = results_df['strategy'].tolist()
        
        # Total Return
        fig.add_trace(
            go.Bar(x=strategies, y=results_df['total_return_%'],
                  name='Total Return %', marker_color=self.colors['strategy']),
            row=1, col=1
        )
        
        # Sharpe Ratio  
        fig.add_trace(
            go.Bar(x=strategies, y=results_df['sharpe_ratio'],
                  name='Sharpe Ratio', marker_color=self.colors['buy']),
            row=1, col=2
        )
        
        # Max Drawdown (negative values, so flip colors)
        drawdown_colors = ['red' if dd > 20 else 'orange' if dd > 10 else 'green' 
                          for dd in results_df['max_drawdown_%']]
        fig.add_trace(
            go.Bar(x=strategies, y=results_df['max_drawdown_%'],
                  name='Max Drawdown %', marker_color=drawdown_colors),
            row=2, col=1
        )
        
        # Win Rate
        win_rate_colors = ['green' if wr > 50 else 'orange' if wr > 40 else 'red'
                          for wr in results_df.get('win_rate_%', [50] * len(strategies))]
        fig.add_trace(
            go.Bar(x=strategies, y=results_df.get('win_rate_%', [50] * len(strategies)),
                  name='Win Rate %', marker_color=win_rate_colors),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Bitcoin Strategy Performance Comparison",
            height=800,
            showlegend=False,
            template='plotly_white'
        )
        
        # Update y-axes
        fig.update_yaxes(title_text="Return %", row=1, col=1)
        fig.update_yaxes(title_text="Sharpe Ratio", row=1, col=2)
        fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
        fig.update_yaxes(title_text="Win Rate %", row=2, col=2)
        
        # Save and show
        if save_as:
            html_file = save_as if save_as.endswith('.html') else f"{save_as}.html"
            fig.write_html(html_file)
            print(f"📊 Strategy comparison saved: {html_file}")
            
        if show_plot:
            fig.show()
        
        return fig
    
    def plot_with_backtrader_and_custom(self, cerebro, strategy_result, data, trades,
                                      strategy_results, strategy_name, indicators=None,
                                      save_as=None, show_plot=True):
        """
        Combine Backtrader native plots with custom interactive visualizations
        
        Args:
            cerebro: Backtrader cerebro instance
            strategy_result: Strategy result 
            data: OHLCV data DataFrame
            trades: Trade list
            strategy_results: Strategy metrics
            strategy_name: Strategy name
            indicators: Indicator data
            save_as: Base filename for saving
            show_plot: Whether to show plots
        """
        print(f"📊 Creating comprehensive visualization for {strategy_name}...")
        
        # 1. Create Backtrader native plot
        print("   📈 Generating Backtrader native plot...")
        backtrader_figs = self.plot_backtrader_strategy(
            cerebro, strategy_result, strategy_name,
            save_as=f"{save_as}_backtrader" if save_as else None,
            show_plot=False
        )
        
        # 2. Create interactive dashboard
        print("   📊 Creating interactive dashboard...")
        dashboard_fig = self.create_interactive_dashboard(
            data, trades, strategy_results, strategy_name, 
            indicators=indicators,
            save_as=f"{save_as}_dashboard" if save_as else None
        )
        
        # 3. Show plots if requested
        if show_plot:
            if backtrader_figs:
                plt.show()
            if dashboard_fig:
                dashboard_fig.show()
        
        return backtrader_figs, dashboard_fig


# Enhanced strategy mixins for better visualization
class EnhancedStrategyMixin:
    """Mixin to add enhanced visualization capabilities to strategies"""
    
    def __init_visualization__(self):
        """Initialize visualization data collection"""
        self.visualization_data = {
            'trade_points': [],
            'indicator_data': [],
            'portfolio_values': [],
            'trades': [],
            'signals': []
        }
    
    def log_visualization_data(self, indicator_values=None):
        """Log data for visualization"""
        current_date = self.datas[0].datetime.date(0)
        current_price = self.data.close[0]
        
        # Base OHLCV data
        base_data = {
            'date': current_date,
            'Open': self.data.open[0],
            'High': self.data.high[0],
            'Low': self.data.low[0], 
            'Close': current_price,
            'Volume': self.data.volume[0] if hasattr(self.data, 'volume') else 0
        }
        
        # Add indicator values
        if indicator_values:
            base_data.update(indicator_values)
            
        self.visualization_data['indicator_data'].append(base_data)
        
        # Portfolio value
        self.visualization_data['portfolio_values'].append({
            'date': current_date,
            'value': self.broker.getvalue(),
            'cash': self.broker.getcash(),
            'position_value': self.broker.getvalue() - self.broker.getcash()
        })
    
    def get_enhanced_visualization_data(self):
        """Get all visualization data"""
        return {
            'indicator_data': pd.DataFrame(self.visualization_data['indicator_data']),
            'trade_points': self.visualization_data['trade_points'],
            'portfolio_values': pd.DataFrame(self.visualization_data['portfolio_values']),
            'trades': self.visualization_data['trades'],
            'signals': pd.DataFrame(self.visualization_data['signals'])
        }


def setup_backtrader_plot_styling():
    """Configure global Backtrader plot styling"""
    
    # Configure matplotlib for better plots
    plt.rcParams.update({
        'figure.figsize': (16, 10),
        'figure.dpi': 100,
        'savefig.dpi': 300,
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'grid.alpha': 0.3
    })


# Initialize plot styling
setup_backtrader_plot_styling()