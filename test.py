import pandas as pd
pd.options.mode.copy_on_write = True
import yfinance as yf
import matplotlib.pyplot as plt

# 获取贵州茅台股票数据
symbol = "600519.SS"
start_date = "2023-05-01"
end_date = "2025-04-01"

data = yf.download(symbol, start=start_date, end=end_date)

# 计算短期（50天）和长期（200天）移动平均
day1 = 5
day2 = 20
name1 = "MA_{}".format(day1)
name2 = "MA_{}".format(day2)

data[name1] = data['Close'].rolling(window=day1).mean()
data[name2] = data['Close'].rolling(window=day2).mean()

# 生成买卖信号
data['Signal'] = 0
data.loc[data[name1] > data[name2], 'Signal'] = -1  # 短期均线上穿长期均线，产生买入信号
data.loc[data[name1] < data[name2], 'Signal'] = 1  # 短期均线下穿长期均线，产生卖出信号
print(data)
# 绘制股价和移动平均线
plt.figure(figsize=(30, 18))
plt.plot(data['Close'], label='Close Price')
plt.plot(data[name1], label='{}-day Moving Average'.format(day1))
plt.plot(data[name2], label='{}-day Moving Average'.format(day2))

# 标记买卖信号
plt.scatter(data[data['Signal'] == 1].index, data[data['Signal'] == 1][name1], marker='^', color='g', label='Buy Signal')
plt.scatter(data[data['Signal'] == -1].index, data[data['Signal'] == -1][name1], marker='v', color='r', label='Sell Signal')

plt.title("Maotai Stock Price with Moving Averages")
plt.xlabel("Date")
plt.ylabel("Price (CNY)")
plt.legend()
plt.show()