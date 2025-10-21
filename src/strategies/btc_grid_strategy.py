import backtrader as bt
import pandas as pd


class BTCGridTradingStrategy(bt.Strategy):
    """
    比特币网格交易策略
    
    策略逻辑:
    - 在价格区间内设置多个买入和卖出网格
    - 价格下跌时分批买入，价格上涨时分批卖出
    - 适合震荡行情，通过频繁交易获得收益
    """
    
    params = (
        ('grid_spacing', 500),      # 网格间距(USD)
        ('grid_levels', 10),        # 网格层数
        ('base_order_size', 0.01),  # 基础订单大小(BTC)
        ('martingale_factor', 1.2), # 马丁格尔倍数
        ('max_position', 0.5),      # 最大仓位(BTC)
        ('take_profit_pct', 0.02),  # 单次网格止盈比例
        ('stop_loss_pct', 0.15),    # 整体止损比例
        ('dynamic_grid', True),     # 是否使用动态网格
        ('sma_period', 50),         # 动态网格基准SMA周期
        ('print_log', True),        # 是否打印日志
    )
    
    def __init__(self):
        # 基准价格指标(用于动态网格)
        if self.params.dynamic_grid:
            self.sma = bt.indicators.SMA(self.data.close, period=self.params.sma_period)
            self.atr = bt.indicators.ATR(self.data, period=14)
        
        # 网格状态跟踪
        self.grid_levels_dict = {}  # {price_level: {'bought': bool, 'size': float, 'order_id': str}}
        self.active_orders = {}     # {order_id: order_object}
        self.total_position = 0.0   # 总持仓
        self.avg_buy_price = 0.0    # 平均买入价
        self.initial_cash = None    # 初始资金
        
        # 性能跟踪
        self.trades = []
        self.grid_transactions = []
        
    def log(self, txt, dt=None):
        """日志记录"""
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')
    
    def calculate_grid_levels(self, current_price):
        """计算网格价格水平"""
        if self.params.dynamic_grid and len(self.sma) > 0:
            # 使用SMA作为中心价格
            center_price = self.sma[0]
            # 根据ATR调整网格间距
            dynamic_spacing = max(self.params.grid_spacing, self.atr[0] * 2)
        else:
            center_price = current_price
            dynamic_spacing = self.params.grid_spacing
        
        levels = []
        for i in range(-self.params.grid_levels // 2, self.params.grid_levels // 2 + 1):
            level_price = center_price + (i * dynamic_spacing)
            if level_price > 0:  # 确保价格为正
                levels.append(level_price)
        
        return sorted(levels), dynamic_spacing
    
    def calculate_order_size(self, level_index):
        """计算订单大小(马丁格尔策略)"""
        if level_index <= 0:
            return self.params.base_order_size
        else:
            return self.params.base_order_size * (self.params.martingale_factor ** level_index)
    
    def update_avg_buy_price(self, new_price, new_size):
        """更新平均买入价"""
        if self.total_position == 0:
            self.avg_buy_price = new_price
        else:
            total_value = (self.avg_buy_price * self.total_position) + (new_price * new_size)
            self.total_position += new_size
            self.avg_buy_price = total_value / self.total_position
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status == order.Completed:
            if order.isbuy():
                self.log(f'网格买入: 价格 {order.executed.price:.2f}, '
                        f'数量 {order.executed.size:.6f}')
                
                # 更新平均买入价
                self.update_avg_buy_price(order.executed.price, order.executed.size)
                
                # 记录网格交易
                self.grid_transactions.append({
                    'date': self.datas[0].datetime.date(0),
                    'type': 'buy',
                    'price': order.executed.price,
                    'size': order.executed.size,
                    'total_position': self.total_position
                })
                
            elif order.issell():
                self.log(f'网格卖出: 价格 {order.executed.price:.2f}, '
                        f'数量 {order.executed.size:.6f}')
                
                # 更新总仓位
                self.total_position -= order.executed.size
                
                # 记录网格交易
                self.grid_transactions.append({
                    'date': self.datas[0].datetime.date(0),
                    'type': 'sell',
                    'price': order.executed.price,
                    'size': order.executed.size,
                    'total_position': self.total_position
                })
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单被取消/拒绝: {order.getstatusname()}')
        
        # 清理订单记录
        if hasattr(order, 'ref') and order.ref in self.active_orders:
            del self.active_orders[order.ref]
    
    def notify_trade(self, trade):
        """交易完成通知"""
        if not trade.isclosed:
            return
        
        profit_loss = trade.pnl
        profit_pct = (profit_loss / trade.price) * 100 if trade.price else 0
        
        self.log(f'网格交易盈亏: {profit_loss:.2f} ({profit_pct:.2f}%)')
        
        self.trades.append({
            'date': self.datas[0].datetime.date(0),
            'pnl': profit_loss,
            'pnl_pct': profit_pct,
            'price': trade.price
        })
    
    def next(self):
        """策略主逻辑"""
        if self.initial_cash is None:
            self.initial_cash = self.broker.getvalue()
        
        current_price = self.data.close[0]
        current_value = self.broker.getvalue()
        
        # 计算当前网格水平
        grid_levels, spacing = self.calculate_grid_levels(current_price)
        
        # 整体止损检查
        if self.total_position > 0:
            total_loss_pct = (current_value - self.initial_cash) / self.initial_cash
            if total_loss_pct < -self.params.stop_loss_pct:
                self.log(f'触发整体止损: 亏损 {total_loss_pct*100:.2f}%')
                if self.total_position > 0:
                    self.sell(size=self.total_position)
                return
        
        # 网格交易逻辑
        self.execute_grid_orders(current_price, grid_levels)
    
    def execute_grid_orders(self, current_price, grid_levels):
        """执行网格订单"""
        # 查找最接近当前价格的网格水平
        closest_levels = []
        for level in grid_levels:
            if abs(level - current_price) <= self.params.grid_spacing * 2:
                closest_levels.append(level)
        
        for i, level in enumerate(closest_levels):
            level_key = f"level_{level:.0f}"
            
            # 买入条件：价格接近或低于网格水平，且未持有该水平
            if (current_price <= level * 1.005 and  # 允许0.5%的价格偏差
                level_key not in self.grid_levels_dict and
                self.total_position < self.params.max_position):
                
                # 计算订单大小
                order_size = self.calculate_order_size(
                    max(0, len([l for l in grid_levels if l < level]) - self.params.grid_levels // 2)
                )
                
                # 检查资金是否足够
                required_cash = level * order_size
                if self.broker.getcash() >= required_cash:
                    order = self.buy(size=order_size)
                    if order:
                        self.active_orders[order.ref] = order
                        self.grid_levels_dict[level_key] = {
                            'price': level,
                            'size': order_size,
                            'order_ref': order.ref
                        }
                        
                        self.log(f'下达网格买单: 价格 {level:.2f}, 数量 {order_size:.6f}')
            
            # 卖出条件：价格上涨到网格获利点
            elif (level_key in self.grid_levels_dict and
                  current_price >= level * (1 + self.params.take_profit_pct)):
                
                grid_info = self.grid_levels_dict[level_key]
                sell_size = grid_info['size']
                
                # 确保有足够的持仓可卖
                if self.total_position >= sell_size:
                    order = self.sell(size=sell_size)
                    if order:
                        self.active_orders[order.ref] = order
                        self.log(f'下达网格卖单: 价格 {current_price:.2f}, '
                                f'数量 {sell_size:.6f}, 获利 {self.params.take_profit_pct*100:.1f}%')
                        
                        # 清理网格记录
                        del self.grid_levels_dict[level_key]
    
    def stop(self):
        """策略结束统计"""
        if self.params.print_log:
            final_value = self.broker.getvalue()
            total_return = (final_value - self.initial_cash) / self.initial_cash if self.initial_cash else 0
            
            # 统计网格交易
            if self.grid_transactions:
                transactions_df = pd.DataFrame(self.grid_transactions)
                buy_count = len(transactions_df[transactions_df['type'] == 'buy'])
                sell_count = len(transactions_df[transactions_df['type'] == 'sell'])
                avg_buy_price = transactions_df[transactions_df['type'] == 'buy']['price'].mean()
                avg_sell_price = transactions_df[transactions_df['type'] == 'sell']['price'].mean()
            else:
                buy_count = sell_count = 0
                avg_buy_price = avg_sell_price = 0
            
            self.log('='*60)
            self.log(f'BTC网格交易策略统计:')
            self.log(f'网格间距: {self.params.grid_spacing} USD')
            self.log(f'网格层数: {self.params.grid_levels}')
            self.log(f'初始资金: {self.initial_cash:.2f}')
            self.log(f'最终资金: {final_value:.2f}')
            self.log(f'总收益率: {total_return*100:.2f}%')
            self.log(f'网格买入次数: {buy_count}')
            self.log(f'网格卖出次数: {sell_count}')
            self.log(f'平均买入价: {avg_buy_price:.2f}')
            self.log(f'平均卖出价: {avg_sell_price:.2f}')
            self.log(f'最终持仓: {self.total_position:.6f} BTC')


class DynamicBTCGridStrategy(BTCGridTradingStrategy):
    """
    动态比特币网格策略
    
    增强特性:
    - 根据市场波动性动态调整网格间距
    - 基于RSI指标调整买卖信号强度
    - 智能资金管理
    """
    
    params = (
        ('grid_spacing', 300),
        ('grid_levels', 8),
        ('base_order_size', 0.01),
        ('volatility_factor', 2.0),    # 波动性调整因子
        ('rsi_period', 14),
        ('rsi_oversold', 35),
        ('rsi_overbought', 65),
        ('max_position', 0.3),
        ('take_profit_pct', 0.015),
        ('print_log', True),
    )
    
    def __init__(self):
        super().__init__()
        
        # 添加技术指标
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.volatility = bt.indicators.StdDev(self.data.close, period=20)
        
        # 波动性历史记录
        self.volatility_history = []
    
    def calculate_dynamic_spacing(self, current_price):
        """计算动态网格间距"""
        if len(self.volatility_history) < 10:
            return self.params.grid_spacing
        
        # 基于最近波动性调整间距
        recent_volatility = sum(self.volatility_history[-10:]) / 10
        volatility_ratio = recent_volatility / current_price
        
        # 波动性越大，间距越大
        dynamic_spacing = self.params.grid_spacing * (1 + volatility_ratio * self.params.volatility_factor)
        
        return max(100, min(1000, dynamic_spacing))  # 限制在合理范围内
    
    def should_buy(self, current_price, level):
        """动态买入条件判断"""
        base_condition = current_price <= level * 1.005
        
        # RSI超卖时增强买入信号
        rsi_condition = self.rsi[0] < self.params.rsi_oversold
        
        return base_condition and (rsi_condition or current_price < level * 0.995)
    
    def should_sell(self, current_price, level):
        """动态卖出条件判断"""
        base_condition = current_price >= level * (1 + self.params.take_profit_pct)
        
        # RSI超买时增强卖出信号
        rsi_condition = self.rsi[0] > self.params.rsi_overbought
        
        return base_condition or (rsi_condition and current_price > level * 1.01)
    
    def next(self):
        """动态策略主逻辑"""
        current_price = self.data.close[0]
        current_volatility = self.volatility[0] if len(self.volatility) > 0 else 0
        
        # 记录波动性
        self.volatility_history.append(current_volatility)
        if len(self.volatility_history) > 50:
            self.volatility_history.pop(0)
        
        # 计算动态参数
        dynamic_spacing = self.calculate_dynamic_spacing(current_price)
        
        # 更新网格间距
        original_spacing = self.params.grid_spacing
        self.params = self.params._replace(grid_spacing=int(dynamic_spacing))
        
        # 执行基础网格逻辑
        super().next()
        
        # 恢复原始间距设置
        self.params = self.params._replace(grid_spacing=original_spacing)
    
    def execute_grid_orders(self, current_price, grid_levels):
        """重写网格订单执行逻辑"""
        closest_levels = []
        dynamic_spacing = self.calculate_dynamic_spacing(current_price)
        
        for level in grid_levels:
            if abs(level - current_price) <= dynamic_spacing * 1.5:
                closest_levels.append(level)
        
        for level in closest_levels:
            level_key = f"level_{level:.0f}"
            
            # 动态买入判断
            if (self.should_buy(current_price, level) and
                level_key not in self.grid_levels_dict and
                self.total_position < self.params.max_position):
                
                order_size = self.calculate_order_size(0)  # 简化订单大小计算
                required_cash = level * order_size
                
                if self.broker.getcash() >= required_cash:
                    order = self.buy(size=order_size)
                    if order:
                        self.active_orders[order.ref] = order
                        self.grid_levels_dict[level_key] = {
                            'price': level,
                            'size': order_size,
                            'order_ref': order.ref
                        }
                        
                        self.log(f'动态网格买单: 价格 {level:.2f}, RSI {self.rsi[0]:.1f}')
            
            # 动态卖出判断
            elif (level_key in self.grid_levels_dict and
                  self.should_sell(current_price, level)):
                
                grid_info = self.grid_levels_dict[level_key]
                sell_size = grid_info['size']
                
                if self.total_position >= sell_size:
                    order = self.sell(size=sell_size)
                    if order:
                        self.active_orders[order.ref] = order
                        self.log(f'动态网格卖单: 价格 {current_price:.2f}, RSI {self.rsi[0]:.1f}')
                        del self.grid_levels_dict[level_key]


if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from btc_data import BTCDataFeed
    
    # 创建回测引擎
    cerebro = bt.Cerebro()
    
    # 选择策略
    # cerebro.addstrategy(BTCGridTradingStrategy)
    cerebro.addstrategy(DynamicBTCGridStrategy)
    
    # 获取比特币数据
    btc_feed = BTCDataFeed()
    bt_data, _ = btc_feed.get_backtrader_data("2023-01-01", "2024-01-01")
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