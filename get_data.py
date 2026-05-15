import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

# 鈹€鈹€鈹€ 甯傚満鏀剁洏鏃堕棿瀹氫箟 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# 鐢?datetime 瀵硅薄鏂逛究缁勫悎锛歜ase_date + 鏃跺埢
# HK  16:00 鍖椾含鏃堕棿 = 褰撳ぉ
# LSE 00:30 鍖椾含鏃堕棿 = 娆℃棩
# NY  04:00 鍐护鏃?/ 05:00 澶忎护鏃?= 娆℃棩

HK_HOUR, HK_MIN  = 16, 0
LSE_HOUR, LSE_MIN = 0, 30
NY_HOUR_WINTER, NY_MIN = 4, 0
NY_HOUR_SUMMER, _   = 5, 0


def ny_close_time(bj_date: datetime) -> datetime:
    """鏍规嵁鏃ユ湡杩斿洖绾界害鏀剁洏鐨勫寳浜椂闂?""
    # 鍖椾含鏃堕棿 -13h = 绾界害鏃堕棿
    ny_dt = bj_date - timedelta(hours=13)
    # 鍒ゆ柇璇?NY 鏃ユ湡鏄惁鍦?DST 鍐?    # 缇庡浗 DST: 3鏈堢浜屼釜鍛ㄦ棩 ~ 11鏈堢涓€涓懆鏃?    year = ny_dt.year
    march_second_sunday = datetime(year, 3, 8) + timedelta(days=(6 - datetime(year, 3, 8).weekday()))
    november_first_sunday = datetime(year, 11, 1) + timedelta(days=(6 - datetime(year, 11, 1).weekday()))
    in_dst = march_second_sunday <= ny_dt < november_first_sunday
    h = NY_HOUR_SUMMER if in_dst else NY_HOUR_WINTER
    return bj_date.replace(hour=h, minute=0, second=0, microsecond=0)


def hk_close_time(bj_date: datetime) -> datetime:
    return bj_date.replace(hour=HK_HOUR, minute=HK_MIN, second=0, microsecond=0)


def lse_close_time(bj_date: datetime) -> datetime:
    return (bj_date + timedelta(days=1)).replace(hour=LSE_HOUR, minute=LSE_MIN, second=0, microsecond=0)


def nearest_price(df_30m: pd.DataFrame, target_bj: datetime) -> float:
    """鍦?30min 鏁版嵁涓壘鍒版渶鎺ヨ繎 target_bj 鐨勬敹鐩樹环"""
    if df_30m.empty:
        return None
    df_30m = df_30m.tz_convert('Asia/Shanghai').sort_index()
    diffs = (df_30m.index - target_bj).total_seconds().abs()
    return float(df_30m.loc[diffs.idxmin(), 'Close'])


def nearest_1d(df_1d: pd.Series, target_bj: datetime) -> float:
    """鍦ㄦ棩绾挎暟鎹腑鎵惧埌鏈€鎺ヨ繎 target_bj 鐨勬敹鐩樹环"""
    if df_1d.empty:
        return None
    s = df_1d.sort_index()
    diffs = (s.index - target_bj).total_seconds().abs()
    return float(s.loc[diffs.idxmin()])


def fetch_qdii_daily():
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_today = datetime.now(bj_tz)

    # 鈹€鈹€鈹€ 鏍囩殑鍒楄〃 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    etf_list = [
        "CRUD.L", "BRNT.L", "DBO", "BNO", "USO",
        "3175.HK", "IAU", "GLD", "AAAU", "SGOL", "FTGC", "BCD", "SLV"
    ]
    fut_list = ["CL=F", "BZ=F"]

    # 鈹€鈹€鈹€ 鏃ョ嚎锛氭渶杩?60 澶╃殑 ETF 鏁版嵁 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    end_dt   = bj_today
    start_dt = end_dt - timedelta(days=90)

    print(f"[{bj_today.strftime('%Y-%m-%d %H:%M:%S')}] Fetching ETF daily data...")
    etf_daily = {}
    for sym in etf_list:
        print(f"  {sym}...", end=" ", flush=True)
        try:
            df = yf.Ticker(sym).history(start=start_dt, end=end_dt, interval="1d")
            if df.empty:
                print("no data"); continue
            etf_daily[sym] = df['Close'].tz_convert('Asia/Shanghai')
            print(f"OK ({len(df)} rows)")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(random.uniform(1.5, 3.0))

    # 鈹€鈹€鈹€ 30min锛氳繎 7 澶╂湡璐ф暟鎹?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    print(f"\n[{bj_today.strftime('%Y-%m-%d %H:%M:%S')}] Fetching futures 30min data...")
    fut_30m = {}
    for sym in fut_list:
        print(f"  {sym}...", end=" ", flush=True)
        try:
            df = yf.Ticker(sym).history(period="7d", interval="30m")
            if df.empty:
                print("no data"); continue
            fut_30m[sym] = df['Close']
            print(f"OK ({len(df)} rows)")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(random.uniform(2.0, 4.0))

    if not etf_daily:
        print("Error: No ETF data fetched.")
        return

    # 鈹€鈹€鈹€ 鍙栨渶杩?60 涓叡鍚屼氦鏄撴棩 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    ref = list(etf_daily.values())[0]
    all_dates = sorted(set(ref.index.normalize().date))[-60:]

    # 鈹€鈹€鈹€ 鏋勫缓涓夎鏁版嵁 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    rows = []
    for bj_date in all_dates:
        bj_dt = datetime.combine(bj_date, datetime.min.time(), tzinfo=bj_tz)

        hk_bj  = hk_close_time(bj_dt)
        lse_bj = lse_close_time(bj_dt)
        ny_bj  = ny_close_time(bj_dt)

        # 姣忚: Date | ETFs... | CL=F | BZ=F
        for market, close_bj, ts_suffix in [
            ("HK",  hk_bj,  "16:00:00+08:00"),
            ("LSE", lse_bj, "00:30:00+08:00"),
            ("NY",  ny_bj,  "04:00:00+08:00"),
        ]:
            date_str = bj_dt.strftime("%Y-%m-%d")
            if market in ("LSE", "NY"):
                date_str = (bj_dt + timedelta(days=1)).strftime("%Y-%m-%d")

            row = {"Datetime": f"{date_str} {ts_suffix}"}

            for sym in etf_list:
                row[sym] = nearest_1d(etf_daily[sym], close_bj) if sym in etf_daily else None

            for sym in fut_list:
                if sym in fut_30m:
                    row[sym] = nearest_price(fut_30m[sym].to_frame('Close'), close_bj)
                else:
                    row[sym] = None

            rows.append(row)

    df_out = pd.DataFrame(rows)
    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", "qdii_daily_latest.csv")
    df_out.to_csv(out_path, index=False)
    print(f"\n--- Done ---")
    print(f"Saved: {out_path} ({len(df_out)} rows)")


if __name__ == "__main__":
    fetch_qdii_daily()