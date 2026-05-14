import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time

def fetch_qdii_daily():
    """
    获取QDII相关品种的日线收盘价（近60个自然日）
    - 时间统一转为北京时间
    - 只保留 Close 列
    - 输出到 output/qdii_daily_{date}.csv
    """
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
        "hf_CL": "CL=F",
        "hf_OIL": "BZ=F",
        "hf_GC": "GC=F",
        "hf_SI": "SI=F"
    }

    os.makedirs("output", exist_ok=True)
    bj_now = datetime.now(pytz.timezone('Asia/Shanghai'))
    date_str = bj_now.strftime("%Y%m%d")
    output_file = os.path.join("output", f"qdii_daily_{date_str}.csv")

    # 近60个自然日
    end_date = bj_now
    start_date = end_date - timedelta(days=60)
    print(f"[{bj_now.strftime('%Y-%m-%d %H:%M:%S')} BJ] Fetching daily data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} (Beijing time)")
    print(f"[{bj_now.strftime('%Y-%m-%d %H:%M:%S')} BJ] Output: {output_file}")

    new_data_list = []
    success_count = 0

    for name, symbol in tickers.items():
        print(f"  Fetching {name} ({symbol})...", end=" ", flush=True)
        try:
            ticker = yf.Ticker(symbol)
            # 日线收盘价
            df = ticker.history(start=start_date, end=end_date, interval="1d")

            if df.empty:
                print("no data")
                continue

            # 只保留 Close 列
            df = df[['Close']].copy()
            # 统一转为北京时间
            df.index = df.index.tz_convert('Asia/Shanghai')
            df.index.name = 'Datetime'
            df.columns = [name]

            new_data_list.append(df)
            print(f"OK ({len(df)} rows)")
            success_count += 1

            # 速率保护
            time.sleep(0.5)

        except Exception as e:
            print(f"Error: {e}")

    if not new_data_list:
        print("[ERROR] All tickers failed. Check network or yfinance status.")
        return

    # 合并所有品种
    combined = pd.concat(new_data_list, axis=1)
    # 按时间升序排列（从旧到新）
    combined = combined.sort_index(ascending=True)
    # 时区标注为北京时间
    combined.index = combined.index.strftime('%Y-%m-%d %H:%M:%S+08:00')
    combined.index.name = 'Datetime'

    # 保存
    combined.to_csv(output_file)
    print(f"\n--- Done ---")
    print(f"Saved to: {output_file}")
    print(f"Date range: {combined.index[0]} ~ {combined.index[-1]}")
    print(f"Total rows: {len(combined)}")
    print(f"Total tickers: {len(combined.columns)}")
    print(f"Tickers with data: {success_count}/{len(tickers)}")


if __name__ == "__main__":
    fetch_qdii_daily()
