import backtrader as bt
import pandas as pd


class RSIMeanReversionStrategy(bt.Strategy):
    """
    RSI均值回归策略
    
    策略逻辑:
    - RSI < 30: 超卖，买入信号
    - RSI > 70: 超买，卖出信号
    - 使用止损和止盈保护
    """
    
    params = (
        ('rsi_period', 14),        # RSI周期
        ('rsi_oversold', 30),      # 超卖阈值
        ('rsi_overbought', 70),    # 超买阈值
        ('stop_loss', 0.05),       # 止损比例 (5%)
        ('take_profit', 0.10),     # 止盈比例 (10%)
        ('position_size', 0.95),   # 仓位大小比例
        ('print_log', True),       # 是否打印日志
    )
    
    def __init__(self):
        # 添加RSI指标
        self.rsi = bt.indicators.RSI(
            self.data.close, 
            period=self.params.rsi_period
        )
        
        # 跟踪订单和价格
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        
        # 性能跟踪
        self.trades = []
        
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
        current_rsi = self.rsi[0]
        
        # 记录指标数据用于可视化
        self.indicator_data.append({
            'date': self.datas[0].datetime.date(0),
            'Open': self.data.open[0],
            'High': self.data.high[0], 
            'Low': self.data.low[0],
            'Close': current_price,
            'Volume': self.data.volume[0],
            'rsi': current_rsi
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
        
        # 买入条件：RSI超卖
        if not self.position and current_rsi < self.params.rsi_oversold:
            # 计算买入数量
            available_cash = self.broker.getcash()
            size = (available_cash * self.params.position_size) / current_price
            
            self.log(f'买入信号: RSI={current_rsi:.2f}, 价格={current_price:.2f}')
            self.order = self.buy(size=size)
        
        # 卖出条件：RSI超买或止损/止盈
        elif self.position:
            # 计算收益率
            if self.buy_price:
                return_pct = (current_price - self.buy_price) / self.buy_price
                
                # RSI超买信号
                if current_rsi > self.params.rsi_overbought:
                    self.log(f'卖出信号(RSI超买): RSI={current_rsi:.2f}, 价格={current_price:.2f}')
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
            'signals': pd.DataFrame([])  # RSI没有专门的信号记录
        }
    
    def stop(self):
        """策略结束时的统计"""
        if self.params.print_log and self.trades:
            trades_df = pd.DataFrame(self.trades)
            win_rate = len(trades_df[trades_df['pnl'] > 0]) / len(trades_df)
            avg_return = trades_df['pnl_pct'].mean()
            
            self.log('='*50)
            self.log(f'策略统计 (RSI={self.params.rsi_period}, '
                    f'超卖={self.params.rsi_oversold}, '
                    f'超买={self.params.rsi_overbought}):')
            self.log(f'总交易次数: {len(trades_df)}')
            self.log(f'胜率: {win_rate:.2%}')
            self.log(f'平均收益率: {avg_return:.2f}%')
            self.log(f'最终资金: {self.broker.getvalue():.2f}')


if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from btc_data import BTCDataFeed
    
    # 创建回测引擎
    cerebro = bt.Cerebro()
    
    # 添加策略
    cerebro.addstrategy(RSIMeanReversionStrategy)
    
    # 获取比特币数据
    btc_feed = BTCDataFeed()
    bt_data, _ = btc_feed.get_backtrader_data("2022-01-01", "2023-12-31")
    cerebro.adddata(bt_data)
    
    # 设置初始资金和手续费
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% 手续费
    
    # 运行回测
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')
    cerebro.run()
    print(f'最终资金: {cerebro.broker.getvalue():.2f}')
    
    # 绘制结果
    cerebro.plot(style='candlestick', volume=False)