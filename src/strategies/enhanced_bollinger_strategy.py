import backtrader as bt
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.enhanced_visualization import EnhancedStrategyMixin


class EnhancedBollingerBandsStrategy(bt.Strategy, EnhancedStrategyMixin):
    """
    增强版布林带策略 - 集成Backtrader原生绘图和自定义可视化
    
    策略逻辑:
    - 价格突破布林带上轨: 买入信号(突破策略)
    - 价格跌破布林带下轨: 卖出信号
    - 集成增强的可视化功能
    """
    
    params = (
        ('bb_period', 20),         # 布林带周期
        ('bb_dev', 2.0),          # 标准差倍数
        ('strategy_type', 'breakout'), # 'breakout' 或 'mean_reversion'
        ('volume_filter', True),   # 是否使用成交量过滤
        ('volume_threshold', 1.2), # 成交量阈值倍数
        ('stop_loss', 0.06),      # 止损比例
        ('take_profit', 0.12),    # 止盈比例
        ('position_size', 0.95),  # 仓位大小比例
        ('print_log', True),      # 是否打印日志
    )
    
    def __init__(self):
        # 初始化可视化功能
        self.__init_visualization__()
        
        # 添加布林带指标
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev,
            subplot=False  # 在主图上显示
        )
        
        # 布林带组件
        self.bb_top = self.bb.top
        self.bb_mid = self.bb.mid    # 中轨(移动平均线)
        self.bb_bot = self.bb.bot
        
        # 设置布林带绘图属性
        try:
            self.bb_top.plotinfo.plotname = 'BB Upper'
            self.bb_mid.plotinfo.plotname = 'BB Middle'
            self.bb_bot.plotinfo.plotname = 'BB Lower'
            
            # 设置颜色
            self.bb_top.plotinfo.plotlinestyle = '--'
            self.bb_bot.plotinfo.plotlinestyle = '--'
            self.bb_top.plotinfo.plotcolor = 'red'
            self.bb_mid.plotinfo.plotcolor = 'blue'
            self.bb_bot.plotinfo.plotcolor = 'red'
        except AttributeError:
            # Fallback for older Backtrader versions
            pass
        
        # 成交量指标
        if self.params.volume_filter:
            self.volume_ma = bt.indicators.SMA(
                self.data.volume, 
                period=self.params.bb_period
            )
            try:
                self.volume_ma.plotinfo.subplot = True  # 在子图中显示
                self.volume_ma.plotinfo.plotname = 'Volume MA'
                self.volume_ma.plotinfo.plotcolor = 'purple'
            except AttributeError:
                pass
        
        # 价格位置指标(价格在布林带中的相对位置)
        self.bb_position = (self.data.close - self.bb_bot) / (self.bb_top - self.bb_bot)
        
        # 添加布林带宽度指标
        self.bb_width = (self.bb_top - self.bb_bot) / self.bb_mid
        try:
            self.bb_width.plotinfo.subplot = True
            self.bb_width.plotinfo.plotname = 'BB Width'
            self.bb_width.plotinfo.plotcolor = 'orange'
        except AttributeError:
            pass
        
        # 添加布林带位置指标到子图
        try:
            self.bb_position.plotinfo.subplot = True
            self.bb_position.plotinfo.plotname = 'BB Position'
            self.bb_position.plotinfo.plotcolor = 'green'
            # 添加水平线到BB Position子图
            self.bb_position.plotinfo.plothlines = [0.0, 0.5, 1.0]
        except AttributeError:
            pass
        
        # 创建买卖信号指标用于绘图
        self.buy_signal = bt.indicators.If(
            bt.indicators.CrossOver(self.data.close, self.bb_top),
            self.data.close, float('nan')
        )
        try:
            self.buy_signal.plotinfo.plot = True
            self.buy_signal.plotinfo.plotmaster = self.data
            self.buy_signal.plotinfo.plotname = 'Buy Signals'
            self.buy_signal.plotinfo.marker = '^'
            self.buy_signal.plotinfo.markersize = 8.0
            self.buy_signal.plotinfo.color = 'green'
            self.buy_signal.plotinfo.fillstyle = 'full'
        except AttributeError:
            pass
        
        self.sell_signal = bt.indicators.If(
            bt.indicators.CrossDown(self.data.close, self.bb_bot),
            self.data.close, float('nan')
        )
        try:
            self.sell_signal.plotinfo.plot = True
            self.sell_signal.plotinfo.plotmaster = self.data
            self.sell_signal.plotinfo.plotname = 'Sell Signals'
            self.sell_signal.plotinfo.marker = 'v'
            self.sell_signal.plotinfo.markersize = 8.0
            self.sell_signal.plotinfo.color = 'red'
            self.sell_signal.plotinfo.fillstyle = 'full'
        except AttributeError:
            pass
        
        # 跟踪订单和价格
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        
        # 性能跟踪
        self.trades = []
        self.signals = []
        
        # 可视化数据收集
        self.trade_points = []
        self.indicator_data = []
        self.portfolio_values = []
        
    def log(self, txt, dt=None):
        """日志记录"""
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行: 价格 {order.executed.price:.2f}, '
                        f'数量 {order.executed.size:.6f}, '
                        f'手续费 {order.executed.comm:.2f}')
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
                
                # 记录买点
                self.trade_points.append({
                    'date': self.datas[0].datetime.date(0),
                    'type': 'buy',
                    'price': order.executed.price,
                    'size': order.executed.size,
                    'commission': order.executed.comm
                })
                self.visualization_data['trade_points'].append({
                    'date': self.datas[0].datetime.date(0),
                    'type': 'buy',
                    'price': order.executed.price,
                    'size': order.executed.size,
                    'commission': order.executed.comm
                })
                
            elif order.issell():
                self.log(f'卖出执行: 价格 {order.executed.price:.2f}, '
                        f'数量 {order.executed.size:.6f}, '
                        f'手续费 {order.executed.comm:.2f}')
                
                # 记录卖点
                self.trade_points.append({
                    'date': self.datas[0].datetime.date(0),
                    'type': 'sell', 
                    'price': order.executed.price,
                    'size': order.executed.size,
                    'commission': order.executed.comm
                })
                self.visualization_data['trade_points'].append({
                    'date': self.datas[0].datetime.date(0),
                    'type': 'sell', 
                    'price': order.executed.price,
                    'size': order.executed.size,
                    'commission': order.executed.comm
                })
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单被取消/拒绝')
        
        self.order = None
    
    def notify_trade(self, trade):
        """交易完成通知"""
        if not trade.isclosed:
            return
        
        profit_loss = trade.pnl
        profit_pct = (profit_loss / trade.price) * 100
        
        self.log(f'交易盈亏: {profit_loss:.2f} ({profit_pct:.2f}%)')
        
        # 记录交易数据
        trade_data = {
            'date': self.datas[0].datetime.date(0),
            'pnl': profit_loss,
            'pnl_pct': profit_pct,
            'price': trade.price
        }
        self.trades.append(trade_data)
        self.visualization_data['trades'].append(trade_data)
    
    def check_volume_condition(self):
        """检查成交量条件"""
        if not self.params.volume_filter:
            return True
        
        current_volume = self.data.volume[0]
        avg_volume = self.volume_ma[0]
        
        return current_volume >= (avg_volume * self.params.volume_threshold)
    
    def next(self):
        """策略主逻辑"""
        current_price = self.data.close[0]
        bb_top = self.bb_top[0]
        bb_mid = self.bb_mid[0]
        bb_bot = self.bb_bot[0]
        bb_width = (bb_top - bb_bot) / bb_mid
        bb_pos = (current_price - bb_bot) / (bb_top - bb_bot)
        
        # 记录信号数据
        signal_data = {
            'date': self.datas[0].datetime.date(0),
            'price': current_price,
            'bb_upper': bb_top,
            'bb_middle': bb_mid,
            'bb_lower': bb_bot,
            'bb_width': bb_width,
            'bb_position': bb_pos
        }
        self.signals.append(signal_data)
        
        # 使用增强的数据记录功能
        self.log_visualization_data({
            'bb_upper': bb_top,
            'bb_middle': bb_mid, 
            'bb_lower': bb_bot,
            'bb_width': bb_width,
            'bb_position': bb_pos
        })
        
        # 记录指标数据用于传统可视化
        self.indicator_data.append({
            'date': self.datas[0].datetime.date(0),
            'Open': self.data.open[0],
            'High': self.data.high[0], 
            'Low': self.data.low[0],
            'Close': current_price,
            'Volume': self.data.volume[0] if hasattr(self.data, 'volume') else 0,
            'bb_upper': bb_top,
            'bb_middle': bb_mid,
            'bb_lower': bb_bot,
            'bb_width': bb_width,
            'bb_position': bb_pos
        })
        
        # 记录组合价值
        self.portfolio_values.append({
            'date': self.datas[0].datetime.date(0),
            'value': self.broker.getvalue(),
            'cash': self.broker.getcash(),
            'position_value': self.broker.getvalue() - self.broker.getcash()
        })
        
        # 如果有挂单，等待执行
        if self.order:
            return
        
        # 策略逻辑
        if self.params.strategy_type == 'breakout':
            self._breakout_logic(current_price, bb_top, bb_bot, bb_pos)
        else:  # mean_reversion
            self._mean_reversion_logic(current_price, bb_top, bb_bot, bb_pos)
    
    def _breakout_logic(self, current_price, bb_top, bb_bot, bb_pos):
        """突破策略逻辑"""
        # 买入条件：突破上轨 + 成交量确认
        if (not self.position and 
            current_price > bb_top and 
            bb_pos > 1.0 and 
            self.check_volume_condition()):
            
            available_cash = self.broker.getcash()
            size = (available_cash * self.params.position_size) / current_price
            
            self.log(f'买入信号(突破上轨): 价格={current_price:.2f}, '
                    f'上轨={bb_top:.2f}, 布林位置={bb_pos:.3f}')
            self.order = self.buy(size=size)
        
        # 卖出条件：跌破下轨或止损/止盈
        elif self.position:
            if self.buy_price:
                return_pct = (current_price - self.buy_price) / self.buy_price
                
                # 跌破下轨
                if current_price < bb_bot and bb_pos < 0.0:
                    self.log(f'卖出信号(跌破下轨): 价格={current_price:.2f}, 下轨={bb_bot:.2f}')
                    self.order = self.sell(size=self.position.size)
                
                # 止损
                elif return_pct < -self.params.stop_loss:
                    self.log(f'止损卖出: 亏损{return_pct*100:.2f}%, 价格={current_price:.2f}')
                    self.order = self.sell(size=self.position.size)
                
                # 止盈
                elif return_pct > self.params.take_profit:
                    self.log(f'止盈卖出: 盈利{return_pct*100:.2f}%, 价格={current_price:.2f}')
                    self.order = self.sell(size=self.position.size)
    
    def _mean_reversion_logic(self, current_price, bb_top, bb_bot, bb_pos):
        """均值回归策略逻辑"""
        # 买入条件：触及下轨(超卖)
        if (not self.position and 
            bb_pos < 0.1 and 
            self.check_volume_condition()):
            
            available_cash = self.broker.getcash()
            size = (available_cash * self.params.position_size) / current_price
            
            self.log(f'买入信号(触及下轨): 价格={current_price:.2f}, '
                    f'下轨={bb_bot:.2f}, 布林位置={bb_pos:.3f}')
            self.order = self.buy(size=size)
        
        # 卖出条件：触及上轨(超买)或止损/止盈
        elif self.position:
            if self.buy_price:
                return_pct = (current_price - self.buy_price) / self.buy_price
                
                # 触及上轨
                if bb_pos > 0.9:
                    self.log(f'卖出信号(触及上轨): 价格={current_price:.2f}, 上轨={bb_top:.2f}')
                    self.order = self.sell(size=self.position.size)
                
                # 止损
                elif return_pct < -self.params.stop_loss:
                    self.log(f'止损卖出: 亏损{return_pct*100:.2f}%, 价格={current_price:.2f}')
                    self.order = self.sell(size=self.position.size)
                
                # 止盈
                elif return_pct > self.params.take_profit:
                    self.log(f'止盈卖出: 盈利{return_pct*100:.2f}%, 价格={current_price:.2f}')
                    self.order = self.sell(size=self.position.size)
    
    def get_visualization_data(self):
        """获取可视化所需的数据(兼容旧接口)"""
        return {
            'indicator_data': pd.DataFrame(self.indicator_data),
            'trade_points': self.trade_points,
            'portfolio_values': pd.DataFrame(self.portfolio_values),
            'trades': self.trades,
            'signals': pd.DataFrame(self.signals)
        }
    
    def stop(self):
        """策略结束时的统计"""
        if self.params.print_log and self.trades:
            trades_df = pd.DataFrame(self.trades)
            win_rate = len(trades_df[trades_df['pnl'] > 0]) / len(trades_df)
            avg_return = trades_df['pnl_pct'].mean()
            avg_bb_width = pd.DataFrame(self.signals)['bb_width'].mean()
            
            self.log('='*50)
            self.log(f'策略统计 (布林带{self.params.bb_period}周期, '
                    f'{self.params.bb_dev}倍标准差):')
            self.log(f'策略类型: {self.params.strategy_type}')
            self.log(f'总交易次数: {len(trades_df)}')
            self.log(f'胜率: {win_rate:.2%}')
            self.log(f'平均收益率: {avg_return:.2f}%')
            self.log(f'平均布林带宽度: {avg_bb_width:.4f}')
            self.log(f'最终资金: {self.broker.getvalue():.2f}')


# 为了向后兼容，创建别名
BollingerBandsStrategy = EnhancedBollingerBandsStrategy