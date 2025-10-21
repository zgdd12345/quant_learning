import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import backtrader as bt

class BTCDataFeed:
    """Bitcoin data fetching and management"""
    
    def __init__(self):
        self.symbol = "BTC-USD"
    
    def fetch_data(self, start_date="2020-01-01", end_date=None, interval="1d"):
        """
        获取比特币历史数据
        
        参数:
        - start_date: 开始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)，默认为今天
        - interval: 时间间隔 (1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo)
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            data = yf.download(self.symbol, start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                raise ValueError(f"无法获取 {self.symbol} 在 {start_date} 到 {end_date} 期间的数据")
            
            # 确保数据格式正确
            data = data.dropna()
            
            # 添加技术指标所需的基础数据
            data['Returns'] = data['Close'].pct_change()
            data['Volume_MA'] = data['Volume'].rolling(window=20).mean()
            
            print(f"成功获取 {len(data)} 条 {self.symbol} 数据记录")
            print(f"数据范围: {data.index[0]} 到 {data.index[-1]}")
            
            return data
            
        except Exception as e:
            print(f"数据获取失败: {e}")
            return None
    
    def get_backtrader_data(self, start_date="2020-01-01", end_date=None):
        """
        获取用于Backtrader的数据格式
        """
        data = self.fetch_data(start_date, end_date)
        if data is None:
            return None, None
        
        # 确保列名正确
        if data.columns.nlevels > 1:
            data.columns = data.columns.droplevel(1)
        
        # 重置索引确保datetime作为列
        data_reset = data.reset_index()
        
        # 创建Backtrader数据源
        bt_data = bt.feeds.PandasData(
            dataname=data_reset,
            datetime='Date',
            open='Open',
            high='High',
            low='Low',
            close='Close',
            volume='Volume',
            openinterest=-1
        )
        
        return bt_data, data

if __name__ == "__main__":
    # 测试数据获取
    btc_feed = BTCDataFeed()
    data = btc_feed.fetch_data("2023-01-01", "2024-01-01")
    if data is not None:
        print("\n数据预览:")
        print(data.head())
        print("\n数据统计:")
        print(data.describe())