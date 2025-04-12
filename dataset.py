import requests

import ccxt
import pandas as pd


def fetch_historical_data(url, symbol, interval, start_time, end_time):
    all_data = []
    while start_time < end_time:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time,
            'limit': 1000
        }
        data = requests.get(url, params=params).json()
        if not data: break
        all_data.extend(data)
        start_time = data[-1][0] + 1  # 更新起始时间戳
    return pd.DataFrame(all_data)


# 初始化Binance交易所对象
exchange = ccxt.binance({
    'enableRateLimit': True,  # 必须开启，避免触发API频率限制
    'options': {'defaultType': 'spot'},  # 指定现货市场
    'proxies': {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890'
    }
})

# 获取BTC/USDT的实时行情
ticker = exchange.fetch_ticker('BTC/USDT')
print(f"最新价: {ticker['last']} USDT\n24小时最高价: {ticker['high']}\n24小时成交量: {ticker['quoteVolume']} USDT")




# if __name__ == '__main__':
#     url = 'https://api.binance.com/api/v3/klines'
#     symbol = 'BTCUSDT'
#     interval = '1s'

#     historical_BTC_data = fetch_historical_data(url, symbol, interval, 0, 1000)
#     print(historical_BTC_data)