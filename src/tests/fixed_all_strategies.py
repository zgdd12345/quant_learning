#!/usr/bin/env python3
"""
修复版策略集合
修复所有发现的错误并改进策略
"""

import backtrader as bt
import pandas as pd
import numpy as np


# 修复MACD相关问题
class FixedMACDStrategy(bt.Strategy):
    """修复版MACD策略"""
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
        ('stop_loss', 0.08),
        ('take_profit', 0.15),
        ('position_size', 0.9),
    )
    
    def __init__(self):
        # 使用MACDHisto指标替代MACD
        self.macd = bt.indicators.MACDHisto(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )
        self.order = None
        self.buy_price = None
        self.trades = []
        
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
            elif order.issell() and self.buy_price:
                profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                self.trades.append(profit_pct)
        self.order = None
    
    def next(self):
        if self.order or len(self.macd) < self.params.slow_period:
            return
            
        current_price = self.data.close[0]
        macd_line = self.macd.macd[0]
        signal_line = self.macd.signal[0]
        
        # 金叉买入
        if (not self.position and 
            macd_line > signal_line and 
            len(self.macd.macd) > 1 and
            self.macd.macd[-1] <= self.macd.signal[-1]):
            
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
            
        # 死叉或止损止盈卖出
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            if ((macd_line < signal_line and 
                 len(self.macd.macd) > 1 and
                 self.macd.macd[-1] >= self.macd.signal[-1]) or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                
                self.order = self.sell(size=self.position.size)


class FixedRSIStrategy(bt.Strategy):
    """修复版RSI策略"""
    params = (
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('stop_loss', 0.06),
        ('take_profit', 0.12),
        ('position_size', 0.9),
    )
    
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.order = None
        self.buy_price = None
        self.trades = []
        
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
            elif order.issell() and self.buy_price:
                profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                self.trades.append(profit_pct)
        self.order = None
    
    def next(self):
        if self.order or len(self.rsi) < self.params.rsi_period:
            return
            
        current_price = self.data.close[0]
        rsi_val = self.rsi[0]
        
        # RSI超卖买入
        if not self.position and rsi_val < self.params.rsi_oversold:
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
            
        # RSI超买或止损止盈卖出
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            if (rsi_val > self.params.rsi_overbought or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                
                self.order = self.sell(size=self.position.size)


class FixedBollingerStrategy(bt.Strategy):
    """修复版布林带策略"""
    params = (
        ('bb_period', 20),
        ('bb_dev', 2.0),
        ('strategy_type', 'mean_reversion'),  # 'breakout' or 'mean_reversion'
        ('stop_loss', 0.08),
        ('take_profit', 0.15),
        ('position_size', 0.9),
    )
    
    def __init__(self):
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )
        self.order = None
        self.buy_price = None
        self.trades = []
        
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
            elif order.issell() and self.buy_price:
                profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                self.trades.append(profit_pct)
        self.order = None
    
    def next(self):
        if self.order or len(self.bb) < self.params.bb_period:
            return
            
        current_price = self.data.close[0]
        bb_top = self.bb.top[0]
        bb_bot = self.bb.bot[0]
        bb_mid = self.bb.mid[0]
        
        if self.params.strategy_type == 'mean_reversion':
            # 均值回归：触及下轨买入
            if not self.position and current_price <= bb_bot * 1.005:
                size = (self.broker.getcash() * self.params.position_size) / current_price
                self.order = self.buy(size=size)
                
            # 触及上轨或止损止盈卖出
            elif self.position and self.buy_price:
                return_pct = (current_price - self.buy_price) / self.buy_price
                
                if (current_price >= bb_top * 0.995 or
                    return_pct < -self.params.stop_loss or
                    return_pct > self.params.take_profit):
                    
                    self.order = self.sell(size=self.position.size)
                    
        else:  # breakout
            # 突破：突破上轨买入
            if not self.position and current_price > bb_top:
                size = (self.broker.getcash() * self.params.position_size) / current_price
                self.order = self.buy(size=size)
                
            # 跌破下轨或止损止盈卖出
            elif self.position and self.buy_price:
                return_pct = (current_price - self.buy_price) / self.buy_price
                
                if (current_price < bb_bot or
                    return_pct < -self.params.stop_loss or
                    return_pct > self.params.take_profit):
                    
                    self.order = self.sell(size=self.position.size)


class ImprovedTurtleStrategy(bt.Strategy):
    """改进版海龟策略"""
    params = (
        ('entry_period', 20),
        ('exit_period', 10), 
        ('atr_period', 20),
        ('atr_multiplier', 2.0),
        ('position_size', 0.02),
        ('trend_filter', True),
        ('trend_period', 50),
    )
    
    def __init__(self):
        self.high_n = bt.indicators.Highest(self.data.high, period=self.params.entry_period)
        self.low_n = bt.indicators.Lowest(self.data.low, period=self.params.exit_period)
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        if self.params.trend_filter:
            self.trend_sma = bt.indicators.SMA(self.data.close, period=self.params.trend_period)
        
        self.order = None
        self.buy_price = None
        self.trades = []
        
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
            elif order.issell() and self.buy_price:
                profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                self.trades.append(profit_pct)
        self.order = None
    
    def next(self):
        if self.order or len(self.atr) < self.params.atr_period:
            return
            
        current_price = self.data.close[0]
        high_n = self.high_n[0]
        low_n = self.low_n[0]
        
        # 趋势过滤
        trend_ok = True
        if self.params.trend_filter and len(self.trend_sma) > 0:
            trend_ok = current_price > self.trend_sma[0]
        
        # 突破买入
        if not self.position and current_price >= high_n and trend_ok:
            # 基于ATR计算仓位
            atr_val = self.atr[0]
            account_value = self.broker.getvalue()
            risk_amount = account_value * self.params.position_size
            shares = risk_amount / atr_val
            
            if shares > 0:
                self.order = self.buy(size=shares)
        
        # 突破退出或ATR止损
        elif self.position and self.buy_price:
            atr_stop_price = self.buy_price - (self.params.atr_multiplier * self.atr[0])
            
            if current_price <= low_n or current_price <= atr_stop_price:
                self.order = self.sell(size=self.position.size)


class ImprovedMomentumStrategy(bt.Strategy):
    """改进版动量策略"""
    params = (
        ('momentum_period', 10),     # 缩短动量周期提高敏感性
        ('volume_period', 20),
        ('momentum_threshold', 0.03), # 降低阈值增加交易机会
        ('volume_threshold', 1.2),
        ('rsi_period', 14),
        ('rsi_filter', True),
        ('stop_loss', 0.08),
        ('take_profit', 0.18),
        ('position_size', 0.9),
    )
    
    def __init__(self):
        self.momentum = bt.indicators.ROC(self.data.close, period=self.params.momentum_period)
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=self.params.volume_period)
        
        if self.params.rsi_filter:
            self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        
        self.order = None
        self.buy_price = None
        self.trades = []
        
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
            elif order.issell() and self.buy_price:
                profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                self.trades.append(profit_pct)
        self.order = None
    
    def next(self):
        if self.order or len(self.momentum) < self.params.momentum_period:
            return
            
        current_price = self.data.close[0]
        momentum_val = self.momentum[0] / 100  # 转换为小数
        volume_ratio = self.data.volume[0] / self.volume_sma[0] if len(self.volume_sma) > 0 else 1
        
        # RSI过滤
        rsi_ok = True
        if self.params.rsi_filter and len(self.rsi) > 0:
            rsi_ok = self.rsi[0] < 75  # 避免在超买区域买入
        
        # 动量突破买入
        if (not self.position and 
            momentum_val > self.params.momentum_threshold and
            volume_ratio > self.params.volume_threshold and
            rsi_ok):
            
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 动量衰减或止损止盈卖出
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            if (momentum_val < self.params.momentum_threshold * 0.2 or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                
                self.order = self.sell(size=self.position.size)


class ImprovedGridStrategy(bt.Strategy):
    """改进版网格策略"""
    params = (
        ('base_price', None),        # 基准价格，None则使用开盘价
        ('grid_spacing', 200),       # 减小网格间距
        ('grid_levels', 8),
        ('base_order_size', 0.02),
        ('max_position', 0.4),
        ('take_profit_pct', 0.01),   # 减小单次止盈
        ('use_trend_filter', True),
        ('trend_period', 30),
        ('max_loss_pct', 0.15),      # 整体止损
    )
    
    def __init__(self):
        if self.params.use_trend_filter:
            self.trend_sma = bt.indicators.SMA(self.data.close, period=self.params.trend_period)
        
        self.grid_orders = {}  # 存储网格订单
        self.total_position = 0.0
        self.base_price = None
        self.initial_cash = None
        self.trades = []
        
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.total_position += order.executed.size
            elif order.issell():
                self.total_position -= order.executed.size
                profit = order.executed.value - (order.executed.size * self.base_price)
                self.trades.append(profit)
    
    def next(self):
        if self.initial_cash is None:
            self.initial_cash = self.broker.getvalue()
            self.base_price = self.data.open[0]
        
        current_price = self.data.close[0]
        
        # 整体止损检查
        current_value = self.broker.getvalue()
        total_loss_pct = (current_value - self.initial_cash) / self.initial_cash
        
        if total_loss_pct < -self.params.max_loss_pct:
            if self.total_position > 0:
                self.sell(size=self.total_position)
            return
        
        # 趋势过滤
        trend_ok = True
        if self.params.use_trend_filter and len(self.trend_sma) > 0:
            # 在下跌趋势中减少买入，在上涨趋势中正常操作
            if current_price < self.trend_sma[0] * 0.95:
                trend_ok = False
        
        # 计算网格水平
        for i in range(1, self.params.grid_levels + 1):
            buy_level = self.base_price - (i * self.params.grid_spacing)
            sell_level = buy_level + self.params.grid_spacing * (1 + self.params.take_profit_pct)
            
            grid_key = f"grid_{i}"
            
            # 网格买入
            if (trend_ok and
                current_price <= buy_level * 1.002 and 
                grid_key not in self.grid_orders and
                self.total_position < self.params.max_position):
                
                order = self.buy(size=self.params.base_order_size)
                if order:
                    self.grid_orders[grid_key] = {
                        'buy_level': buy_level,
                        'sell_level': sell_level,
                        'size': self.params.base_order_size
                    }
            
            # 网格卖出
            elif (grid_key in self.grid_orders and 
                  current_price >= self.grid_orders[grid_key]['sell_level']):
                
                order = self.sell(size=self.grid_orders[grid_key]['size'])
                if order:
                    del self.grid_orders[grid_key]