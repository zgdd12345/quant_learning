import pandas as pd
import  backtrader as bt
from datetime import datetime

from strategy.strategy import MyStrategy
from strategy.grid import GridTradingStrategyBase


if __name__ == '__main__':

    test_strategy = GridTradingStrategyBase

    df = pd.read_csv('./data/BTC-USDT_1m.csv')
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)  # 自动识别时区并转为UTC
    df.set_index('datetime', inplace=True)

    start_date = datetime(2025, 3, 12, 00, 00, 00)  # 回测开始时间
    end_date = datetime(2025, 4, 13, 00, 00, 00)  # 回测结束时间

    data = bt.feeds.PandasData(dataname=df, fromdate=start_date, todate=end_date, timeframe=bt.TimeFrame.Minutes)

    cerebro = bt.Cerebro() # 实例化 创建了一个机器人大脑（Cerebro），同时隐含创建了一个borker（券商）。

    cerebro.adddata(data) # 添加数据
    cerebro.broker.setcash(1000) # set init cash
    cerebro.broker.setcommission(0.00075) # 设置佣金， 根据交易成本设置
    cerebro.addsizer(bt.sizers.FixedSize, stake=0.002) # 设置每次买多少股票

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # cerebro.addstrategy(test_strategy, myparam=20, exitbars=7) # 自定义策略
    cerebro.addstrategy(GridTradingStrategyBase,
                       grid_space=5,
                       volume_per_layer=0.002,
                       max_layers=5)
    cerebro.run() # 运行 让机器人大脑开始运行。
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    cerebro.plot()

