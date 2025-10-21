#!/usr/bin/env python3
"""
比特币交易策略验证脚本

此脚本用于验证所有策略的基本功能和获取初步回测结果
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

try:
    from btc_backtest_framework import BTCStrategyBacktester
    from btc_strategies.rsi_strategy import RSIMeanReversionStrategy
    from btc_strategies.macd_strategy import MACDMomentumStrategy
    from btc_strategies.bollinger_strategy import BollingerBandsStrategy
    from btc_strategies.btc_grid_strategy import BTCGridTradingStrategy
    print("✅ 所有模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("请确保已安装必要的依赖包:")
    print("pip install yfinance pandas matplotlib backtrader")
    sys.exit(1)


def quick_validation():
    """快速验证策略功能"""
    print("\n" + "="*60)
    print("🚀 开始比特币交易策略验证")
    print("="*60)
    
    # 创建回测器
    backtest = BTCStrategyBacktester(initial_cash=10000, commission=0.001)
    
    # 定义测试策略
    test_strategies = [
        {
            'name': 'RSI均值回归策略',
            'strategy': RSIMeanReversionStrategy,
            'params': {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'print_log': False  # 减少输出
            }
        },
        {
            'name': 'MACD动量策略',
            'strategy': MACDMomentumStrategy,
            'params': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
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
                'print_log': False
            }
        },
        {
            'name': '比特币网格策略',
            'strategy': BTCGridTradingStrategy,
            'params': {
                'grid_spacing': 300,
                'grid_levels': 6,
                'base_order_size': 0.02,
                'print_log': False
            }
        }
    ]
    
    # 测试短期数据
    validation_results = []
    test_start = "2023-06-01"
    test_end = "2023-12-31"
    
    print(f"📅 测试时间段: {test_start} 到 {test_end}")
    print(f"💰 初始资金: $10,000")
    print(f"📊 手续费: 0.1%")
    
    for strategy_config in test_strategies:
        print(f"\n🔄 测试 {strategy_config['name']}...")
        
        try:
            result = backtest.run_single_strategy(
                strategy_config['strategy'],
                strategy_config['params'],
                test_start,
                test_end
            )
            
            if result:
                validation_results.append(result)
                print(f"✅ {strategy_config['name']} 验证成功")
            else:
                print(f"❌ {strategy_config['name']} 验证失败 - 无数据")
                
        except Exception as e:
            print(f"❌ {strategy_config['name']} 验证失败: {str(e)}")
    
    # 生成验证报告
    if validation_results:
        generate_validation_report(validation_results)
    else:
        print("\n❌ 没有成功的策略验证结果")
    
    return validation_results


def generate_validation_report(results):
    """生成验证报告"""
    if not results:
        return
    
    print("\n" + "="*80)
    print("📈 比特币交易策略验证报告")
    print("="*80)
    
    # 表头
    print(f"{'策略名称':<20} {'收益率':<10} {'夏普比率':<10} {'最大回撤':<10} {'交易次数':<8} {'胜率':<8} {'状态':<8}")
    print("-" * 80)
    
    # 策略结果
    for result in results:
        perf = result['performance']
        name = result['strategy_name'][:19]  # 截断长名称
        total_return = result['total_return'] * 100
        sharpe = perf.get('sharpe_ratio', 0)
        max_dd = perf.get('max_drawdown', 0) * 100
        trades = perf.get('total_trades', 0)
        win_rate = perf.get('win_rate', 0) * 100
        
        # 判断策略状态
        if total_return > 0 and sharpe > 0:
            status = "✅ 良好"
        elif total_return > -5:
            status = "⚠️  一般"
        else:
            status = "❌ 较差"
        
        print(f"{name:<20} {total_return:>8.1f}% {sharpe:>8.2f} {abs(max_dd):>8.1f}% {trades:>6} {win_rate:>6.1f}% {status}")
    
    # 总结
    profitable_strategies = [r for r in results if r['total_return'] > 0]
    
    print("\n" + "="*80)
    print("📋 验证总结:")
    print(f"   总测试策略数: {len(results)}")
    print(f"   盈利策略数: {len(profitable_strategies)}")
    print(f"   成功率: {len(profitable_strategies)/len(results)*100:.1f}%")
    
    if profitable_strategies:
        best_strategy = max(profitable_strategies, key=lambda x: x['total_return'])
        print(f"   最佳策略: {best_strategy['strategy_name']}")
        print(f"   最佳收益率: {best_strategy['total_return']*100:.2f}%")
    
    print("\n💡 验证建议:")
    if len(profitable_strategies) >= 2:
        print("   ✅ 多个策略显示盈利潜力，可进行更长期的回测")
        print("   ✅ 建议优化参数并进行组合策略测试")
    elif len(profitable_strategies) == 1:
        print("   ⚠️  只有一个策略盈利，建议调整其他策略参数")
        print("   ⚠️  考虑市场环境因素，扩大测试时间范围")
    else:
        print("   ❌ 所有策略在测试期间均亏损")
        print("   ❌ 建议重新评估策略参数和市场适应性")


def performance_benchmark():
    """性能基准测试"""
    print("\n" + "="*60)
    print("📊 比特币策略性能基准测试")
    print("="*60)
    
    try:
        from btc_data import BTCDataFeed
        
        # 获取比特币价格作为基准
        btc_feed = BTCDataFeed()
        btc_data = btc_feed.fetch_data("2023-06-01", "2023-12-31")
        
        if btc_data is not None and not btc_data.empty:
            start_price = btc_data['Close'].iloc[0]
            end_price = btc_data['Close'].iloc[-1]
            btc_return = (end_price - start_price) / start_price
            
            print(f"📈 BTC价格变化:")
            print(f"   期初价格: ${start_price:,.2f}")
            print(f"   期末价格: ${end_price:,.2f}")
            print(f"   买入持有收益率: {btc_return*100:.2f}%")
            print(f"   (这是策略需要超越的基准)")
            
        else:
            print("❌ 无法获取BTC基准数据")
            
    except Exception as e:
        print(f"❌ 基准测试失败: {e}")


if __name__ == "__main__":
    print("🔍 比特币量化策略验证工具")
    print("   此工具将验证所有策略的功能并提供初步性能评估\n")
    
    # 检查依赖
    try:
        import yfinance
        import backtrader
        import pandas
        import matplotlib
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install yfinance pandas matplotlib backtrader")
        sys.exit(1)
    
    # 运行验证
    try:
        results = quick_validation()
        
        # 运行基准测试
        performance_benchmark()
        
        print("\n" + "="*60)
        print("✅ 策略验证完成!")
        print("   可以运行 btc_backtest_framework.py 进行完整回测")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断验证过程")
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()