import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 获取比特币数据
symbol = "BTC-USD"  # 比特币代码
start_date = "2020-01-01"
end_date = "2024-01-01"

data = yf.download(symbol, start=start_date, end=end_date)
if not isinstance(data, pd.DataFrame) or data.empty:
    raise ValueError("下载数据失败，或指定时间段内无数据。")
# 计算移动平均
data['SMA_50'] = data['Close'].rolling(window=50).mean() # type: ignore
data['SMA_200'] = data['Close'].rolling(window=200).mean() # type: ignore

# 初始化交叉信号列
data['Signal'] = 0 # type: ignore

# 计算交叉信号
data.loc[data['SMA_50'] > data['SMA_200'], 'Signal'] = 1
data.loc[data['SMA_50'] < data['SMA_200'], 'Signal'] = -1

# 计算每日收益率
data['Daily_Return'] = data['Close'].pct_change()

# 计算策略信号的收益率（shift(1) 是为了避免未来数据的偏差）
data['Strategy_Return'] = data['Signal'].shift(1) * data['Daily_Return']

# 计算累计收益
data['Cumulative_Return'] = (1 + data['Strategy_Return']).cumprod()

# 绘制累计收益曲线
plt.figure(figsize=(10, 6))
plt.plot(data['Cumulative_Return'], label='Strategy Cumulative Return', color='b')
plt.plot(data['Close'] / data['Close'].iloc[0], label='Stock Cumulative Return', color='g')
plt.title("Cumulative Return of Strategy vs. Stock")
plt.xlabel("Date")
plt.ylabel("Cumulative Return")
plt.legend()
plt.show()