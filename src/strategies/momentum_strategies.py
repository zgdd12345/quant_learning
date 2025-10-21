#!/usr/bin/env python3
"""
动量类策略集合
包含4个基于动量的交易策略
"""

import backtrader as bt
import pandas as pd
import numpy as np


class TurtleTradingStrategy(bt.Strategy):
    """
    海龟交易策略
    
    策略逻辑:
    - 价格突破20日最高价买入
    - 价格跌破10日最低价卖出
    - 使用ATR动态止损
    """
    
    params = (
        ('entry_period', 20),      # 入场突破周期
        ('exit_period', 10),       # 出场突破周期
        ('atr_period', 20),        # ATR周期
        ('atr_multiplier', 2.0),   # ATR止损倍数
        ('position_size', 0.02),   # 每次交易仓位大小
        ('max_units', 4),          # 最大加仓单位
        ('print_log', False),
    )
    
    def __init__(self):
        self.high_n = bt.indicators.Highest(self.data.high, period=self.params.entry_period)
        self.low_n = bt.indicators.Lowest(self.data.low, period=self.params.exit_period)
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        
        self.order = None
        self.units = 0  # 当前持仓单位数
        self.entry_prices = []  # 记录入场价格
        self.trades = []
        
    def log(self, txt, dt=None):
        if self.params.print_log:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.units += 1
                self.entry_prices.append(order.executed.price)
                self.log(f'海龟买入: {order.executed.price:.2f}, 单位数: {self.units}')
            elif order.issell():
                if self.entry_prices:
                    avg_entry = sum(self.entry_prices) / len(self.entry_prices)
                    profit_pct = ((order.executed.price - avg_entry) / avg_entry) * 100
                    self.trades.append(profit_pct)
                    self.log(f'海龟卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
                self.units = 0
                self.entry_prices = []
        self.order = None
    
    def next(self):
        if self.order:
            return
            
        current_price = self.data.close[0]
        high_n = self.high_n[0]
        low_n = self.low_n[0]
        
        # 突破买入条件
        if (not self.position and 
            current_price >= high_n and 
            len(self.atr) >= self.params.atr_period):
            
            # 计算仓位大小
            account_value = self.broker.getvalue()
            dollar_volatility = self.atr[0] * self.params.position_size
            shares = (account_value * self.params.position_size) / dollar_volatility
            
            self.order = self.buy(size=shares)
        
        # 加仓条件
        elif (self.position and 
              self.units < self.params.max_units and
              len(self.entry_prices) > 0):
            
            last_entry = self.entry_prices[-1]
            if current_price >= last_entry + (0.5 * self.atr[0]):
                account_value = self.broker.getvalue()
                dollar_volatility = self.atr[0] * self.params.position_size
                shares = (account_value * self.params.position_size) / dollar_volatility
                
                self.order = self.buy(size=shares)
        
        # 退出条件
        elif (self.position and 
              (current_price <= low_n or 
               (len(self.entry_prices) > 0 and 
                current_price <= self.entry_prices[0] - (self.params.atr_multiplier * self.atr[0])))):
            
            self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'海龟策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class MomentumBreakoutStrategy(bt.Strategy):
    """
    动量突破策略
    
    策略逻辑:
    - 计算价格动量和成交量动量
    - 双动量确认时入场
    - 动量消失时出场
    """
    
    params = (
        ('momentum_period', 14),    # 动量计算周期
        ('volume_period', 20),      # 成交量均线周期
        ('momentum_threshold', 0.05), # 动量阈值
        ('volume_threshold', 1.5),   # 成交量阈值
        ('stop_loss', 0.08),
        ('take_profit', 0.20),
        ('position_size', 0.9),
        ('print_log', False),
    )
    
    def __init__(self):
        # 价格动量
        self.price_momentum = bt.indicators.ROC(
            self.data.close, 
            period=self.params.momentum_period
        )
        
        # 成交量动量
        self.volume_sma = bt.indicators.SMA(
            self.data.volume, 
            period=self.params.volume_period
        )
        
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
                self.log(f'动量买入: {order.executed.price:.2f}')
            elif order.issell():
                if self.buy_price:
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    self.trades.append(profit_pct)
                    self.log(f'动量卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def next(self):
        if self.order:
            return
            
        current_price = self.data.close[0]
        price_mom = self.price_momentum[0] / 100  # 转换为小数
        volume_ratio = self.data.volume[0] / self.volume_sma[0] if len(self.volume_sma) > 0 else 1
        
        # 双动量突破买入
        if (not self.position and 
            price_mom > self.params.momentum_threshold and
            volume_ratio > self.params.volume_threshold):
            
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 出场条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 动量消失或止损止盈
            if (price_mom < self.params.momentum_threshold * 0.3 or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'动量突破策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class RelativeStrengthStrategy(bt.Strategy):
    """
    相对强度策略
    
    策略逻辑:
    - 计算相对强度指标
    - 强势时做多，弱势时观望
    - 结合趋势过滤
    """
    
    params = (
        ('rs_period', 14),         # 相对强度周期
        ('trend_period', 50),      # 趋势过滤周期
        ('rs_threshold', 1.1),     # 相对强度阈值
        ('stop_loss', 0.10),
        ('take_profit', 0.25),
        ('position_size', 0.85),
        ('print_log', False),
    )
    
    def __init__(self):
        # 使用收盘价作为基准计算相对强度
        self.price_change = self.data.close / self.data.close(-1)
        self.rs = bt.indicators.SMA(self.price_change, period=self.params.rs_period)
        
        # 趋势过滤
        self.trend_sma = bt.indicators.SMA(self.data.close, period=self.params.trend_period)
        
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
                self.log(f'相对强度买入: {order.executed.price:.2f}')
            elif order.issell():
                if self.buy_price:
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    self.trades.append(profit_pct)
                    self.log(f'相对强度卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def next(self):
        if self.order:
            return
            
        current_price = self.data.close[0]
        rs_value = self.rs[0]
        
        # 趋势确认
        trend_up = current_price > self.trend_sma[0] if len(self.trend_sma) > 0 else True
        
        # 强势买入
        if (not self.position and 
            rs_value > self.params.rs_threshold and
            trend_up):
            
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 出场条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 相对强度减弱或止损止盈
            if (rs_value < self.params.rs_threshold * 0.9 or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'相对强度策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class PriceVolumeStrategy(bt.Strategy):
    """
    价量策略
    
    策略逻辑:
    - 价格上涨配合成交量放大确认买入
    - 价格下跌配合成交量萎缩确认卖出
    - 量价背离时谨慎交易
    """
    
    params = (
        ('volume_period', 20),      # 成交量均线周期
        ('price_period', 5),        # 价格变化周期
        ('volume_threshold', 1.3),  # 成交量放大阈值
        ('price_threshold', 0.02),  # 价格变化阈值
        ('stop_loss', 0.06),
        ('take_profit', 0.15),
        ('position_size', 0.9),
        ('print_log', False),
    )
    
    def __init__(self):
        self.volume_sma = bt.indicators.SMA(self.data.volume, period=self.params.volume_period)
        self.price_change = bt.indicators.ROC(self.data.close, period=self.params.price_period)
        
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
                self.log(f'价量买入: {order.executed.price:.2f}')
            elif order.issell():
                if self.buy_price:
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    self.trades.append(profit_pct)
                    self.log(f'价量卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def next(self):
        if self.order or len(self.volume_sma) == 0:
            return
            
        current_price = self.data.close[0]
        volume_ratio = self.data.volume[0] / self.volume_sma[0]
        price_change_pct = self.price_change[0] / 100
        
        # 价涨量增买入
        if (not self.position and 
            price_change_pct > self.params.price_threshold and
            volume_ratio > self.params.volume_threshold):
            
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 出场条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 价跌量缩或止损止盈
            if ((price_change_pct < -self.params.price_threshold and volume_ratio < 0.8) or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'价量策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')