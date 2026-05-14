import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

def fetch_qdii_daily():
    tickers = {
        "CRUD.L": "CRUD.L", "BRNT.L": "BRNT.L",
        "DBO": "DBO", "BNO": "BNO", "USO": "USO",
        "IAU": "IAU", "GLD": "GLD", "AAAU": "AAAU",
        "SGOL": "SGOL", "FTGC": "FTGC", "BCD": "BCD", "SLV": "SLV",
        "hf_CL": "CL=F", "hf_OIL": "BZ=F", "hf_GC": "GC=F", "hf_SI": "SI=F"
    }

    os.makedirs("output", exist_ok=True)
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_now = datetime.now(bj_tz)
    output_file = os.path.join("output", "qdii_daily_latest.csv")

    end_date = bj_now
    start_date = end_date - timedelta(days=60)

    new_data_list = []
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1d")
            if df.empty: continue
            df = df[['Close']].copy()
            df.index = df.index.tz_convert('Asia/Shanghai').normalize()
            df.columns = [name]
            new_data_list.append(df)
            time.sleep(random.uniform(0.5, 1.0))
        except Exception: pass

    if not new_data_list: return

    combined = pd.concat(new_data_list, axis=1)
    combined = combined.sort_index(ascending=True).ffill()
    combined.index = combined.index.strftime('%Y-%m-%d 00:00:00+08:00')
    combined.index.name = 'Datetime'
    combined.to_csv(output_file)
    print("Done. Output: output/qdii_daily_latest.csv")

if __name__ == "__main__":
    fetch_qdii_daily()