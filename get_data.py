import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

# Market close times in Beijing timezone
# HK:  16:00 Beijing same day
# LSE: 00:30 Beijing next day
# NY:  04:00 Winter / 05:00 Summer Beijing next day

HK_HOUR, HK_MIN = 16, 0
LSE_HOUR, LSE_MIN = 0, 30
NY_HOUR_WINTER = 4
NY_HOUR_SUMMER = 5


def ny_close_time(bj_date: datetime) -> datetime:
    """Return NY close time in Beijing, with DST awareness."""
    # NY = Beijing - 13h (EST) or -12h (EDT)
    ny_dt = bj_date - timedelta(hours=13)
    ny_dt_naive = ny_dt.replace(tzinfo=None)
    # US DST: 2nd Sunday March - 1st Sunday November
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
    """Find the nearest price to target from a datetime-indexed series."""
    if series.empty:
        return None
    s = series.sort_index()
    diffs = pd.Series((s.index - target).total_seconds(), index=s.index)
    diffs = diffs.abs()
    return float(s.loc[diffs.idxmin()])


def fetch_qdii_daily():
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_today = datetime.now(bj_tz)

    etf_list = [
        "CRUD.L", "BRNT.L", "DBO", "BNO", "USO",
        "3175.HK", "IAU", "GLD", "AAAU", "SGOL", "FTGC", "BCD", "SLV"
    ]
    fut_list = ["CL=F", "BZ=F"]

    # Stock ETF: 60 days daily data
    end_dt   = bj_today
    start_dt = end_dt - timedelta(days=10)  # 7 trading days + buffer

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

    # Futures: 7 days 30min data
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
        print("Error: No ETF data fetched."); return

    # Build trading days from ETF daily data
    ref = list(etf_daily.values())[0]
    all_dates = sorted(set(ref.index.normalize().date))

    rows = []
    for bj_date in all_dates:
        bj_dt = datetime.combine(bj_date, datetime.min.time(), tzinfo=bj_tz)

        # Three close times in Beijing
        hk_close  = hk_close_time(bj_dt)
        lse_close = lse_close_time(bj_dt)
        ny_close  = ny_close_time(bj_dt)

        for market, close_bj in [("HK", hk_close), ("LSE", lse_close), ("NY", ny_close)]:
            # Only emit rows for trading days fully in the past
            if bj_dt.date() >= bj_today.date():
                continue
            date_label = bj_dt.strftime("%Y-%m-%d")

            row = {"Date": date_label, "Market": market}

            # ETF: nearest daily close to this market's close time
            for sym in etf_list:
                row[sym] = nearest_price(etf_daily[sym], close_bj) if sym in etf_daily else None

            # Futures: nearest 30min close to this market's close time
            for sym in fut_list:
                row[sym] = nearest_price(fut_30m[sym], close_bj) if sym in fut_30m else None

            rows.append(row)

    df_out = pd.DataFrame(rows)
    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", "qdii_daily_latest.csv")
    df_out.to_csv(out_path, index=False)
    print(f"\n--- Done ---")
    print(f"Saved: {out_path} ({len(df_out)} rows, {len(df_out)//3} trading days)")


if __name__ == "__main__":
    fetch_qdii_daily()