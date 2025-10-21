#!/usr/bin/env python3
"""
均值回归类策略集合
包含3个基于均值回归的交易策略
"""

import backtrader as bt
import pandas as pd
import numpy as np


class BollingerMeanReversionStrategy(bt.Strategy):
    """
    增强版布林带均值回归策略
    
    策略逻辑:
    - 价格触及下轨买入，触及上轨卖出
    - 结合RSI确认超买超卖
    - 使用ATR动态止损
    """
    
    params = (
        ('bb_period', 20),
        ('bb_dev', 2.2),
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('atr_period', 14),
        ('atr_multiplier', 1.5),
        ('position_size', 0.9),
        ('print_log', False),
    )
    
    def __init__(self):
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )
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
                self.log(f'布林带买入: {order.executed.price:.2f}')
            elif order.issell():
                if self.buy_price:
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    self.trades.append(profit_pct)
                    self.log(f'布林带卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def next(self):
        if self.order or len(self.bb) < self.params.bb_period:
            return
            
        current_price = self.data.close[0]
        bb_lower = self.bb.bot[0]
        bb_upper = self.bb.top[0]
        rsi_val = self.rsi[0]
        
        # 触及下轨 + RSI超卖确认买入
        if (not self.position and 
            current_price <= bb_lower * 1.005 and
            rsi_val < self.params.rsi_oversold):
            
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 出场条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 触及上轨 + RSI超买 或 ATR止损
            atr_stop = (self.atr[0] * self.params.atr_multiplier) / self.buy_price if len(self.atr) > 0 else 0.08
            
            if ((current_price >= bb_upper * 0.995 and rsi_val > self.params.rsi_overbought) or
                return_pct < -atr_stop):
                
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'增强布林带策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class ZScoreMeanReversionStrategy(bt.Strategy):
    """
    Z-Score均值回归策略
    
    策略逻辑:
    - 计算价格的Z-Score
    - Z-Score < -2时买入（价格严重偏离均值）
    - Z-Score > 2时卖出（价格严重高估）
    """
    
    params = (
        ('lookback_period', 20),    # 回望周期
        ('entry_zscore', -2.0),     # 入场Z-Score阈值
        ('exit_zscore', 2.0),       # 出场Z-Score阈值
        ('stop_loss', 0.10),
        ('position_size', 0.85),
        ('print_log', False),
    )
    
    def __init__(self):
        self.price_sma = bt.indicators.SMA(self.data.close, period=self.params.lookback_period)
        self.price_std = bt.indicators.StdDev(self.data.close, period=self.params.lookback_period)
        
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
                self.log(f'Z-Score买入: {order.executed.price:.2f}')
            elif order.issell():
                if self.buy_price:
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    self.trades.append(profit_pct)
                    self.log(f'Z-Score卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def calculate_zscore(self):
        """计算当前价格的Z-Score"""
        if len(self.price_sma) == 0 or len(self.price_std) == 0:
            return 0
        
        current_price = self.data.close[0]
        mean_price = self.price_sma[0]
        std_price = self.price_std[0]
        
        if std_price == 0:
            return 0
        
        return (current_price - mean_price) / std_price
    
    def next(self):
        if self.order or len(self.price_sma) < self.params.lookback_period:
            return
            
        current_price = self.data.close[0]
        zscore = self.calculate_zscore()
        
        # Z-Score过低买入（价格被低估）
        if not self.position and zscore < self.params.entry_zscore:
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 出场条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # Z-Score回归正常区间或止损
            if zscore > self.params.exit_zscore * 0.5 or return_pct < -self.params.stop_loss:
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'Z-Score策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')


class OverboughtOversoldStrategy(bt.Strategy):
    """
    多指标超买超卖策略
    
    策略逻辑:
    - 结合RSI、Stochastic、Williams %R三个指标
    - 三指标同时超卖时买入
    - 三指标同时超买时卖出
    """
    
    params = (
        ('rsi_period', 14),
        ('stoch_period', 14),
        ('williams_period', 14),
        ('oversold_threshold', 25),
        ('overbought_threshold', 75),
        ('confirmation_count', 2),   # 至少需要几个指标确认
        ('stop_loss', 0.08),
        ('take_profit', 0.18),
        ('position_size', 0.9),
        ('print_log', False),
    )
    
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.stoch = bt.indicators.Stochastic(self.data, period=self.params.stoch_period)
        self.williams = bt.indicators.WilliamsR(self.data, period=self.params.williams_period)
        
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
                self.log(f'多指标买入: {order.executed.price:.2f}')
            elif order.issell():
                if self.buy_price:
                    profit_pct = ((order.executed.price - self.buy_price) / self.buy_price) * 100
                    self.trades.append(profit_pct)
                    self.log(f'多指标卖出: {order.executed.price:.2f}, 收益: {profit_pct:.2f}%')
        self.order = None
    
    def count_oversold_signals(self):
        """统计超卖信号数量"""
        signals = 0
        
        if len(self.rsi) > 0 and self.rsi[0] < self.params.oversold_threshold:
            signals += 1
            
        if len(self.stoch) > 0 and self.stoch.percK[0] < self.params.oversold_threshold:
            signals += 1
            
        if len(self.williams) > 0 and self.williams[0] < -100 + self.params.oversold_threshold:
            signals += 1
            
        return signals
    
    def count_overbought_signals(self):
        """统计超买信号数量"""
        signals = 0
        
        if len(self.rsi) > 0 and self.rsi[0] > self.params.overbought_threshold:
            signals += 1
            
        if len(self.stoch) > 0 and self.stoch.percK[0] > self.params.overbought_threshold:
            signals += 1
            
        if len(self.williams) > 0 and self.williams[0] > -100 + self.params.overbought_threshold:
            signals += 1
            
        return signals
    
    def next(self):
        if self.order:
            return
            
        min_periods = max(self.params.rsi_period, self.params.stoch_period, self.params.williams_period)
        if len(self.data) < min_periods:
            return
            
        current_price = self.data.close[0]
        oversold_count = self.count_oversold_signals()
        overbought_count = self.count_overbought_signals()
        
        # 多指标超卖买入
        if not self.position and oversold_count >= self.params.confirmation_count:
            size = (self.broker.getcash() * self.params.position_size) / current_price
            self.order = self.buy(size=size)
        
        # 出场条件
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            # 多指标超买或止损止盈
            if (overbought_count >= self.params.confirmation_count or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                
                self.order = self.sell(size=self.position.size)
    
    def stop(self):
        if self.params.print_log and self.trades:
            win_rate = len([t for t in self.trades if t > 0]) / len(self.trades)
            avg_return = sum(self.trades) / len(self.trades)
            self.log(f'多指标策略 - 交易: {len(self.trades)}, 胜率: {win_rate:.2%}, 平均收益: {avg_return:.2f}%')