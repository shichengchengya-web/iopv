import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

def fetch_qdii_daily():
    """
    精简版：仅抓取伦敦/纽约海外锚点数据
    - 移除 3175.HK (由实时接口处理)
    - 4个核心期货 + 对应海外 ETF
    """
    tickers = {
        # 伦敦市场 (LSE)
        "CRUD.L": "CRUD.L",
        "BRNT.L": "BRNT.L",
        # 纽约市场 (NYSE)
        "DBO": "DBO",
        "BNO": "BNO",
        "USO": "USO",
        "IAU": "IAU",
        "GLD": "GLD",
        "AAAU": "AAAU",
        "SGOL": "SGOL",
        "FTGC": "FTGC",
        "BCD": "BCD",
        "SLV": "SLV",
        # 香港交易所
        "3175.HK": "3175.HK",        
        # 期货锚点 (用于计算实时偏移)
        "hf_CL": "CL=F",
        "hf_OIL": "BZ=F",
        "hf_GC": "GC=F",
        "hf_SI": "SI=F"
    }

    os.makedirs("output", exist_ok=True)
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_now = datetime.now(bj_tz)
    
    # 抓取近60天数据
    end_date = bj_now
    start_date = end_date - timedelta(days=60)
    
    print(f"[{bj_now.strftime('%Y-%m-%d %H:%M:%S')}] Fetching Overseas Anchors (LSE & NYSE)...")

    new_data_list = []
    for name, symbol in tickers.items():
        print(f"  Fetching {name}...", end=" ", flush=True)
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1d")
            if df.empty:
                print("no data")
                continue
            df = df[['Close']].copy()
            df.index = df.index.tz_convert('Asia/Shanghai')
            df.columns = [name]
            new_data_list.append(df)
            print(f"OK")
            time.sleep(random.uniform(1.0, 2.0))
        except Exception as e:
            print(f"Error: {e}")

    if not new_data_list:
        return

    # 合并、排序并向下填充空格
    combined = pd.concat(new_data_list, axis=1)
    combined = combined.sort_index(ascending=True).ffill()
    
    # 格式化日期戳
    combined.index = combined.index.strftime('%Y-%m-%d %H:%M:%S+08:00')
    combined.index.name = 'Datetime'

    # 输出最新文件
    output_file = os.path.join("output", "qdii_daily_latest.csv")
    combined.to_csv(output_file)
    
    print(f"\n--- Done ---")
    print(f"Clean overseas data saved to: {output_file}")

if __name__ == "__main__":
    fetch_qdii_daily()
