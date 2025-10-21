import backtrader as bt
import pandas as pd


class BollingerBandsStrategy(bt.Strategy):
    """
    布林带突破策略
    
    策略逻辑:
    - 价格突破布林带上轨: 买入信号(突破策略)
    - 价格跌破布林带下轨: 卖出信号
    - 或者使用均值回归：价格触及上轨卖出，触及下轨买入
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
        # 添加布林带指标
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )
        
        # 布林带组件
        self.bb_top = self.bb.top
        self.bb_mid = self.bb.mid    # 中轨(移动平均线)
        self.bb_bot = self.bb.bot
        
        # 成交量过滤器
        if self.params.volume_filter:
            self.volume_ma = bt.indicators.SMA(
                self.data.volume, 
                period=self.params.bb_period
            )
        
        # 价格位置指标(价格在布林带中的相对位置)
        self.bb_position = (self.data.close - self.bb_bot) / (self.bb_top - self.bb_bot)
        
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
                        f'数量 {order.executed.size:.6f}')
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
                        f'数量 {order.executed.size:.6f}')
                
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
        
        self.trades.append({
            'date': self.datas[0].datetime.date(0),
            'pnl': profit_loss,
            'pnl_pct': profit_pct,
            'price': trade.price
        })
    
    def check_volume_condition(self):
        """检查成交量条件"""
        if not self.params.volume_filter:
            return True
        
        current_volume = self.data.volume[0]
        avg_volume = self.volume_ma[0]
        
        return current_volume > (avg_volume * self.params.volume_threshold)
    
    def next(self):
        """策略主逻辑"""
        current_price = self.data.close[0]
        bb_top = self.bb_top[0]
        bb_mid = self.bb_mid[0]
        bb_bot = self.bb_bot[0]
        bb_width = (bb_top - bb_bot) / bb_mid  # 布林带宽度
        bb_pos = self.bb_position[0]  # 价格在布林带中的位置(0-1)
        
        # 记录信号数据
        self.signals.append({
            'date': self.datas[0].datetime.date(0),
            'price': current_price,
            'bb_top': bb_top,
            'bb_mid': bb_mid,
            'bb_bot': bb_bot,
            'bb_width': bb_width,
            'bb_position': bb_pos
        })
        
        # 记录指标数据用于可视化
        self.indicator_data.append({
            'date': self.datas[0].datetime.date(0),
            'Open': self.data.open[0],
            'High': self.data.high[0], 
            'Low': self.data.low[0],
            'Close': current_price,
            'Volume': self.data.volume[0],
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
        
        # 突破策略
        if self.params.strategy_type == 'breakout':
            self._breakout_logic(current_price, bb_top, bb_bot, bb_pos)
        # 均值回归策略  
        elif self.params.strategy_type == 'mean_reversion':
            self._mean_reversion_logic(current_price, bb_top, bb_bot, bb_pos)
    
    def _breakout_logic(self, current_price, bb_top, bb_bot, bb_pos):
        """突破策略逻辑"""
        # 买入条件：价格突破上轨 + 成交量确认
        if (not self.position and 
            current_price > bb_top and 
            bb_pos > 1.0 and  # 确保真正突破
            self.check_volume_condition()):
            
            available_cash = self.broker.getcash()
            size = (available_cash * self.params.position_size) / current_price
            
            self.log(f'买入信号(突破上轨): 价格={current_price:.2f}, '
                    f'上轨={bb_top:.2f}, 布林位置={bb_pos:.3f}')
            self.order = self.buy(size=size)
        
        # 卖出条件：价格跌破下轨或止损/止盈
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 跌破下轨
            if current_price < bb_bot and bb_pos < 0.0:
                self.log(f'卖出信号(跌破下轨): 价格={current_price:.2f}, '
                        f'下轨={bb_bot:.2f}')
                self.order = self.sell(size=self.position.size)
            
            # 止损
            elif return_pct < -self.params.stop_loss:
                self.log(f'止损卖出: 亏损{return_pct*100:.2f}%')
                self.order = self.sell(size=self.position.size)
            
            # 止盈
            elif return_pct > self.params.take_profit:
                self.log(f'止盈卖出: 盈利{return_pct*100:.2f}%')
                self.order = self.sell(size=self.position.size)
    
    def _mean_reversion_logic(self, current_price, bb_top, bb_bot, bb_pos):
        """均值回归策略逻辑"""
        # 买入条件：价格触及下轨(超卖)
        if (not self.position and 
            current_price <= bb_bot and 
            bb_pos <= 0.1 and  # 价格在布林带底部10%范围内
            self.check_volume_condition()):
            
            available_cash = self.broker.getcash()
            size = (available_cash * self.params.position_size) / current_price
            
            self.log(f'买入信号(触及下轨): 价格={current_price:.2f}, '
                    f'下轨={bb_bot:.2f}, 布林位置={bb_pos:.3f}')
            self.order = self.buy(size=size)
        
        # 卖出条件：价格触及上轨(超买)或止损/止盈
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 触及上轨
            if current_price >= bb_top and bb_pos >= 0.9:
                self.log(f'卖出信号(触及上轨): 价格={current_price:.2f}, '
                        f'上轨={bb_top:.2f}')
                self.order = self.sell(size=self.position.size)
            
            # 止损
            elif return_pct < -self.params.stop_loss:
                self.log(f'止损卖出: 亏损{return_pct*100:.2f}%')
                self.order = self.sell(size=self.position.size)
            
            # 止盈
            elif return_pct > self.params.take_profit:
                self.log(f'止盈卖出: 盈利{return_pct*100:.2f}%')
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
            
            # 布林带统计
            avg_bb_width = signals_df['bb_width'].mean()
            
            self.log('='*50)
            self.log(f'策略统计 (布林带{self.params.bb_period}周期, {self.params.bb_dev}倍标准差):')
            self.log(f'策略类型: {self.params.strategy_type}')
            self.log(f'总交易次数: {len(trades_df)}')
            self.log(f'胜率: {win_rate:.2%}')
            self.log(f'平均收益率: {avg_return:.2f}%')
            self.log(f'平均布林带宽度: {avg_bb_width:.4f}')
            self.log(f'最终资金: {self.broker.getvalue():.2f}')


class AdaptiveBollingerStrategy(BollingerBandsStrategy):
    """
    自适应布林带策略
    
    特性:
    - 根据市场波动性调整标准差倍数
    - 使用ATR指标辅助判断
    - 动态调整仓位大小
    """
    
    params = (
        ('bb_period', 20),
        ('bb_dev_base', 2.0),     # 基础标准差倍数
        ('bb_dev_min', 1.5),      # 最小标准差倍数
        ('bb_dev_max', 2.5),      # 最大标准差倍数
        ('atr_period', 14),       # ATR周期
        ('volatility_threshold', 0.05),  # 波动性阈值
        ('strategy_type', 'breakout'),
        ('adaptive_position', True),      # 是否使用自适应仓位
        ('stop_loss', 0.08),
        ('take_profit', 0.15),
        ('position_size', 0.95),
        ('print_log', True),
    )
    
    def __init__(self):
        # 基础布林带(固定参数)
        self.bb_base = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev_base
        )
        
        # ATR指标用于衡量波动性
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        # 价格变化率用于判断波动性
        self.price_change = bt.indicators.ROC(self.data.close, period=5)
        
        # 动态标准差倍数
        self.adaptive_dev = self.params.bb_dev_base
        
        # 跟踪订单和价格
        self.order = None
        self.buy_price = None
        self.trades = []
        self.volatility_history = []
    
    def calculate_adaptive_deviation(self):
        """计算自适应标准差倍数"""
        if len(self.volatility_history) < 10:
            return self.params.bb_dev_base
        
        # 基于最近的波动性调整
        recent_volatility = sum(self.volatility_history[-10:]) / 10
        
        if recent_volatility > self.params.volatility_threshold:
            # 高波动时扩大布林带
            dev_factor = min(self.params.bb_dev_max, 
                           self.params.bb_dev_base * (1 + recent_volatility))
        else:
            # 低波动时收窄布林带
            dev_factor = max(self.params.bb_dev_min,
                           self.params.bb_dev_base * (1 - recent_volatility))
        
        return dev_factor
    
    def next(self):
        """自适应策略主逻辑"""
        current_price = self.data.close[0]
        atr_val = self.atr[0]
        price_change_val = abs(self.price_change[0]) / 100  # 转换为小数
        
        # 记录波动性
        current_volatility = atr_val / current_price
        self.volatility_history.append(current_volatility)
        
        # 计算自适应参数
        self.adaptive_dev = self.calculate_adaptive_deviation()
        
        # 重新计算布林带
        bb_std = self.data.close.get(size=self.params.bb_period).std()
        bb_mid = self.data.close.get(size=self.params.bb_period).mean()
        bb_top = bb_mid + (bb_std * self.adaptive_dev)
        bb_bot = bb_mid - (bb_std * self.adaptive_dev)
        
        # 如果有挂单，等待执行
        if self.order:
            return
        
        # 自适应仓位大小
        if self.params.adaptive_position:
            volatility_factor = max(0.3, 1 - current_volatility * 10)  # 波动越大仓位越小
            adaptive_position_size = self.params.position_size * volatility_factor
        else:
            adaptive_position_size = self.params.position_size
        
        # 买入条件（突破策略）
        if (not self.position and 
            current_price > bb_top and
            current_volatility < self.params.volatility_threshold * 1.5):  # 避免在极端波动时入场
            
            available_cash = self.broker.getcash()
            size = (available_cash * adaptive_position_size) / current_price
            
            self.log(f'买入信号(自适应突破): 价格={current_price:.2f}, '
                    f'动态上轨={bb_top:.2f}, 标准差倍数={self.adaptive_dev:.2f}, '
                    f'波动性={current_volatility:.4f}')
            self.order = self.buy(size=size)
        
        # 卖出条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 跌破下轨或止损/止盈
            if current_price < bb_bot:
                self.log(f'卖出信号(跌破动态下轨): 价格={current_price:.2f}, '
                        f'动态下轨={bb_bot:.2f}')
                self.order = self.sell(size=self.position.size)
            
            elif return_pct < -self.params.stop_loss:
                self.log(f'止损卖出: 亏损{return_pct*100:.2f}%')
                self.order = self.sell(size=self.position.size)
            
            elif return_pct > self.params.take_profit:
                self.log(f'止盈卖出: 盈利{return_pct*100:.2f}%')
                self.order = self.sell(size=self.position.size)


if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from btc_data import BTCDataFeed
    
    # 创建回测引擎
    cerebro = bt.Cerebro()
    
    # 选择策略
    # cerebro.addstrategy(BollingerBandsStrategy, strategy_type='breakout')
    # cerebro.addstrategy(BollingerBandsStrategy, strategy_type='mean_reversion')
    cerebro.addstrategy(AdaptiveBollingerStrategy)
    
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