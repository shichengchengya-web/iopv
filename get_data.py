import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

# Market close times in Beijing
HK_HOUR, HK_MIN = 16, 0
LSE_HOUR, LSE_MIN = 0, 30
NY_HOUR_WINTER = 4
NY_HOUR_SUMMER = 5

HK_TZ  = pytz.timezone('Asia/Hong_Kong')
BJ_TZ  = pytz.timezone('Asia/Shanghai')

ETF_LIST = [
    "CRUD.L", "BRNT.L", "DBO", "BNO", "USO",
    "3175.HK", "IAU", "GLD", "AAAU", "SGOL", "FTGC", "BCD", "SLV"
]
FUT_LIST = ["CL=F", "BZ=F"]

# Which ETF markets close when (in Beijing time on their trading day T)
ETF_MARKETS = {
    "HK":  ["3175.HK"],                          # HK stock
    "LSE": ["CRUD.L", "BRNT.L"],                # London stocks
    "NY":  ["DBO", "BNO", "USO", "IAU", "GLD",  # US stocks
            "AAAU", "SGOL", "FTGC", "BCD", "SLV"]
}

# All ETFs available in NY window (NY close is last, so has all)
ALL_ETFS = ETF_LIST


def ny_close_time(bj_date: datetime) -> datetime:
    ny_dt = bj_date - timedelta(hours=13)
    ny_dt_naive = ny_dt.replace(tzinfo=None)
    dst_start = datetime(ny_dt.year, 3, 8) + timedelta(days=(6 - datetime(ny_dt.year, 3, 8).weekday()))
    dst_end   = datetime(ny_dt.year, 11, 1) + timedelta(days=(6 - datetime(ny_dt.year, 11, 1).weekday()))
    in_dst = dst_start <= ny_dt_naive < dst_end
    h = NY_HOUR_SUMMER if in_dst else NY_HOUR_WINTER
    return bj_date.replace(hour=h, minute=0, second=0, microsecond=0)


def hk_close_time(bj_date: datetime) -> datetime:
    return bj_date.replace(hour=HK_HOUR, minute=HK_MIN, second=0, microsecond=0)


def lse_close_time(bj_date: datetime) -> datetime:
    return (bj_date + timedelta(days=1)).replace(hour=LSE_HOUR, minute=LSE_MIN, second=0, microsecond=0)


def nearest_price(series: pd.Series, target: datetime) -> float:
    """Find the nearest price <= target from a datetime-indexed series."""
    if series.empty:
        return None
    s = series.sort_index()
    available = s[s.index <= target]
    if available.empty:
        return None
    return round(float(available.iloc[-1]), 4)


def fetch_up_to(sym: str, end_dt: datetime) -> pd.Series:
    start_dt = end_dt - timedelta(days=20)
    try:
        df = yf.Ticker(sym).history(start=start_dt, end=end_dt, interval="1d")
        if df.empty:
            return pd.Series(dtype=float)
        return df['Close'].tz_convert('Asia/Shanghai')
    except Exception:
        return pd.Series(dtype=float)


def fetch_fut_up_to(sym: str, end_dt: datetime) -> pd.Series:
    start_dt = end_dt - timedelta(days=10)
    try:
        df = yf.Ticker(sym).history(start=start_dt, end=end_dt, interval="30m")
        if df.empty:
            return pd.Series(dtype=float)
        return df['Close']
    except Exception:
        return pd.Series(dtype=float)


def fetch_qdii_daily():
    bj_tz   = pytz.timezone('Asia/Shanghai')
    bj_now  = datetime.now(bj_tz)
    today   = bj_now.date()

    # Fetch all ETF daily data once (up to today's close)
    etf_data = {}
    for sym in ETF_LIST:
        print(f"  {sym}...", end=" ", flush=True)
        data = fetch_up_to(sym, bj_now)
        if not data.empty:
            etf_data[sym] = data
            print(f"OK ({len(data)} rows)")
        else:
            print("no data")
        time.sleep(random.uniform(1.5, 3.0))

    # Fetch all futures 30min data once (up to now)
    fut_data = {}
    for sym in FUT_LIST:
        print(f"  {sym}...", end=" ", flush=True)
        data = fetch_fut_up_to(sym, bj_now)
        if not data.empty:
            fut_data[sym] = data
            print(f"OK ({len(data)} rows)")
        else:
            print("no data")
        time.sleep(random.uniform(2.0, 4.0))

    if not etf_data:
        print("Error: No ETF data fetched."); return

    # Build trading days from first ETF
    ref = list(etf_data.values())[0]
    all_dates = sorted(set(ref.index.normalize().date))
    # Only keep dates strictly before today (fully closed)
    all_dates = [d for d in all_dates if d < today]

    rows = []
    for bj_date in all_dates:
        bj_dt = datetime.combine(bj_date, datetime.min.time(), tzinfo=bj_tz)

        hk_close  = hk_close_time(bj_dt)
        lse_close = lse_close_time(bj_dt)
        ny_close  = ny_close_time(bj_dt)

        for market, close_bj in [("HK", hk_close), ("LSE", lse_close), ("NY", ny_close)]:
            row = {"Date": bj_dt.strftime("%Y-%m-%d"), "Market": market}

            # Only emit if this market's close time is in the past
            if close_bj > bj_now:
                continue

            # ETF: nearest price <= close_bj (uses data fetched up to bj_now)
            for sym in ETF_LIST:
                row[sym] = nearest_price(etf_data.get(sym, pd.Series(dtype=float)), close_bj)

            # Futures: nearest 30min price <= close_bj
            for sym in FUT_LIST:
                row[sym] = nearest_price(fut_data.get(sym, pd.Series(dtype=float)), close_bj)

            rows.append(row)

    df_out = pd.DataFrame(rows)
    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", "qdii_daily_latest.csv")
    df_out.to_csv(out_path, index=False)
    print(f"\n--- Done ---")
    print(f"Saved: {out_path} ({len(df_out)} rows, {len(df_out)//3} trading days)")


if __name__ == "__main__":
    fetch_qdii_daily()