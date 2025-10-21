import pandas as pd
pd.options.mode.copy_on_write = True
import yfinance as yf
import matplotlib.pyplot as plt


class Test:
    def __init__(self, config):
        self.config = config
        
        # symbol = config['symbol']
        # start_date = config['start_date']
        # end_date = config['end_date']

        self.data: pd.DataFrame = yf.download(config['symbol'], start=config['start_date'], end=config['end_date']) # type: ignore
        if self.data is None or self.data.empty:
            raise ValueError("下载数据失败，请检查股票代码和网络连接")

    def run(self):
        self.mean_average_strategy()

        pass

    def mean_average_strategy(self):        
        day1 = self.config['long']
        day2 = self.config['short']
        name1 = "MA_{}".format(day1)
        name2 = "MA_{}".format(day2)

        self.data[name1] = self.data['Close'].rolling(window=day1).mean()
        self.data[name2] = self.data['Close'].rolling(window=day2).mean()

        # 生成买卖信号
        self.data['Signal'] = 0
        self.data.loc[self.data[name1] > self.data[name2], 'Signal'] = -1  # 短期均线上穿长期均线，产生买入信号
        self.data.loc[self.data[name1] < self.data[name2], 'Signal'] = 1  # 短期均线下穿长期均线，产生卖出信号

        self.draw(name1, name2, day1, day2)


    def backtest(self):
        pass

    
    def draw(self, name1, name2, day1, day2, figsize=(15, 9)):
        # 绘制股价和移动平均线
        plt.figure(figsize=figsize)
        plt.plot(self.data['Close'], label='Close Price')
        plt.plot(self.data[name1], label='{}-day Moving Average'.format(day1))
        plt.plot(self.data[name2], label='{}-day Moving Average'.format(day2))

        # 标记买卖信号
        plt.scatter(self.data[self.data['Signal'] == 1].index, self.data[self.data['Signal'] == 1][name1], marker='^', color='g', label='Buy Signal')
        plt.scatter(self.data[self.data['Signal'] == -1].index, self.data[self.data['Signal'] == -1][name1], marker='v', color='r', label='Sell Signal')

        plt.title("{} Stock Price with Moving Averages".format(self.config['stock_name']))
        plt.xlabel("Date")
        plt.ylabel("Price (CNY)")
        plt.legend()
        plt.show()


if __name__ =="__main__":
    config = {
        'name':'Moving Average',
        'long':50,
        'short':10,

        'stock_name':'Bitcoin',
        'symbol': "BTC-USD",
        'start_date':"2020-01-01",
        'end_date':"2024-01-01",

    }

    Test(config).run()

    # set QUANDL_API_KEY=JxAk9PxnUUfSqh6swgev