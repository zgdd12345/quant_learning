import os, datetime, pytz, time
import pandas as pd
import ccxt
import click

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

    # absolute_path = os.path.join(save_dir, f"{symbol.replace('/', '-')}_{str(start)[:10]}_{str(end)[:10]}_{timeframe}.csv")
    absolute_path = os.path.join(save_dir, f"{str(start)[:10]}_{str(end)[:10]}_{timeframe}.csv")

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


def fetch_historical_data(symbol, start, end, interval='y', timeframe='1d', save_dir='.'):
    """
    Download OHLCV data from Binance
    
    """
    if interval == 'y':
        save_dir = os.path.join(save_dir, symbol.replace('/', ''), 'years') + "_" + timeframe
    elif interval == 'm':
        save_dir = os.path.join(save_dir, symbol.replace('/', ''), 'months') + "_" + timeframe
    elif interval == 'w':
        save_dir = os.path.join(save_dir, symbol.replace('/', ''), 'weeks') + "_" + timeframe
    elif interval == 'd':
        save_dir = os.path.join(save_dir, symbol.replace('/', ''), 'days') + "_" + timeframe
    else:
        assert False, "The interval must be one of 'y', 'm', 'w', 'd'"

    start = datetime.datetime.strptime(start, '%Y-%m-%d')
    end = datetime.datetime.strptime(end, '%Y-%m-%d')
    current = start
    while current < end:
        if interval == 'y':
            added_date = relativedelta(years=1)
        elif interval == 'm':
            added_date = relativedelta(months=1)
        elif interval == 'w':
            added_date = relativedelta(weeks=1)
        elif interval == 'd':
            added_date = relativedelta(days=1)

        download(symbol=symbol, start=current, end=current + added_date, timeframe=timeframe, save_dir=save_dir)
        current += added_date



def convert_to_zipline_format(path, save_dir, symbol, timeframe="1m", interval="d"):
    if timeframe == "1m":
        timeframe_dir = "minute"
    elif timeframe == "1h":
        timeframe_dir = "hour"
    elif timeframe == "1d":
        timeframe_dir = "daily"

    for csv_name in os.listdir(path):
        df = pd.read_csv(os.path.join(path, csv_name), index_col=0, parse_dates=True)
        df = df.sort_index()
        df = df.ffill()
        date = csv_name[:10]

        save_path = os.path.join(save_dir, timeframe_dir, date)
        if not  os.path.exists(save_path):
            os.makedirs(os.path.join(save_dir, timeframe_dir, date))

        out_file = os.path.join(save_path, symbol + '.csv')
        print(out_file, '\r',end="")
        print()
        df.to_csv(out_file)


@click.command()
@click.option("--symbol", required=True, help="Trading symbol (e.g. BTC/USDT)")
@click.option("--start",type=click.DateTime(), help="Start date (YYYY-MM-DD)")
@click.option("--end", type=click.DateTime(),help="End date (YYYY-MM-DD)")
@click.option("--timeframe", default="1d", help="Timeframe for OHLCV data (1m, 5m, 15m, 1h, 1d, etc.)")
@click.option("--save-dir", default=".", help="Directory to save the CSV file")
def main(symbol, start, end, timeframe, save_dir):
    """Download OHLCV data from Binance"""
    download(symbol=symbol, start=start, end=end, timeframe=timeframe, save_dir=save_dir)

if __name__ == "__main__":
    # main()
    
    # fetch_historical_data(symbol="BTC/USDT", start="2017-08-01", end="2025-05-01", interval='d', timeframe='1m', save_dir='./data')

    convert_to_zipline_format('./data/BTCUSDT/days_1m', './data/BTCUSDT/', 'BTC_USDT', timeframe='1m', interval='d')


#  python data.py --symbol BTC/USDT --start 2023-04-12 --end 2025-04-12 --timeframe 1m --save-dir ./data