#!/usr/bin/env python3
"""
综合策略测试系统
测试所有20个策略并生成详细报告
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
import traceback

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'advanced_strategies'))

# 导入所有策略
from btc_data import BTCDataFeed

# 原有策略
from btc_strategies.rsi_strategy import RSIMeanReversionStrategy
from btc_strategies.macd_strategy import MACDMomentumStrategy, AdvancedMACDStrategy
from btc_strategies.bollinger_strategy import BollingerBandsStrategy
from btc_strategies.btc_grid_strategy import BTCGridTradingStrategy, DynamicBTCGridStrategy

# 修复版策略
from fixed_strategies_test import FixedRSIStrategy, FixedMACDStrategy, SimpleBollingerStrategy

# 优化版策略
from optimized_strategies_2025 import OptimizedRSIStrategy, OptimizedMACDStrategy, EnhancedBollingerStrategy, EnhancedGridStrategy

# 新增策略
from momentum_strategies import TurtleTradingStrategy, MomentumBreakoutStrategy, RelativeStrengthStrategy, PriceVolumeStrategy
from mean_reversion_strategies import BollingerMeanReversionStrategy, ZScoreMeanReversionStrategy, OverboughtOversoldStrategy
from arbitrage_strategies import StatisticalArbitrageStrategy, PairsTradingStrategy, CalendarSpreadStrategy


class StrategyTester:
    """策略测试器"""
    
    def __init__(self, initial_cash=10000, commission=0.001):
        self.initial_cash = initial_cash
        self.commission = commission
        self.btc_feed = BTCDataFeed()
        self.test_results = []
        self.failed_strategies = []
        
    def test_single_strategy(self, strategy_class, strategy_name, params=None, 
                           start_date="2025-01-01", end_date="2025-08-23"):
        """测试单个策略"""
        try:
            print(f"🔄 测试 {strategy_name}...")
            
            cerebro = bt.Cerebro()
            
            # 添加策略
            if params:
                cerebro.addstrategy(strategy_class, **params)
            else:
                cerebro.addstrategy(strategy_class, print_log=False)
            
            # 获取数据
            bt_data, raw_data = self.btc_feed.get_backtrader_data(start_date, end_date)
            if bt_data is None:
                raise ValueError("无法获取数据")
            
            cerebro.adddata(bt_data)
            cerebro.broker.setcash(self.initial_cash)
            cerebro.broker.setcommission(commission=self.commission)
            
            # 运行回测
            start_value = cerebro.broker.getvalue()
            strategies = cerebro.run()
            final_value = cerebro.broker.getvalue()
            
            # 计算指标
            total_return = (final_value - start_value) / start_value
            return_pct = total_return * 100
            
            # 获取策略交易记录
            strategy_instance = strategies[0]
            trades = getattr(strategy_instance, 'trades', [])
            
            # 计算更多指标
            if trades:
                win_trades = [t for t in trades if t > 0]
                win_rate = len(win_trades) / len(trades)
                avg_return = sum(trades) / len(trades)
                max_loss = min(trades) if trades else 0
                max_gain = max(trades) if trades else 0
            else:
                win_rate = 0
                avg_return = 0
                max_loss = 0
                max_gain = 0
            
            result = {
                'name': strategy_name,
                'class': strategy_class.__name__,
                'return_pct': return_pct,
                'final_value': final_value,
                'total_trades': len(trades),
                'win_rate': win_rate,
                'avg_return': avg_return,
                'max_gain': max_gain,
                'max_loss': max_loss,
                'params': params,
                'status': 'success'
            }
            
            # 状态标记
            if return_pct > 30:
                status_emoji = "🏆"
            elif return_pct > 22.58:  # 基准
                status_emoji = "🟢"
            elif return_pct > 10:
                status_emoji = "🟡"
            elif return_pct > 0:
                status_emoji = "🟠"
            else:
                status_emoji = "🔴"
            
            print(f"   {status_emoji} {strategy_name}: {return_pct:.2f}% | 交易:{len(trades)} | 胜率:{win_rate*100:.1f}%")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ {strategy_name} 失败: {error_msg}")
            
            failed_result = {
                'name': strategy_name,
                'class': strategy_class.__name__,
                'error': error_msg,
                'params': params,
                'status': 'failed'
            }
            
            self.failed_strategies.append(failed_result)
            return None
    
    def run_comprehensive_test(self):
        """运行所有策略的综合测试"""
        print("🚀 开始综合策略测试")
        print("="*80)
        print(f"📅 测试时间: 2025-01-01 到 2025-08-23")
        print(f"💰 初始资金: ${self.initial_cash:,}")
        print(f"📊 手续费: {self.commission*100:.1f}%")
        print(f"🎯 BTC基准收益: +22.58%")
        print("="*80)
        
        # 定义所有策略
        strategies_to_test = [
            # 原有策略组
            ("原版RSI策略", RSIMeanReversionStrategy, None),
            ("原版MACD策略", MACDMomentumStrategy, None),
            ("增强MACD策略", AdvancedMACDStrategy, None),
            ("布林带突破策略", BollingerBandsStrategy, {'strategy_type': 'breakout'}),
            ("布林带均值回归策略", BollingerBandsStrategy, {'strategy_type': 'mean_reversion'}),
            ("原版网格策略", BTCGridTradingStrategy, None),
            ("动态网格策略", DynamicBTCGridStrategy, None),
            
            # 修复版策略组
            ("修复RSI策略", FixedRSIStrategy, None),
            ("修复MACD策略", FixedMACDStrategy, None),
            ("简化布林带策略", SimpleBollingerStrategy, None),
            
            # 优化版策略组
            ("优化RSI策略v2", OptimizedRSIStrategy, None),
            ("优化MACD策略v2", OptimizedMACDStrategy, None),
            ("增强布林带策略v2", EnhancedBollingerStrategy, None),
            ("增强网格策略v2", EnhancedGridStrategy, None),
            
            # 动量策略组
            ("海龟交易策略", TurtleTradingStrategy, None),
            ("动量突破策略", MomentumBreakoutStrategy, None),
            ("相对强度策略", RelativeStrengthStrategy, None),
            ("价量策略", PriceVolumeStrategy, None),
            
            # 均值回归策略组
            ("增强布林带均值回归", BollingerMeanReversionStrategy, None),
            ("Z-Score均值回归", ZScoreMeanReversionStrategy, None),
            ("多指标超买超卖", OverboughtOversoldStrategy, None),
            
            # 套利策略组
            ("统计套利策略", StatisticalArbitrageStrategy, None),
            ("配对交易策略", PairsTradingStrategy, None),
            ("日历价差策略", CalendarSpreadStrategy, None),
        ]
        
        print(f"\n📋 计划测试 {len(strategies_to_test)} 个策略")
        print("-"*80)
        
        # 逐一测试策略
        for i, (name, strategy_class, params) in enumerate(strategies_to_test, 1):
            print(f"\n[{i:2d}/{len(strategies_to_test)}]", end=" ")
            self.test_single_strategy(strategy_class, name, params)
        
        return self.test_results, self.failed_strategies
    
    def generate_comprehensive_report(self):
        """生成综合测试报告"""
        if not self.test_results and not self.failed_strategies:
            print("❌ 没有测试结果可以生成报告")
            return
        
        print(f"\n{'='*100}")
        print(f"📊 综合策略测试报告")
        print(f"{'='*100}")
        
        # 基准信息
        print(f"🎯 BTC基准收益率: +22.58%")
        print(f"📈 测试时间段: 2025年1月1日 - 2025年8月23日")
        print(f"💰 初始资金: ${self.initial_cash:,}")
        
        if self.test_results:
            # 按收益率排序
            sorted_results = sorted(self.test_results, key=lambda x: x['return_pct'], reverse=True)
            
            print(f"\n🏆 成功策略排行榜 (共{len(sorted_results)}个):")
            print("-"*100)
            print(f"{'排名':<4} {'策略名称':<25} {'收益率':<10} {'vs基准':<8} {'交易次数':<8} {'胜率':<8} {'评级'}")
            print("-"*100)
            
            for i, result in enumerate(sorted_results, 1):
                name = result['name'][:24]
                return_pct = result['return_pct']
                vs_benchmark = return_pct - 22.58
                trades = result['total_trades']
                win_rate = result['win_rate'] * 100
                
                # 评级系统
                if return_pct > 35:
                    rating = "🏆 卓越"
                elif return_pct > 25:
                    rating = "🥇 优秀"
                elif return_pct > 15:
                    rating = "🥈 良好"
                elif return_pct > 0:
                    rating = "🥉 一般"
                else:
                    rating = "❌ 亏损"
                
                print(f"{i:2d}.  {name:<25} {return_pct:>8.1f}% {vs_benchmark:>6.1f}% {trades:>6d} {win_rate:>6.1f}% {rating}")
            
            # 统计分析
            profitable_count = len([r for r in sorted_results if r['return_pct'] > 0])
            beat_benchmark_count = len([r for r in sorted_results if r['return_pct'] > 22.58])
            avg_return = sum(r['return_pct'] for r in sorted_results) / len(sorted_results)
            
            print(f"\n📈 统计摘要:")
            print(f"   总测试策略数: {len(sorted_results)}")
            print(f"   成功策略数: {profitable_count} ({profitable_count/len(sorted_results)*100:.1f}%)")
            print(f"   跑赢基准策略数: {beat_benchmark_count} ({beat_benchmark_count/len(sorted_results)*100:.1f}%)")
            print(f"   平均收益率: {avg_return:.2f}%")
            
            if sorted_results:
                best = sorted_results[0]
                print(f"   🏆 最佳策略: {best['name']}")
                print(f"   🎯 最高收益率: {best['return_pct']:.2f}%")
        
        # 失败策略分析
        if self.failed_strategies:
            print(f"\n❌ 失败策略分析 (共{len(self.failed_strategies)}个):")
            print("-"*100)
            
            error_types = {}
            for failed in self.failed_strategies:
                error = failed['error']
                if error in error_types:
                    error_types[error].append(failed['name'])
                else:
                    error_types[error] = [failed['name']]
            
            for error, strategies in error_types.items():
                print(f"🔸 错误类型: {error}")
                for strategy in strategies:
                    print(f"     - {strategy}")
                print()
        
        # 策略类别分析
        if self.test_results:
            print(f"\n📊 策略类别分析:")
            print("-"*50)
            
            # 按策略类别分组
            momentum_strategies = [r for r in sorted_results if any(x in r['name'] for x in ['MACD', '动量', '海龟', '突破', '相对强度', '价量'])]
            mean_reversion_strategies = [r for r in sorted_results if any(x in r['name'] for x in ['RSI', '布林', 'Z-Score', '超买超卖', '均值回归'])]
            grid_strategies = [r for r in sorted_results if '网格' in r['name']]
            arbitrage_strategies = [r for r in sorted_results if any(x in r['name'] for x in ['套利', '配对', '价差'])]
            
            categories = [
                ("动量策略", momentum_strategies),
                ("均值回归策略", mean_reversion_strategies),
                ("网格策略", grid_strategies),
                ("套利策略", arbitrage_strategies)
            ]
            
            for category_name, category_strategies in categories:
                if category_strategies:
                    avg_return = sum(s['return_pct'] for s in category_strategies) / len(category_strategies)
                    best_strategy = max(category_strategies, key=lambda x: x['return_pct'])
                    print(f"{category_name}: {len(category_strategies)}个, 平均收益{avg_return:.1f}%, 最佳{best_strategy['name']}({best_strategy['return_pct']:.1f}%)")
        
        print(f"\n{'='*100}")
        print(f"✅ 综合测试报告生成完成!")
        print(f"{'='*100}")


def main():
    """主函数"""
    print("🔬 比特币量化策略综合测试系统")
    print("   测试所有20+个策略并生成详细分析报告\n")
    
    try:
        # 创建测试器
        tester = StrategyTester(initial_cash=10000, commission=0.001)
        
        # 运行综合测试
        test_results, failed_strategies = tester.run_comprehensive_test()
        
        # 生成报告
        tester.generate_comprehensive_report()
        
        # 保存结果到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if test_results:
            results_df = pd.DataFrame(test_results)
            results_df.to_csv(f'strategy_test_results_{timestamp}.csv', index=False)
            print(f"\n💾 测试结果已保存到: strategy_test_results_{timestamp}.csv")
        
        if failed_strategies:
            failed_df = pd.DataFrame(failed_strategies)
            failed_df.to_csv(f'failed_strategies_{timestamp}.csv', index=False)
            print(f"💾 失败策略记录已保存到: failed_strategies_{timestamp}.csv")
        
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程出现错误: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()