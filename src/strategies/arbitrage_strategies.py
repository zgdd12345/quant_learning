#!/usr/bin/env python3
"""
套利和配对交易策略集合
包含3个基于套利思想的交易策略
"""

import backtrader as bt
import pandas as pd
import numpy as np


class StatisticalArbitrageStrategy(bt.Strategy):
    """
    统计套利策略
    
    策略逻辑:
    - 基于价格与其移动平均线的统计关系
    - 计算价格偏离度的Z-Score
    - 在统计显著偏离时进行反向操作
    """
    
    params = (
        ('lookback_period', 60),     # 统计周期
        ('entry_threshold', 2.0),    # 入场阈值
        ('exit_threshold', 0.5),     # 出场阈值
        ('max_holding_days', 10),    # 最大持有天数
        ('position_size', 0.8),
        ('print_log', False),
    )
    
    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.lookback_period)
        self.std = bt.indicators.StdDev(self.data.close, period=self.params.lookback_period)
        
        self.order = None
        self.buy_price = None
        self.entry_date = None
        self.trades = []
    
    def log(self, txt, dt=None):
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.entry_date = self.datas[0].datetime.date(0)
                self.log(f'统计套利买入: {order.executed.price:.2f}')
            elif order.issell():
                if self.buy_price:
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    self.trades.append(profit_pct)
                    self.log(f'统计套利卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
                self.entry_date = None
        self.order = None
    
    def calculate_zscore(self):
        """计算价格偏离的Z-Score"""
        if len(self.sma) == 0 or len(self.std) == 0:
            return 0
        
        current_price = self.data.close[0]
        mean_price = self.sma[0]
        std_price = self.std[0]
        
        if std_price == 0:
            return 0
        
        return (current_price - mean_price) / std_price
    
    def days_since_entry(self):
        """计算持有天数"""
        if self.entry_date is None:
            return 0
        
        current_date = self.datas[0].datetime.date(0)
        return (current_date - self.entry_date).days
    
    def next(self):
        if self.order or len(self.sma) < self.params.lookback_period:
            return
            
        current_price = self.data.close[0]
        zscore = self.calculate_zscore()
        
        # 价格显著低于统计均值时买入
        if not self.position and zscore < -self.params.entry_threshold:
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 出场条件
        elif self.position:
            days_held = self.days_since_entry()
            
            # Z-Score回归或最大持有期限
            if (zscore > -self.params.exit_threshold or 
                days_held >= self.params.max_holding_days):
                
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'统计套利策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class PairsTradingStrategy(bt.Strategy):
    """
    配对交易策略
    
    策略逻辑:
    - 基于价格与其自身历史价格的协整关系
    - 计算价格差异的统计特征
    - 在差异过大时进行均值回归交易
    """
    
    params = (
        ('cointegration_period', 30), # 协整计算周期
        ('entry_threshold', 1.5),     # 入场阈值
        ('exit_threshold', 0.3),      # 出场阈值
        ('stop_loss', 0.10),
        ('position_size', 0.85),
        ('print_log', False),
    )
    
    def __init__(self):
        # 使用高价和低价的差异作为配对
        self.spread = self.data.high - self.data.low
        self.spread_sma = bt.indicators.SMA(self.spread, period=self.params.cointegration_period)
        self.spread_std = bt.indicators.StdDev(self.spread, period=self.params.cointegration_period)
        
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
                self.log(f'配对交易买入: {order.executed.price:.2f}')
            elif order.issell():
                if self.buy_price:
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    self.trades.append(profit_pct)
                    self.log(f'配对交易卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def calculate_spread_zscore(self):
        """计算价差的Z-Score"""
        if len(self.spread_sma) == 0 or len(self.spread_std) == 0:
            return 0
        
        current_spread = self.spread[0]
        mean_spread = self.spread_sma[0]
        std_spread = self.spread_std[0]
        
        if std_spread == 0:
            return 0
        
        return (current_spread - mean_spread) / std_spread
    
    def next(self):
        if self.order or len(self.spread_sma) < self.params.cointegration_period:
            return
            
        current_price = self.data.close[0]
        spread_zscore = self.calculate_spread_zscore()
        
        # 价差异常小时买入（预期价差会扩大）
        if not self.position and spread_zscore < -self.params.entry_threshold:
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 出场条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 价差回归正常或止损
            if (spread_zscore > -self.params.exit_threshold or 
                return_pct < -self.params.stop_loss):
                
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'配对交易策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class CalendarSpreadStrategy(bt.Strategy):
    """
    日历价差策略
    
    策略逻辑:
    - 基于不同时间窗口价格的关系
    - 短期和长期均线的差异作为交易信号
    - 适合波动率交易
    """
    
    params = (
        ('short_period', 5),       # 短期均线
        ('long_period', 30),       # 长期均线
        ('spread_threshold', 0.03), # 价差阈值
        ('volatility_period', 20),  # 波动率计算周期
        ('vol_threshold', 0.02),    # 波动率阈值
        ('stop_loss', 0.08),
        ('take_profit', 0.12),
        ('position_size', 0.9),
        ('print_log', False),
    )
    
    def __init__(self):
        self.short_sma = bt.indicators.SMA(self.data.close, period=self.params.short_period)
        self.long_sma = bt.indicators.SMA(self.data.close, period=self.params.long_period)
        
        # 计算价差
        self.spread = (self.short_sma - self.long_sma) / self.long_sma
        
        # 波动率指标
        self.volatility = bt.indicators.StdDev(self.data.close, period=self.params.volatility_period)
        
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
                self.log(f'日历价差买入: {order.executed.price:.2f}')
            elif order.issell():
                if self.buy_price:
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    self.trades.append(profit_pct)
                    self.log(f'日历价差卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def next(self):
        if self.order or len(self.long_sma) < self.params.long_period:
            return
            
        current_price = self.data.close[0]
        spread_value = self.spread[0]
        current_vol = self.volatility[0] / current_price if len(self.volatility) > 0 else 0
        
        # 价差过大且波动率适中时买入
        if (not self.position and 
            spread_value < -self.params.spread_threshold and
            current_vol > self.params.vol_threshold):
            
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 出场条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 价差收敛或止损止盈
            if (spread_value > -self.params.spread_threshold * 0.3 or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'日历价差策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')