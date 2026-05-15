import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

# Market close times (Beijing timezone)
# HK:  16:00 same day
# LSE: 00:30 next day
# NY:  04:00 (winter) / 05:00 (summer) next day

HK_HOUR, HK_MIN  = 16, 0
LSE_HOUR, LSE_MIN = 0, 30
NY_HOUR_WINTER, NY_MIN = 4, 0
NY_HOUR_SUMMER, _   = 5, 0


def ny_close_time(bj_date: datetime) -> datetime:
    ny_dt = bj_date - timedelta(hours=13)
    year = ny_dt.year
    dst_start = datetime(year, 3, 8) + timedelta(days=(6 - datetime(year, 3, 8).weekday()))
    dst_end   = datetime(year, 11, 1) + timedelta(days=(6 - datetime(year, 11, 1).weekday()))
    ny_dt_naive = ny_dt.replace(tzinfo=None)
    in_dst = dst_start <= ny_dt_naive < dst_end
    h = NY_HOUR_SUMMER if in_dst else NY_HOUR_WINTER
    return bj_date.replace(hour=h, minute=0, second=0, microsecond=0)


def hk_close_time(bj_date: datetime) -> datetime:
    return bj_date.replace(hour=HK_HOUR, minute=HK_MIN, second=0, microsecond=0)


def lse_close_time(bj_date: datetime) -> datetime:
    return (bj_date + timedelta(days=1)).replace(hour=LSE_HOUR, minute=LSE_MIN, second=0, microsecond=0)


def nearest_price(df_series: pd.Series, target_bj: datetime) -> float:
    if df_series.empty:
        return None
    s = df_series.sort_index()
    diffs = (s.index - target_bj).total_seconds().abs()
    return float(s.loc[diffs.idxmin()])


def fetch_qdii_daily():
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_today = datetime.now(bj_tz)

    etf_list = [
        "CRUD.L", "BRNT.L", "DBO", "BNO", "USO",
        "3175.HK", "IAU", "GLD", "AAAU", "SGOL", "FTGC", "BCD", "SLV"
    ]
    fut_list = ["CL=F", "BZ=F"]

    end_dt = bj_today
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

    ref = list(etf_daily.values())[0]
    all_dates = sorted(set(ref.index.normalize().date))[-60:]

    rows = []
    for bj_date in all_dates:
        bj_dt = datetime.combine(bj_date, datetime.min.time(), tzinfo=bj_tz)

        hk_bj  = hk_close_time(bj_dt)
        lse_bj = lse_close_time(bj_dt)
        ny_bj  = ny_close_time(bj_dt)

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
                row[sym] = nearest_price(etf_daily[sym], close_bj) if sym in etf_daily else None

            for sym in fut_list:
                if sym in fut_30m:
                    row[sym] = nearest_price(fut_30m[sym], close_bj)
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