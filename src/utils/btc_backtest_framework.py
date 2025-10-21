import backtrader as bt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from btc_data import BTCDataFeed
from btc_strategies.rsi_strategy import RSIMeanReversionStrategy
from btc_strategies.macd_strategy import MACDMomentumStrategy, AdvancedMACDStrategy
from btc_strategies.bollinger_strategy import BollingerBandsStrategy, AdaptiveBollingerStrategy
from btc_strategies.btc_grid_strategy import BTCGridTradingStrategy, DynamicBTCGridStrategy


class PerformanceAnalyzer(bt.Analyzer):
    """性能分析器"""
    
    def __init__(self):
        self.trades = []
        self.daily_values = []
        self.start_value = None
        self.drawdowns = []
        self.returns = []
    
    def start(self):
        self.start_value = self.strategy.broker.getvalue()
    
    def next(self):
        current_value = self.strategy.broker.getvalue()
        self.daily_values.append({
            'date': self.strategy.datas[0].datetime.date(0),
            'value': current_value,
            'cash': self.strategy.broker.getcash()
        })
        
        # 计算日收益率
        if len(self.daily_values) > 1:
            prev_value = self.daily_values[-2]['value']
            daily_return = (current_value - prev_value) / prev_value
            self.returns.append(daily_return)
    
    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append({
                'date': self.strategy.datas[0].datetime.date(0),
                'pnl': trade.pnl,
                'pnl_pct': (trade.pnl / trade.price) * 100,
                'duration': (trade.dtclose - trade.dtopen),
                'entry_price': trade.price,
                'exit_price': trade.price + (trade.pnl / trade.size)
            })
    
    def get_analysis(self):
        if not self.daily_values or not self.start_value:
            return {}
        
        df = pd.DataFrame(self.daily_values)
        final_value = df['value'].iloc[-1]
        
        # 基本指标
        total_return = (final_value - self.start_value) / self.start_value
        trading_days = len(df)
        annualized_return = (1 + total_return) ** (365 / trading_days) - 1
        
        # 风险指标
        returns_array = np.array(self.returns) if self.returns else np.array([0])
        volatility = np.std(returns_array) * np.sqrt(365)
        sharpe_ratio = (annualized_return - 0.02) / volatility if volatility > 0 else 0
        
        # 最大回撤
        df['peak'] = df['value'].cummax()
        df['drawdown'] = (df['value'] - df['peak']) / df['peak']
        max_drawdown = df['drawdown'].min()
        
        # 交易统计
        trades_df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades_df),
            'win_rate': len(trades_df[trades_df['pnl'] > 0]) / len(trades_df) if len(trades_df) > 0 else 0,
            'avg_return': trades_df['pnl_pct'].mean() if len(trades_df) > 0 else 0,
            'start_value': self.start_value,
            'final_value': final_value,
            'daily_data': df,
            'trades_data': trades_df
        }


class BTCStrategyBacktester:
    """比特币策略回测框架"""
    
    def __init__(self, initial_cash=10000, commission=0.001):
        self.initial_cash = initial_cash
        self.commission = commission
        self.btc_feed = BTCDataFeed()
        self.results = {}
    
    def run_single_strategy(self, strategy_class, strategy_params=None, 
                          start_date="2022-01-01", end_date="2023-12-31"):
        """运行单个策略回测"""
        cerebro = bt.Cerebro()
        
        # 添加性能分析器
        cerebro.addanalyzer(PerformanceAnalyzer, _name='performance')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        
        # 添加策略
        if strategy_params:
            cerebro.addstrategy(strategy_class, **strategy_params)
        else:
            cerebro.addstrategy(strategy_class)
        
        # 获取数据
        bt_data, raw_data = self.btc_feed.get_backtrader_data(start_date, end_date)
        if bt_data is None:
            print(f"无法获取数据: {start_date} 到 {end_date}")
            return None
        
        cerebro.adddata(bt_data)
        
        # 设置资金和手续费
        cerebro.broker.setcash(self.initial_cash)
        cerebro.broker.setcommission(commission=self.commission)
        
        # 运行回测
        print(f"\n{'='*50}")
        print(f"回测策略: {strategy_class.__name__}")
        print(f"时间范围: {start_date} 到 {end_date}")
        print(f"初始资金: {self.initial_cash}")
        print(f"{'='*50}")
        
        start_value = cerebro.broker.getvalue()
        strategies = cerebro.run()
        final_value = cerebro.broker.getvalue()
        
        # 获取分析结果
        strategy = strategies[0]
        performance = strategy.analyzers.performance.get_analysis()
        
        result = {
            'strategy_name': strategy_class.__name__,
            'start_date': start_date,
            'end_date': end_date,
            'initial_cash': self.initial_cash,
            'final_value': final_value,
            'total_return': (final_value - start_value) / start_value,
            'performance': performance,
            'raw_data': raw_data
        }
        
        self.print_results(result)
        return result
    
    def run_strategy_comparison(self, strategies_config, 
                               start_date="2022-01-01", end_date="2023-12-31"):
        """运行多策略对比"""
        results = []
        
        print(f"\n{'='*60}")
        print(f"比特币交易策略对比分析")
        print(f"时间范围: {start_date} 到 {end_date}")
        print(f"初始资金: {self.initial_cash}")
        print(f"{'='*60}")
        
        for config in strategies_config:
            result = self.run_single_strategy(
                config['strategy'], 
                config.get('params', {}),
                start_date, 
                end_date
            )
            if result:
                results.append(result)
        
        # 生成对比报告
        if results:
            self.generate_comparison_report(results)
            self.plot_strategy_comparison(results)
        
        return results
    
    def print_results(self, result):
        """打印回测结果"""
        perf = result['performance']
        
        print(f"\n📊 {result['strategy_name']} 回测结果:")
        print(f"   总收益率: {result['total_return']*100:.2f}%")
        print(f"   年化收益率: {perf.get('annualized_return', 0)*100:.2f}%")
        print(f"   夏普比率: {perf.get('sharpe_ratio', 0):.3f}")
        print(f"   最大回撤: {perf.get('max_drawdown', 0)*100:.2f}%")
        print(f"   年化波动率: {perf.get('volatility', 0)*100:.2f}%")
        print(f"   交易次数: {perf.get('total_trades', 0)}")
        print(f"   胜率: {perf.get('win_rate', 0)*100:.2f}%")
        print(f"   平均收益: {perf.get('avg_return', 0):.2f}%")
        print(f"   最终资金: {result['final_value']:.2f}")
    
    def generate_comparison_report(self, results):
        """生成策略对比报告"""
        if not results:
            return
        
        print(f"\n{'='*80}")
        print(f"{'策略名称':<25} {'总收益':<10} {'年化收益':<10} {'夏普比率':<10} {'最大回撤':<10} {'胜率':<10}")
        print(f"{'='*80}")
        
        for result in results:
            perf = result['performance']
            print(f"{result['strategy_name']:<25} "
                  f"{result['total_return']*100:>8.1f}% "
                  f"{perf.get('annualized_return', 0)*100:>8.1f}% "
                  f"{perf.get('sharpe_ratio', 0):>8.2f} "
                  f"{perf.get('max_drawdown', 0)*100:>8.1f}% "
                  f"{perf.get('win_rate', 0)*100:>8.1f}%")
        
        # 找出最佳策略
        best_return = max(results, key=lambda x: x['total_return'])
        best_sharpe = max(results, key=lambda x: x['performance'].get('sharpe_ratio', 0))
        
        print(f"\n🏆 最佳收益策略: {best_return['strategy_name']} ({best_return['total_return']*100:.2f}%)")
        print(f"🏆 最佳风险调整收益策略: {best_sharpe['strategy_name']} (夏普比率: {best_sharpe['performance'].get('sharpe_ratio', 0):.3f})")
    
    def plot_strategy_comparison(self, results):
        """绘制策略对比图"""
        if not results:
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('比特币交易策略对比分析', fontsize=16)
        
        # 1. 收益率对比
        strategies = [r['strategy_name'] for r in results]
        returns = [r['total_return']*100 for r in results]
        
        bars1 = ax1.bar(strategies, returns, color=['blue', 'green', 'red', 'orange', 'purple'][:len(strategies)])
        ax1.set_title('总收益率对比')
        ax1.set_ylabel('收益率 (%)')
        ax1.tick_params(axis='x', rotation=45)
        
        # 添加数值标签
        for bar, return_val in zip(bars1, returns):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{return_val:.1f}%', ha='center', va='bottom')
        
        # 2. 夏普比率对比
        sharpe_ratios = [r['performance'].get('sharpe_ratio', 0) for r in results]
        bars2 = ax2.bar(strategies, sharpe_ratios, color=['lightblue', 'lightgreen', 'lightcoral', 'moccasin', 'plum'][:len(strategies)])
        ax2.set_title('夏普比率对比')
        ax2.set_ylabel('夏普比率')
        ax2.tick_params(axis='x', rotation=45)
        
        for bar, sharpe in zip(bars2, sharpe_ratios):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{sharpe:.2f}', ha='center', va='bottom')
        
        # 3. 最大回撤对比
        max_drawdowns = [abs(r['performance'].get('max_drawdown', 0))*100 for r in results]
        bars3 = ax3.bar(strategies, max_drawdowns, color=['salmon', 'lightcyan', 'wheat', 'lightpink', 'lightgray'][:len(strategies)])
        ax3.set_title('最大回撤对比')
        ax3.set_ylabel('最大回撤 (%)')
        ax3.tick_params(axis='x', rotation=45)
        
        for bar, drawdown in zip(bars3, max_drawdowns):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                    f'{drawdown:.1f}%', ha='center', va='bottom')
        
        # 4. 净值曲线对比
        for i, result in enumerate(results):
            perf = result['performance']
            if 'daily_data' in perf and not perf['daily_data'].empty:
                df = perf['daily_data']
                df['normalized_value'] = df['value'] / df['value'].iloc[0]
                ax4.plot(df['date'], df['normalized_value'], 
                        label=result['strategy_name'], linewidth=2)
        
        ax4.set_title('净值曲线对比')
        ax4.set_ylabel('净值(标准化)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # 保存图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plt.savefig(f'btc_strategy_comparison_{timestamp}.png', dpi=300, bbox_inches='tight')
        print(f"\n📈 图表已保存: btc_strategy_comparison_{timestamp}.png")


def main():
    """主函数 - 运行策略回测"""
    
    # 创建回测器
    backtest = BTCStrategyBacktester(initial_cash=10000, commission=0.001)
    
    # 定义策略配置
    strategies_config = [
        {
            'strategy': RSIMeanReversionStrategy,
            'params': {'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70}
        },
        {
            'strategy': MACDMomentumStrategy,
            'params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}
        },
        {
            'strategy': AdvancedMACDStrategy,
            'params': {'fast_period': 12, 'slow_period': 26, 'rsi_period': 14}
        },
        {
            'strategy': BollingerBandsStrategy,
            'params': {'bb_period': 20, 'bb_dev': 2.0, 'strategy_type': 'breakout'}
        },
        {
            'strategy': BTCGridTradingStrategy,
            'params': {'grid_spacing': 500, 'grid_levels': 8, 'base_order_size': 0.01}
        }
    ]
    
    # 运行策略对比
    results = backtest.run_strategy_comparison(
        strategies_config,
        start_date="2022-01-01",
        end_date="2023-12-31"
    )
    
    return results


if __name__ == "__main__":
    results = main()