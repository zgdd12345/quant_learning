import os
import datetime
import pytz
import pandas as pd
import ccxt
import click
import time  # Add this import for retry delays

from dateutil.relativedelta import relativedelta
from pathlib import Path

exchange = ccxt.binance(
    {
        "enableRateLimit": True, # 必须开启！防止被交易所封IP
        "timeout":15000, # 超时设为15秒
        'proxies': {
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
            }
        # "proxies": {
        #     "http": os.getenv("http_proxy"),
        #     "https": os.getenv("https_proxy"),
        #     }
    }
)

def download(symbol: str, start=None, end=None, timeframe="1d", save_dir="."):
    if end is None:
        end = datetime.datetime.now(pytz.UTC)
    else:
        end = end.replace(tzinfo=pytz.UTC)
    if start is None:
        start = end - relativedelta(years=3)
    else:
        start = start.replace(tzinfo=pytz.UTC)

    max_limit = 1000
    since = start.timestamp()
    end_time = int(end.timestamp() * 1e3)

    # Create save directory if it doesn't exist
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    absolute_path = os.path.join(save_dir, f"{symbol.replace('/', '-')}_{str(start)[:10]}_{str(end)[:10]}_{timeframe}.csv")

    ohlcvs = []
    while True:
        try:
            new_ohlcvs = exchange.fetch_ohlcv(
                symbol,
                since=int(since * 1e3),
                timeframe=timeframe,
                limit=max_limit,
                params={"endTime": end_time},
            )
            if len(new_ohlcvs) == 0:
                break
            ohlcvs += new_ohlcvs
            since = ohlcvs[-1][0] / 1e3 + 1
            print(f"下载进度：{datetime.datetime.fromtimestamp(ohlcvs[-1][0] / 1e3)}\r", end="")
        except ccxt.RequestTimeout:
            print("Request timed out. Retrying in 5 seconds...")
            time.sleep(5)  # Wait before retrying
            continue
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    print()

    data = pd.DataFrame(ohlcvs, columns=["timestamp_ms", "open", "high", "low", "close", "volume"])
    data.drop_duplicates(inplace=True)
    data.set_index(pd.DatetimeIndex(pd.to_datetime(data["timestamp_ms"], unit="ms", utc=True)), inplace=True)
    data.index.name = "datetime"
    del data["timestamp_ms"]
    data.to_csv(absolute_path)
    print(f"Data saved to: {absolute_path}")


def fetch_historical_data(symbol, start, end, multifile, timeframe, save_dir):
    """
    Download OHLCV data from Binance
    
    
    """


    download(symbol=symbol, start=start, end=end, timeframe=timeframe, save_dir=save_dir)


@click.command()
@click.option("--symbol", required=True, help="Trading symbol (e.g. BTC/USDT)")
@click.option("--start",type=click.DateTime(), help="Start date (YYYY-MM-DD)")
@click.option("--end", type=click.DateTime(),help="End date (YYYY-MM-DD)")
@click.option("--timeframe", default="1d", help="Timeframe for OHLCV data (1m, 5m, 15m, 1h, 1d, etc.)")
@click.option("--save-dir", default=".", help="Directory to save the CSV file")
def main(symbol, start, end, timeframe, save_dir):
    """Download OHLCV data from Binance"""
    download(symbol=symbol, start=start, end=end, timeframe=timeframe, save_dir=save_dir)



# if __name__ == "__main__":
#     # exchange = ccxt.binance({'enableRateLimit': True})
#     start_time = exchange.parse8601('2025-03-12T00:00:00Z')  # 调整起始日期
#     end_time = exchange.parse8601('2025-04-12T00:00:00Z')
#     all_data = []

#     while start_time < end_time:
#         ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1m', since=start_time, limit=1000)
#         if not ohlcv: break
#         all_data.extend(ohlcv)
#         start_time = ohlcv[-1][0] + 1  # 更新起始时间戳

#     df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
#     df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

if __name__ == "__main__":
    time_list = [(2023, 4, 12), (2023, 4, 12), (2023, 4, 12), (2023, 4, 12), (2023, 4, 12)]
    for tup in [('2023-04-12', '2025-04-12'), ]:
        main()

#  python data.py --symbol BTC/USDT --start 2023-04-12 --end 2025-04-12 --timeframe 1m --save-dir ./data