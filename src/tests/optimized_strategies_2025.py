#!/usr/bin/env python3
"""
基于2025年数据分析的优化版策略
"""

import backtrader as bt
import pandas as pd
import numpy as np


class OptimizedRSIStrategy(bt.Strategy):
    """
    优化版RSI策略 v2.0
    
    优化点:
    1. RSI阈值从30/70调整为25/75
    2. 动态止损机制
    3. 成交量确认
    4. 优化止盈止损比例
    """
    
    params = (
        ('rsi_period', 14),
        ('rsi_oversold', 25),      # 更激进的阈值
        ('rsi_overbought', 75),    # 更激进的阈值  
        ('stop_loss', 0.06),       # 略微放宽止损
        ('take_profit', 0.15),     # 提高止盈目标
        ('volume_confirm', True),   # 成交量确认
        ('position_size', 0.9),    # 略微保守的仓位
        ('print_log', False),
    )
    
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=20)
        self.order = None
        self.buy_price = None
        self.trades = []
        
    def log(self, txt, dt=None):
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'买入: {order.executed.price:.2f}')
            elif order.issell():
                profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                self.trades.append(profit_pct)
                self.log(f'卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def next(self):
        if self.order or len(self.rsi) < self.params.rsi_period:
            return
            
        current_price = self.data.close[0]
        rsi_val = self.rsi[0]
        
        # 成交量确认
        volume_confirm = True
        if self.params.volume_confirm and len(self.volume_sma) > 0:
            volume_confirm = self.data.volume[0] > self.volume_sma[0] * 1.1
        
        # 买入条件: RSI超卖 + 成交量确认
        if not self.position and rsi_val < self.params.rsi_oversold and volume_confirm:
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
            
        # 卖出条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # RSI超买 or 止损 or 止盈
            if (rsi_val > self.params.rsi_overbought or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'优化RSI策略 - 交易次数: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class OptimizedMACDStrategy(bt.Strategy):
    """
    优化版多因子MACD策略 v2.0
    
    优化点:
    1. 更快的MACD参数 (8-17-9)
    2. EMA趋势过滤
    3. RSI信号确认
    4. ATR动态止损
    """
    
    params = (
        ('fast_period', 8),        # 更快的参数
        ('slow_period', 17),       # 更快的参数
        ('signal_period', 9),
        ('ema_trend', 50),         # EMA趋势过滤
        ('rsi_period', 14),        # RSI确认
        ('atr_period', 14),        # ATR动态止损
        ('stop_loss_atr', 2.0),    # ATR止损倍数
        ('take_profit', 0.20),     # 提高止盈
        ('position_size', 0.9),
        ('print_log', False),
    )
    
    def __init__(self):
        self.macd = bt.indicators.MACDHisto(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )
        self.ema_trend = bt.indicators.EMA(self.data.close, period=self.params.ema_trend)
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        self.order = None
        self.buy_price = None
        self.trades = []
        
    def log(self, txt, dt=None):
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'买入: {order.executed.price:.2f}')
            elif order.issell():
                profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                self.trades.append(profit_pct)
                self.log(f'卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def next(self):
        if self.order:
            return
            
        # 确保有足够的数据
        min_len = max(self.params.slow_period, self.params.ema_trend)
        if len(self.data) < min_len:
            return
            
        current_price = self.data.close[0]
        macd_line = self.macd.macd[0]
        signal_line = self.macd.signal[0]
        ema_val = self.ema_trend[0]
        rsi_val = self.rsi[0]
        
        # 买入条件: MACD金叉 + 价格在EMA上方 + RSI不超买
        macd_crossup = macd_line > signal_line and self.macd.macd[-1] <= self.macd.signal[-1]
        trend_confirm = current_price > ema_val
        rsi_confirm = rsi_val < 70
        
        if not self.position and macd_crossup and trend_confirm and rsi_confirm:
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
            
        # 卖出条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # MACD死叉
            macd_crossdown = macd_line < signal_line and self.macd.macd[-1] >= self.macd.signal[-1]
            
            # ATR动态止损
            atr_stop_loss = 0
            if len(self.atr) > 0:
                atr_stop_loss = (self.atr[0] * self.params.stop_loss_atr) / self.buy_price
            
            if (macd_crossdown or
                return_pct < -max(0.08, atr_stop_loss) or  # 动态止损
                return_pct > self.params.take_profit):
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'优化MACD策略 - 交易次数: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class EnhancedBollingerStrategy(bt.Strategy):
    """
    增强版布林带策略 v2.0
    
    优化点:
    1. 动态标准差调整
    2. RSI过滤信号
    3. 成交量确认
    4. 优化进出场逻辑
    """
    
    params = (
        ('bb_period', 20),
        ('bb_dev_base', 2.0),
        ('bb_dev_min', 1.6),       # 动态标准差范围
        ('bb_dev_max', 2.4),
        ('rsi_period', 14),
        ('volatility_period', 10),  # 波动性计算周期
        ('stop_loss', 0.08),
        ('take_profit', 0.18),
        ('position_size', 0.9),
        ('print_log', False),
    )
    
    def __init__(self):
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev_base
        )
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=self.params.bb_period)
        self.volatility = bt.indicators.StdDev(self.data.close, period=self.params.volatility_period)
        
        self.order = None
        self.buy_price = None
        self.trades = []
        self.current_bb_dev = self.params.bb_dev_base
        
    def log(self, txt, dt=None):
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.log(f'买入: {order.executed.price:.2f}')
            elif order.issell():
                profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                self.trades.append(profit_pct)
                self.log(f'卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def calculate_dynamic_bb_dev(self):
        """计算动态标准差倍数"""
        if len(self.volatility) < self.params.volatility_period:
            return self.params.bb_dev_base
            
        # 基于波动率调整
        current_vol = self.volatility[0]
        avg_vol = sum(self.volatility.get(size=self.params.volatility_period)) / self.params.volatility_period
        
        vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0
        
        if vol_ratio > 1.2:  # 高波动时扩大布林带
            bb_dev = min(self.params.bb_dev_max, self.params.bb_dev_base * vol_ratio)
        elif vol_ratio < 0.8:  # 低波动时缩小布林带
            bb_dev = max(self.params.bb_dev_min, self.params.bb_dev_base * vol_ratio)
        else:
            bb_dev = self.params.bb_dev_base
            
        return bb_dev
    
    def next(self):
        if self.order or len(self.bb) < self.params.bb_period:
            return
            
        current_price = self.data.close[0]
        rsi_val = self.rsi[0]
        
        # 动态调整布林带
        self.current_bb_dev = self.calculate_dynamic_bb_dev()
        
        # 重新计算布林带
        bb_mid = self.bb.mid[0]
        bb_std = self.data.close.get(size=self.params.bb_period).std()
        bb_top = bb_mid + (bb_std * self.current_bb_dev)
        bb_bot = bb_mid - (bb_std * self.current_bb_dev)
        
        # 成交量确认
        volume_confirm = self.data.volume[0] > self.volume_sma[0] * 1.0
        
        # 买入条件: 触及下轨 + RSI不超卖 + 成交量确认
        if (not self.position and 
            current_price <= bb_bot * 1.002 and  # 允许小幅偏差
            rsi_val > 25 and  # 避免极度超卖
            volume_confirm):
            
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
            
        # 卖出条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 触及上轨 + RSI超买 or 止损止盈
            touch_upper = current_price >= bb_top * 0.998
            rsi_overbought = rsi_val > 75
            
            if ((touch_upper and rsi_overbought) or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'增强布林带策略 - 交易次数: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class EnhancedGridStrategy(bt.Strategy):
    """
    增强版网格策略 v2.0
    
    优化点:
    1. 趋势过滤避免单边行情
    2. 动态网格间距调整
    3. 智能资金分配
    4. 风险控制增强
    """
    
    params = (
        ('grid_spacing_base', 250),  # 基础网格间距
        ('grid_levels', 10),         # 增加网格层数
        ('base_order_size', 0.015),  # 稍小的基础订单
        ('max_position', 0.35),      # 控制最大仓位
        ('trend_ema', 50),           # 趋势过滤EMA
        ('atr_period', 14),          # ATR波动性指标
        ('take_profit_pct', 0.012),  # 略小的止盈
        ('use_trend_filter', True),  # 启用趋势过滤
        ('print_log', False),
    )
    
    def __init__(self):
        self.ema_trend = bt.indicators.EMA(self.data.close, period=self.params.trend_ema)
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        self.grid_levels_dict = {}
        self.active_orders = {}
        self.total_position = 0.0
        self.trades = []
        self.initial_cash = None
        
    def log(self, txt, dt=None):
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        if order.status == order.Completed:
            if order.isbuy():
                self.total_position += order.executed.size
                self.log(f'网格买入: {order.executed.price:.2f}, 仓位: {self.total_position:.4f}')
            elif order.issell():
                self.total_position -= order.executed.size
                profit = (order.executed.price - order.executed.value/order.executed.size) * order.executed.size
                self.trades.append(profit)
                self.log(f'网格卖出: {order.executed.price:.2f}, 盈利: {profit:.2f}')
        
        if hasattr(order, 'ref') and order.ref in self.active_orders:
            del self.active_orders[order.ref]
    
    def calculate_dynamic_spacing(self, current_price):
        """基于ATR计算动态网格间距"""
        if len(self.atr) < self.params.atr_period:
            return self.params.grid_spacing_base
            
        atr_value = self.atr[0]
        # 网格间距 = 基础间距 + ATR调整
        dynamic_spacing = self.params.grid_spacing_base + (atr_value * 0.8)
        
        return max(150, min(500, dynamic_spacing))  # 限制范围
    
    def trend_direction(self):
        """判断趋势方向"""
        if not self.params.use_trend_filter or len(self.ema_trend) < self.params.trend_ema:
            return 0  # 无趋势过滤
            
        current_price = self.data.close[0]
        ema_val = self.ema_trend[0]
        
        if current_price > ema_val * 1.02:
            return 1  # 上涨趋势
        elif current_price < ema_val * 0.98:
            return -1  # 下跌趋势
        else:
            return 0  # 震荡
    
    def next(self):
        if self.initial_cash is None:
            self.initial_cash = self.broker.getvalue()
            
        current_price = self.data.close[0]
        trend = self.trend_direction()
        dynamic_spacing = self.calculate_dynamic_spacing(current_price)
        
        # 趋势过滤: 在强趋势中减少逆势交易
        if abs(trend) > 0:
            # 在上升趋势中，更积极买入，在下降趋势中更保守
            buy_threshold = 0.998 if trend > 0 else 1.005
        else:
            buy_threshold = 1.002
        
        # 计算网格水平
        center_price = self.ema_trend[0] if len(self.ema_trend) > 0 else current_price
        grid_levels = []
        for i in range(-self.params.grid_levels//2, self.params.grid_levels//2 + 1):
            level = center_price + (i * dynamic_spacing)
            if level > 0:
                grid_levels.append(level)
        
        # 执行网格交易
        for level in grid_levels:
            level_key = f"grid_{level:.0f}"
            
            # 买入条件
            if (current_price <= level * buy_threshold and
                level_key not in self.grid_levels_dict and
                self.total_position < self.params.max_position and
                self.broker.getcash() > level * self.params.base_order_size):
                
                order = self.buy(size=self.params.base_order_size)
                if order:
                    self.active_orders[order.ref] = order
                    self.grid_levels_dict[level_key] = {
                        'level': level,
                        'size': self.params.base_order_size
                    }
            
            # 卖出条件
            elif (level_key in self.grid_levels_dict and
                  current_price >= level * (1 + self.params.take_profit_pct) and
                  self.total_position >= self.params.base_order_size):
                
                order = self.sell(size=self.params.base_order_size)
                if order:
                    self.active_orders[order.ref] = order
                    del self.grid_levels_dict[level_key]
    
    def stop(self):
        if self.params.print_log and self.trades:
            total_profit = sum(self.trades)
            win_count = len([t for t in self.trades if t > 0])
            self.log(f'增强网格策略 - 网格交易次数: {len(self.trades)}, 盈利次数: {win_count}, 总盈利: {total_profit:.2f}')


# 测试优化策略的函数
def test_optimized_strategies():
    """测试所有优化版策略"""
    from btc_data import BTCDataFeed
    
    strategies = [
        ('优化RSI策略 v2.0', OptimizedRSIStrategy),
        ('优化MACD策略 v2.0', OptimizedMACDStrategy),
        ('增强布林带策略 v2.0', EnhancedBollingerStrategy),
        ('增强网格策略 v2.0', EnhancedGridStrategy),
    ]
    
    results = []
    
    for name, strategy_class in strategies:
        try:
            cerebro = bt.Cerebro()
            cerebro.addstrategy(strategy_class, print_log=False)
            
            # 获取2025年数据
            btc_feed = BTCDataFeed()
            bt_data, raw_data = btc_feed.get_backtrader_data("2025-01-01", "2025-08-23")
            
            if bt_data is None:
                continue
                
            cerebro.adddata(bt_data)
            cerebro.broker.setcash(10000.0)
            cerebro.broker.setcommission(commission=0.001)
            
            start_value = cerebro.broker.getvalue()
            cerebro.run()
            final_value = cerebro.broker.getvalue()
            
            total_return = (final_value - start_value) / start_value
            results.append({
                'name': name,
                'return': total_return * 100,
                'final_value': final_value
            })
            
            status = "🏆" if total_return > 0.30 else "🟢" if total_return > 0.2258 else "🟡" if total_return > 0 else "🔴"
            print(f"{status} {name}: {total_return*100:.2f}% (${final_value:.2f})")
            
        except Exception as e:
            print(f"❌ {name} 测试失败: {e}")
    
    return results


if __name__ == "__main__":
    print("🚀 测试优化版策略 (2025年数据)")
    print("="*50)
    
    results = test_optimized_strategies()
    
    if results:
        print(f"\n📊 优化效果对比:")
        print(f"基准 (BTC买入持有): +22.58%")
        print(f"原版网格策略: +31.52%")
        print("-" * 40)
        
        best_result = max(results, key=lambda x: x['return'])
        print(f"🏆 最佳优化策略: {best_result['name']}")
        print(f"🎯 最佳收益率: {best_result['return']:.2f}%")
    else:
        print("❌ 没有成功的测试结果")