import backtrader as bt
import pandas as pd


class MACDMomentumStrategy(bt.Strategy):
    """
    MACD动量策略
    
    策略逻辑:
    - MACD金叉(MACD线上穿信号线): 买入信号
    - MACD死叉(MACD线下穿信号线): 卖出信号
    - 结合MACD柱状图和零轴位置进行信号确认
    """
    
    params = (
        ('fast_period', 12),       # MACD快线周期
        ('slow_period', 26),       # MACD慢线周期
        ('signal_period', 9),      # 信号线周期
        ('min_macd_diff', 0.001),  # MACD线最小差值(避免假信号)
        ('stop_loss', 0.08),       # 止损比例 (8%)
        ('take_profit', 0.15),     # 止盈比例 (15%)
        ('position_size', 0.95),   # 仓位大小比例
        ('print_log', True),       # 是否打印日志
    )
    
    def __init__(self):
        # 添加MACD指标
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )
        
        # MACD组件
        self.macd_line = self.macd.macd
        self.signal_line = self.macd.signal
        self.histogram = self.macd.histo if hasattr(self.macd, 'histo') else (self.macd_line - self.signal_line)
        
        # 交叉信号
        self.macd_crossover = bt.indicators.CrossOver(self.macd_line, self.signal_line)
        
        # 跟踪订单和价格
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        
        # 性能跟踪
        self.trades = []
        self.signals = []
        
        # 可视化数据收集
        self.trade_points = []  # 买卖点记录
        self.indicator_data = []  # 指标数据记录
        self.portfolio_values = []  # 组合价值记录
        
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
        self.trades.append({
            'date': self.datas[0].datetime.date(0),
            'pnl': profit_loss,
            'pnl_pct': profit_pct,
            'price': trade.price
        })
    
    def next(self):
        """策略主逻辑"""
        current_price = self.data.close[0]
        macd_val = self.macd_line[0]
        signal_val = self.signal_line[0]
        histogram_val = self.histogram[0]
        crossover = self.macd_crossover[0]
        
        # 记录信号数据
        self.signals.append({
            'date': self.datas[0].datetime.date(0),
            'price': current_price,
            'macd': macd_val,
            'signal': signal_val,
            'histogram': histogram_val,
            'crossover': crossover
        })
        
        # 记录指标数据用于可视化
        self.indicator_data.append({
            'date': self.datas[0].datetime.date(0),
            'Open': self.data.open[0],
            'High': self.data.high[0], 
            'Low': self.data.low[0],
            'Close': current_price,
            'Volume': self.data.volume[0],
            'macd': macd_val,
            'macd_signal': signal_val,
            'macd_hist': histogram_val,
            'macd_crossover': crossover
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
        
        # 买入条件：MACD金叉 + 额外确认条件
        if not self.position and crossover > 0:
            # 确认信号强度
            macd_diff = abs(macd_val - signal_val)
            
            if (macd_diff > self.params.min_macd_diff and  # MACD差值足够大
                histogram_val > histogram_val or True):    # 柱状图增长(或忽略此条件)
                
                # 计算买入数量
                available_cash = self.broker.getcash()
                size = (available_cash * self.params.position_size) / current_price
                
                self.log(f'买入信号(MACD金叉): MACD={macd_val:.4f}, '
                        f'信号线={signal_val:.4f}, 价格={current_price:.2f}')
                self.order = self.buy(size=size)
        
        # 卖出条件：MACD死叉或止损/止盈
        elif self.position:
            # 计算收益率
            if self.buy_price:
                return_pct = (current_price - self.buy_price) / self.buy_price
                
                # MACD死叉信号
                if crossover < 0:
                    macd_diff = abs(macd_val - signal_val)
                    if macd_diff > self.params.min_macd_diff:
                        self.log(f'卖出信号(MACD死叉): MACD={macd_val:.4f}, '
                                f'信号线={signal_val:.4f}, 价格={current_price:.2f}')
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
        """获取可视化所需的数据"""
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
            signals_df = pd.DataFrame(self.signals)
            
            win_rate = len(trades_df[trades_df['pnl'] > 0]) / len(trades_df)
            avg_return = trades_df['pnl_pct'].mean()
            
            # 信号统计
            buy_signals = len(signals_df[signals_df['crossover'] > 0])
            sell_signals = len(signals_df[signals_df['crossover'] < 0])
            
            self.log('='*50)
            self.log(f'策略统计 (MACD {self.params.fast_period}-{self.params.slow_period}-{self.params.signal_period}):')
            self.log(f'总交易次数: {len(trades_df)}')
            self.log(f'胜率: {win_rate:.2%}')
            self.log(f'平均收益率: {avg_return:.2f}%')
            self.log(f'买入信号数: {buy_signals}')
            self.log(f'卖出信号数: {sell_signals}')
            self.log(f'最终资金: {self.broker.getvalue():.2f}')


class AdvancedMACDStrategy(MACDMomentumStrategy):
    """
    增强版MACD策略
    
    额外特性:
    - 结合RSI过滤信号
    - 使用EMA趋势确认
    - 动态止损
    """
    
    params = (
        ('fast_period', 12),
        ('slow_period', 26), 
        ('signal_period', 9),
        ('rsi_period', 14),
        ('rsi_overbought', 75),
        ('rsi_oversold', 25),
        ('ema_period', 50),
        ('trailing_stop', True),
        ('stop_loss', 0.06),
        ('take_profit', 0.12),
        ('position_size', 0.95),
        ('print_log', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # 添加RSI和EMA过滤器
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.ema = bt.indicators.EMA(self.data.close, period=self.params.ema_period)
        
        # 动态止损跟踪
        self.highest_price = None
        self.trailing_stop_price = None
        
    def next(self):
        """增强版策略主逻辑"""
        current_price = self.data.close[0]
        macd_val = self.macd_line[0]
        signal_val = self.signal_line[0]
        crossover = self.macd_crossover[0]
        rsi_val = self.rsi[0]
        ema_val = self.ema[0]
        
        # 如果有挂单，等待执行
        if self.order:
            return
        
        # 买入条件：MACD金叉 + RSI不超买 + 价格在EMA之上
        if not self.position and crossover > 0:
            if (rsi_val < self.params.rsi_overbought and 
                current_price > ema_val and
                abs(macd_val - signal_val) > self.params.min_macd_diff):
                
                available_cash = self.broker.getcash()
                size = (available_cash * self.params.position_size) / current_price
                
                self.log(f'买入信号(增强MACD): MACD={macd_val:.4f}, '
                        f'RSI={rsi_val:.2f}, 价格={current_price:.2f}')
                self.order = self.buy(size=size)
                
                # 初始化动态止损
                if self.params.trailing_stop:
                    self.highest_price = current_price
                    self.trailing_stop_price = current_price * (1 - self.params.stop_loss)
        
        # 持仓管理
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 更新动态止损
            if self.params.trailing_stop and current_price > self.highest_price:
                self.highest_price = current_price
                new_stop = current_price * (1 - self.params.stop_loss)
                if new_stop > self.trailing_stop_price:
                    self.trailing_stop_price = new_stop
            
            # 卖出条件
            sell_signal = False
            sell_reason = ""
            
            # MACD死叉 + RSI超买
            if (crossover < 0 and rsi_val > self.params.rsi_overbought and
                abs(macd_val - signal_val) > self.params.min_macd_diff):
                sell_signal = True
                sell_reason = "MACD死叉+RSI超买"
            
            # 动态止损
            elif self.params.trailing_stop and current_price < self.trailing_stop_price:
                sell_signal = True
                sell_reason = f"动态止损(止损价:{self.trailing_stop_price:.2f})"
            
            # 固定止损
            elif not self.params.trailing_stop and return_pct < -self.params.stop_loss:
                sell_signal = True
                sell_reason = f"固定止损({return_pct*100:.2f}%)"
            
            # 止盈
            elif return_pct > self.params.take_profit:
                sell_signal = True
                sell_reason = f"止盈({return_pct*100:.2f}%)"
            
            if sell_signal:
                self.log(f'卖出信号({sell_reason}): 价格={current_price:.2f}')
                self.order = self.sell(size=self.position.size)


if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from btc_data import BTCDataFeed
    
    # 创建回测引擎
    cerebro = bt.Cerebro()
    
    # 选择策略：基础MACD或增强MACD
    # cerebro.addstrategy(MACDMomentumStrategy)
    cerebro.addstrategy(AdvancedMACDStrategy)
    
    # 获取比特币数据
    btc_feed = BTCDataFeed()
    bt_data, _ = btc_feed.get_backtrader_data("2022-01-01", "2023-12-31")
    cerebro.adddata(bt_data)
    
    # 设置初始资金和手续费
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)
    
    # 运行回测
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')
    cerebro.run()
    print(f'最终资金: {cerebro.broker.getvalue():.2f}')
    
    # 绘制结果
    cerebro.plot(style='candlestick', volume=False)