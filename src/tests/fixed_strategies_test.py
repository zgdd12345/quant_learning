#!/usr/bin/env python3
"""
修复版策略测试 - 2025年数据
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

import backtrader as bt
import pandas as pd
import numpy as np
from btc_data import BTCDataFeed


class FixedRSIStrategy(bt.Strategy):
    """修复版RSI策略"""
    params = (
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('stop_loss', 0.05),
        ('take_profit', 0.10),
    )
    
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.order = None
        self.buy_price = None
        
    def next(self):
        if self.order:
            return
        
        # 确保RSI有值
        if len(self.rsi) < self.params.rsi_period:
            return
            
        current_price = self.data.close[0]
        rsi_val = self.rsi[0]
        
        if not self.position and rsi_val < self.params.rsi_oversold:
            size = 0.95 * self.broker.getcash() / current_price
            self.order = self.buy(size=size)
            self.buy_price = current_price
            
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            if (rsi_val > self.params.rsi_overbought or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                self.order = self.sell(size=self.position.size)
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None


class FixedMACDStrategy(bt.Strategy):
    """修复版MACD策略"""
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
        ('stop_loss', 0.08),
        ('take_profit', 0.15),
    )
    
    def __init__(self):
        self.macd = bt.indicators.MACDHisto(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )
        self.order = None
        self.buy_price = None
        
    def next(self):
        if self.order:
            return
        
        # 确保MACD有足够数据
        if len(self.macd) < max(self.params.fast_period, self.params.slow_period):
            return
            
        current_price = self.data.close[0]
        macd_line = self.macd.macd[0]
        signal_line = self.macd.signal[0]
        
        if not self.position and macd_line > signal_line and self.macd.macd[-1] <= self.macd.signal[-1]:
            size = 0.95 * self.broker.getcash() / current_price
            self.order = self.buy(size=size)
            self.buy_price = current_price
            
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            if (macd_line < signal_line and self.macd.macd[-1] >= self.macd.signal[-1] or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                self.order = self.sell(size=self.position.size)
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None


class SimpleBollingerStrategy(bt.Strategy):
    """简化版布林带策略"""
    params = (
        ('bb_period', 20),
        ('bb_dev', 2.0),
        ('stop_loss', 0.06),
        ('take_profit', 0.12),
    )
    
    def __init__(self):
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )
        self.order = None
        self.buy_price = None
        
    def next(self):
        if self.order:
            return
            
        if len(self.bb) < self.params.bb_period:
            return
            
        current_price = self.data.close[0]
        bb_top = self.bb.top[0]
        bb_bot = self.bb.bot[0]
        
        if not self.position and current_price <= bb_bot:
            size = 0.95 * self.broker.getcash() / current_price
            self.order = self.buy(size=size)
            self.buy_price = current_price
            
        elif self.position and self.buy_price:
            return_pct = (current_price - self.buy_price) / self.buy_price
            
            if (current_price >= bb_top or
                return_pct < -self.params.stop_loss or
                return_pct > self.params.take_profit):
                self.order = self.sell(size=self.position.size)
    
    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None


def run_strategy_test(strategy_class, strategy_name, params=None):
    """运行单个策略测试"""
    try:
        cerebro = bt.Cerebro()
        
        if params:
            cerebro.addstrategy(strategy_class, **params)
        else:
            cerebro.addstrategy(strategy_class)
        
        # 获取2025年数据
        btc_feed = BTCDataFeed()
        bt_data, raw_data = btc_feed.get_backtrader_data("2025-01-01", "2025-08-23")
        
        if bt_data is None:
            return None
            
        cerebro.adddata(bt_data)
        cerebro.broker.setcash(10000.0)
        cerebro.broker.setcommission(commission=0.001)
        
        start_value = cerebro.broker.getvalue()
        cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        total_return = (final_value - start_value) / start_value
        
        result = {
            'name': strategy_name,
            'start_value': start_value,
            'final_value': final_value,
            'total_return': total_return,
            'return_pct': total_return * 100
        }
        
        return result
        
    except Exception as e:
        print(f"❌ {strategy_name} 测试失败: {e}")
        return None


def main():
    """主测试函数"""
    print("🚀 修复版2025年比特币策略测试")
    print("="*50)
    
    # 测试策略配置
    strategies = [
        ('RSI均值回归策略', FixedRSIStrategy, {'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70}),
        ('MACD动量策略', FixedMACDStrategy, {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}),
        ('布林带均值回归策略', SimpleBollingerStrategy, {'bb_period': 20, 'bb_dev': 2.0}),
    ]
    
    results = []
    
    for name, strategy_class, params in strategies:
        print(f"🔄 测试 {name}...")
        result = run_strategy_test(strategy_class, name, params)
        if result:
            results.append(result)
            print(f"   ✅ 收益率: {result['return_pct']:.2f}%")
        else:
            print(f"   ❌ 测试失败")
    
    return results


if __name__ == "__main__":
    results = main()
    
    if results:
        print("\n📊 2025年策略测试结果:")
        print("-" * 50)
        for result in results:
            status = "🟢" if result['return_pct'] > 22.58 else "🟡" if result['return_pct'] > 0 else "🔴"
            print(f"{status} {result['name']}: {result['return_pct']:.2f}%")
    else:
        print("\n❌ 没有成功的测试结果")