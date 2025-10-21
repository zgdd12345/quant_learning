#!/usr/bin/env python3
"""
测试下载2025年比特币数据并进行初步分析
"""

from btc_data import BTCDataFeed
from datetime import datetime
import pandas as pd

def download_2025_data():
    print('🔄 正在下载2025年比特币数据...')
    btc_feed = BTCDataFeed()
    
    # 获取2025年数据
    data_2025 = btc_feed.fetch_data('2025-01-01', '2025-12-31')
    
    if data_2025 is not None and not data_2025.empty:
        print(f'✅ 成功获取数据: {len(data_2025)} 条记录')
        print(f'📅 数据范围: {data_2025.index[0].strftime("%Y-%m-%d")} 到 {data_2025.index[-1].strftime("%Y-%m-%d")}')
        min_price = float(data_2025["Close"].min())
        max_price = float(data_2025["Close"].max())
        current_price = float(data_2025["Close"].iloc[-1])
        start_price = float(data_2025["Close"].iloc[0])
        
        print(f'💰 价格范围: ${min_price:.2f} - ${max_price:.2f}')
        print(f'📊 当前价格: ${current_price:.2f}')
        print(f'📈 2025年收益率: {((current_price / start_price) - 1) * 100:.2f}%')
        avg_volume = float(data_2025["Volume"].mean())
        print(f'📦 平均日交易量: {avg_volume:.0f}')
        
        # 计算波动性
        daily_returns = data_2025['Close'].pct_change().dropna()
        volatility = float(daily_returns.std() * (252 ** 0.5))  # 年化波动率
        print(f'📉 年化波动率: {volatility * 100:.2f}%')
        
        # 保存数据
        data_2025.to_csv('btc_2025_data.csv')
        print('💾 数据已保存到 btc_2025_data.csv')
        
        return data_2025
    else:
        print('❌ 无法获取2025年数据，可能数据还不完整')
        return None

if __name__ == "__main__":
    data = download_2025_data()