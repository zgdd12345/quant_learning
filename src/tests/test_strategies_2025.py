#!/usr/bin/env python3
"""
在2025年比特币数据上测试所有量化策略
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from btc_backtest_framework import BTCStrategyBacktester
from btc_strategies.rsi_strategy import RSIMeanReversionStrategy
from btc_strategies.macd_strategy import MACDMomentumStrategy, AdvancedMACDStrategy
from btc_strategies.bollinger_strategy import BollingerBandsStrategy, AdaptiveBollingerStrategy
from btc_strategies.btc_grid_strategy import BTCGridTradingStrategy, DynamicBTCGridStrategy


def test_all_strategies_2025():
    """在2025年数据上测试所有策略"""
    print("🚀 开始在2025年比特币数据上测试所有量化策略")
    print("="*70)
    
    # 创建回测器
    backtest = BTCStrategyBacktester(initial_cash=10000, commission=0.001)
    
    # 定义所有策略配置
    strategies_config = [
        {
            'name': 'RSI均值回归策略',
            'strategy': RSIMeanReversionStrategy,
            'params': {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'print_log': False
            }
        },
        {
            'name': '基础MACD动量策略',
            'strategy': MACDMomentumStrategy,
            'params': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
                'stop_loss': 0.08,
                'take_profit': 0.15,
                'print_log': False
            }
        },
        {
            'name': '增强MACD策略',
            'strategy': AdvancedMACDStrategy,
            'params': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
                'rsi_period': 14,
                'trailing_stop': True,
                'stop_loss': 0.06,
                'take_profit': 0.12,
                'print_log': False
            }
        },
        {
            'name': '布林带突破策略',
            'strategy': BollingerBandsStrategy,
            'params': {
                'bb_period': 20,
                'bb_dev': 2.0,
                'strategy_type': 'breakout',
                'volume_filter': True,
                'stop_loss': 0.06,
                'take_profit': 0.12,
                'print_log': False
            }
        },
        {
            'name': '布林带均值回归策略',
            'strategy': BollingerBandsStrategy,
            'params': {
                'bb_period': 20,
                'bb_dev': 2.0,
                'strategy_type': 'mean_reversion',
                'volume_filter': True,
                'stop_loss': 0.06,
                'take_profit': 0.12,
                'print_log': False
            }
        },
        {
            'name': '自适应布林带策略',
            'strategy': AdaptiveBollingerStrategy,
            'params': {
                'bb_period': 20,
                'adaptive_position': True,
                'stop_loss': 0.08,
                'take_profit': 0.15,
                'print_log': False
            }
        },
        {
            'name': 'BTC网格交易策略',
            'strategy': BTCGridTradingStrategy,
            'params': {
                'grid_spacing': 300,
                'grid_levels': 8,
                'base_order_size': 0.02,
                'max_position': 0.4,
                'take_profit_pct': 0.015,
                'print_log': False
            }
        },
        {
            'name': '动态BTC网格策略',
            'strategy': DynamicBTCGridStrategy,
            'params': {
                'grid_spacing': 300,
                'grid_levels': 6,
                'base_order_size': 0.02,
                'max_position': 0.3,
                'take_profit_pct': 0.015,
                'print_log': False
            }
        }
    ]
    
    # 2025年测试时间段
    test_start = "2025-01-01"
    test_end = "2025-08-23"  # 到目前为止的数据
    
    print(f"📅 测试时间段: {test_start} 到 {test_end}")
    print(f"💰 初始资金: $10,000")
    print(f"📊 手续费: 0.1%")
    print(f"🎯 BTC基准收益率: +22.58%")
    
    results = []
    
    for i, strategy_config in enumerate(strategies_config, 1):
        print(f"\n🔄 [{i}/{len(strategies_config)}] 测试 {strategy_config['name']}...")
        
        try:
            result = backtest.run_single_strategy(
                strategy_config['strategy'],
                strategy_config['params'],
                test_start,
                test_end
            )
            
            if result:
                results.append({
                    'name': strategy_config['name'],
                    'result': result
                })
                
                # 简要结果
                perf = result['performance']
                total_return = result['total_return'] * 100
                sharpe = perf.get('sharpe_ratio', 0)
                max_dd = perf.get('max_drawdown', 0) * 100
                trades = perf.get('total_trades', 0)
                win_rate = perf.get('win_rate', 0) * 100
                
                status = "🟢" if total_return > 22.58 else "🟡" if total_return > 0 else "🔴"
                print(f"   {status} 收益: {total_return:.1f}% | 夏普: {sharpe:.2f} | 回撤: {abs(max_dd):.1f}% | 交易: {trades} | 胜率: {win_rate:.1f}%")
                
        except Exception as e:
            print(f"   ❌ 测试失败: {str(e)}")
    
    return results


def generate_2025_performance_report(results):
    """生成2025年性能报告"""
    if not results:
        print("\n❌ 没有成功的策略测试结果")
        return
    
    print(f"\n{'='*90}")
    print(f"📈 2025年比特币量化策略性能报告 (截至8月23日)")
    print(f"{'='*90}")
    
    # 基准信息
    print(f"🎯 BTC买入持有基准: +22.58%")
    print(f"📊 市场波动率: 36.51%")
    print(f"💹 价格区间: $76,272 - $123,344")
    
    print(f"\n{'策略名称':<25} {'收益率':<10} {'vs基准':<8} {'夏普':<8} {'回撤':<8} {'交易':<6} {'胜率':<8} {'评级'}")
    print("-" * 90)
    
    # 排序：按收益率排序
    sorted_results = sorted(results, key=lambda x: x['result']['total_return'], reverse=True)
    
    for item in sorted_results:
        name = item['name'][:24]
        result = item['result']
        perf = result['performance']
        
        total_return = result['total_return'] * 100
        vs_benchmark = total_return - 22.58
        sharpe = perf.get('sharpe_ratio', 0)
        max_dd = abs(perf.get('max_drawdown', 0)) * 100
        trades = perf.get('total_trades', 0)
        win_rate = perf.get('win_rate', 0) * 100
        
        # 评级系统
        if total_return > 30 and sharpe > 1.0:
            rating = "🏆 优秀"
        elif total_return > 22.58 and sharpe > 0.5:
            rating = "🥇 良好"
        elif total_return > 10:
            rating = "🥈 一般"
        elif total_return > 0:
            rating = "🥉 较差"
        else:
            rating = "❌ 亏损"
        
        print(f"{name:<25} {total_return:>8.1f}% {vs_benchmark:>6.1f}% {sharpe:>6.2f} {max_dd:>6.1f}% {trades:>4} {win_rate:>6.1f}% {rating}")
    
    # 统计分析
    profitable_count = len([r for r in results if r['result']['total_return'] > 0])
    beat_benchmark_count = len([r for r in results if r['result']['total_return'] > 0.2258])
    
    print(f"\n{'='*90}")
    print(f"📋 统计摘要:")
    print(f"   总测试策略数: {len(results)}")
    print(f"   盈利策略数: {profitable_count} ({profitable_count/len(results)*100:.1f}%)")
    print(f"   跑赢基准策略数: {beat_benchmark_count} ({beat_benchmark_count/len(results)*100:.1f}%)")
    
    if beat_benchmark_count > 0:
        best_strategy = sorted_results[0]
        best_name = best_strategy['name']
        best_return = best_strategy['result']['total_return'] * 100
        best_sharpe = best_strategy['result']['performance'].get('sharpe_ratio', 0)
        
        print(f"   🏆 最佳策略: {best_name}")
        print(f"   🎯 最佳收益率: {best_return:.2f}%")
        print(f"   📊 最佳夏普比率: {best_sharpe:.3f}")
    
    # 建议
    print(f"\n💡 策略优化建议:")
    if beat_benchmark_count >= 3:
        print(f"   ✅ 多个策略表现优秀，可考虑组合策略")
        print(f"   ✅ 建议进一步优化参数以提升收益")
    elif beat_benchmark_count >= 1:
        print(f"   ⚠️  有优秀策略但需要优化其他策略")
        print(f"   ⚠️  考虑调整止损止盈参数")
    else:
        print(f"   ❌ 所有策略均未跑赢基准")
        print(f"   ❌ 需要重新评估策略逻辑和参数")


if __name__ == "__main__":
    print("📊 2025年比特币量化策略验证")
    print("   在真实的2025年市场数据上测试所有策略\n")
    
    try:
        # 运行策略测试
        results = test_all_strategies_2025()
        
        # 生成报告
        if results:
            generate_2025_performance_report(results)
        
        print(f"\n{'='*70}")
        print("✅ 2025年策略验证完成！")
        print("   准备进行策略优化...")
        print(f"{'='*70}")
        
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断测试过程")
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()