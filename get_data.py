import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

def fetch_qdii_daily():
    """
    获取QDII日线收盘价 (1d)
    - 严格锁定日线 interval="1d"
    - 统一转为北京时间 (+08:00) 标注
    - 仅保留 Close 列
    """
    # 纯 ETF 列表（期货由你后续单独处理）
    tickers = {
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
    }

    os.makedirs("output", exist_ok=True)
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_now = datetime.now(bj_tz)
    date_str = bj_now.strftime("%Y%m%d")
    output_file = os.path.join("output", f"qdii_daily_{date_str}.csv")

    # 近60天日线
    end_date = bj_now
    start_date = end_date - timedelta(days=60)
    
    print(f"[{bj_now.strftime('%Y-%m-%d %H:%M:%S')}] Fetching Daily Close (interval='1d')...")

    new_data_list = []
    
    for name, symbol in tickers.items():
        print(f"  Fetching {name}...", end=" ", flush=True)
        try:
            ticker = yf.Ticker(symbol)
            # 严格使用 1d 频率
            df = ticker.history(start=start_date, end=end_date, interval="1d")

            if df.empty:
                print("no data")
                continue

            # 提取收盘价
            df = df[['Close']].copy()
            # 转换为北京时间
            df.index = df.index.tz_convert('Asia/Shanghai')
            df.columns = [name]
            
            new_data_list.append(df)
            print(f"OK ({len(df)} rows)")
            
            # 随机延迟，降低被封风险
            time.sleep(random.uniform(1.5, 3.0))

        except Exception as e:
            print(f"Error: {e}")

    if not new_data_list:
        print("Error: No data fetched.")
        return

    # 合并所有 ETF 数据
    combined = pd.concat(new_data_list, axis=1)
    
    # 按时间升序并填充缺失值（防止因两地市场休市日期不同导致的空行）
    combined = combined.sort_index(ascending=True).ffill()
    
    # 格式化索引：2026-05-13 00:00:00+08:00
    combined.index = combined.index.strftime('%Y-%m-%d %H:%M:%S+08:00')
    combined.index.name = 'Datetime'
    
    # 只保存一个固定名称的文件，实时程序永远只读这一个
    combined.to_csv(os.path.join("output", "qdii_daily_latest.csv"))
    
    print(f"\n--- Done ---")
    print(f"Daily Close saved to: output/qdii_daily_latest.csv")
    
    print(f"\n--- Done ---")
    print(f"Daily Close saved to: {output_file}")

if __name__ == "__main__":
    fetch_qdii_daily()
