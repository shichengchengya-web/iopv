# get_market_close_prices_final.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os

def is_us_summer_time(dt):
    """判断是否为美国夏令时（简单版）"""
    return 3 < dt.month < 11

def fetch_market_close_prices():
    """
    按各市场真实收盘时间提取价格（用于 T-1 净值计算）
    """
    tickers_config = {
        # 伦敦 LSE ≈ 北京时间 00:30
        "CRUD.L": {"symbol": "CRUD.L", "market": "London",  "close_time": "00:30"},
        "BRNT.L": {"symbol": "BRNT.L", "market": "London",  "close_time": "00:30"},
        
        # 纽约 NYSE
        "DBO":    {"symbol": "DBO",    "market": "NewYork", "close_time": "04:00"},  # 夏令时
        "BNO":    {"symbol": "BNO",    "market": "NewYork", "close_time": "04:00"},
        "USO":    {"symbol": "USO",    "market": "NewYork", "close_time": "04:00"},
        
        # 香港/首尔
        "3175.HK":{"symbol": "3175.HK","market": "Seoul",   "close_time": "14:30"},
    }

    os.makedirs("output", exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = f"output/qdii_market_close_{date_str}.csv"

    print("开始获取各市场收盘价...\n")

    results = []
    for name, cfg in tickers_config.items():
        symbol = cfg["symbol"]
        market = cfg["market"]
        close_time = cfg["close_time"]
        
        print(f"  → {name:8} ({market}) ", end="")
        
        try:
            # 下载日线
            df = yf.download(
                symbol,
                period="60d",
                interval="1d",
                auto_adjust=True,
                progress=False
            )
            
            if df.empty:
                print("× 无数据")
                continue

            df = df[['Close']].copy()
            
            # 转为北京时间
            if df.index.tz is None:
                df.index = pd.to_datetime(df.index).tz_localize('UTC')
            df.index = df.index.tz_convert('Asia/Shanghai')

            # 提取最近一天对应收盘时间的价格
            latest_date = df.index.max().date()
            
            # 纽约夏令时切换
            if market == "NewYork":
                hour = 4 if is_us_summer_time(latest_date) else 5
                target
