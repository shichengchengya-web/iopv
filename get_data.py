import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

def fetch_qdii_daily():
    """
    获取QDII ETF及对应期货日线数据
    - 统一使用 interval="1d"
    - 4个核心期货：WTI(CL=F), 布油(BZ=F), 黄金(GC=F), 白银(SI=F)
    - 自动通过 ffill() 实现 ETF 收盘时刻的期货锚点对齐
    """
    tickers = {
        # ETF 部分
        "CRUD.L": "CRUD.L",
        "BRNT.L": "BRNT.L",
        "DBO": "DBO",
        "BNO": "BNO",
        "USO": "USO",
        "3175.HK": "3175.HK",
        "IAU": "IAU",
        "GLD": "GLD",
        "AAAU": "AAAU",
        "SGOL": "SGOL",
        "FTGC": "FTGC",
        "BCD": "BCD",
        "SLV": "SLV",
        # 期货部分 (用于锚点对齐)
        "hf_CL": "CL=F",   # WTI原油期货
        "hf_OIL": "BZ=F",  # 布伦特原油期货
        "hf_GC": "GC=F",   # 黄金期货
        "hf_SI": "SI=F"    # 白银期货
    }

    os.makedirs("output", exist_ok=True)
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_now = datetime.now(bj_tz)
    # 抓取近60天数据
    end_date = bj_now
    start_date = end_date - timedelta(days=60)
    
    print(f"[{bj_now.strftime('%Y-%m-%d %H:%M:%S')}] Fetching ETF and Futures (1d)...")

    new_data_list = []
    
    for name, symbol in tickers.items():
        print(f"  Fetching {name}...", end=" ", flush=True)
        try:
            ticker = yf.Ticker(symbol)
            # 统一使用日线
            df = ticker.history(start=start_date, end=end_date, interval="1d")

            if df.empty:
                print("no data")
                continue

            df = df[['Close']].copy()
            # 统一转为北京时间
            df.index = df.index.tz_convert('Asia/Shanghai')
            df.columns = [name]
            new_data_list.append(df)
            print(f"OK")
            
            # 保护性延迟
            time.sleep(random.uniform(1.0, 2.0))

        except Exception as e:
            print(f"Error: {e}")

    if not new_data_list:
        return

    # 合并数据
    combined = pd.concat(new_data_list, axis=1)
    
    # 【核心逻辑】按时间排序并向下填充
    # 这会确保某天如果只有期货有值、ETF没值（休市），ETF会沿用前一天价格
    # 反之，某时刻ETF收盘的价格会与当时已知的最新期货价格对齐在同一行
    combined = combined.sort_index(ascending=True).ffill()
    
    # 格式化日期戳
    combined.index = combined.index.strftime('%Y-%m-%d %H:%M:%S+08:00')
    combined.index.name = 'Datetime'

    # 仅输出一个固定名称的最新文件，保持仓库整洁
    output_file = os.path.join("output", "qdii_daily_latest.csv")
    combined.to_csv(output_file)
    
    print(f"\n--- Done ---")
    print(f"File saved to: {output_file}")

if __name__ == "__main__":
    fetch_qdii_daily()
