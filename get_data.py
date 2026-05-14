# get_market_close_prices_final.py
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import os
import traceback
import sys

LOG_FILE = "output/fetch_log.txt"

def log(msg=""):
    print(msg)
    os.makedirs("output", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

log("=" * 50)
log("开始获取 QDII 数据")
log("=" * 50)

tickers_config = {
    # 伦敦 LSE (北京 00:30 → UTC 前一天 16:30)
    "CRUD.L":  {"market": "London",  "close_utc_hour": 16, "close_utc_min": 30},
    "BRNT.L":  {"market": "London",  "close_utc_hour": 16, "close_utc_min": 30},
    # 纽约 NYSE (北京 04:00 → UTC 前一天 20:00， 夏令时 19:00)
    "DBO":     {"market": "NewYork", "close_utc_hour": 20, "close_utc_min": 0,  "dst": True},
    "BNO":     {"market": "NewYork", "close_utc_hour": 20, "close_utc_min": 0,  "dst": True},
    "USO":     {"market": "NewYork", "close_utc_hour": 20, "close_utc_min": 0,  "dst": True},
    # 首尔/香港
    "3175.HK": {"market": "Seoul",   "close_utc_hour": 5,  "close_utc_min": 30},
}

date_str = datetime.now().strftime("%Y%m%d")
output_csv = f"output/qdii_market_close_{date_str}.csv"
output_xlsx = output_csv.replace(".csv", ".xlsx")

log(f"目标日期: {date_str}")

os.makedirs("output", exist_ok=True)
results = []
errors = []

for ticker, cfg in tickers_config.items():
    market = cfg["market"]
    log(f"\n--- {ticker} ({market}) ---")

    try:
        df = yf.download(
            ticker,
            period="5d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            timeout=20
        )

        if df.empty:
            log(f"  × 下载为空")
            errors.append(f"{ticker}: download empty")
            continue

        log(f"  数据行数: {len(df)}, 最新日期: {df.index[-1]}")

        # 确保是 UTC
        if df.index.tz is None:
            df.index = pd.to_datetime(df.index).tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")

        # 提取 Close 列（处理 MultiIndex）
        if isinstance(df.columns, pd.MultiIndex):
            close = df["Close"].squeeze()
        else:
            close = df["Close"].squeeze()

        latest_dt = df.index[-1]
        latest_close = float(close.iloc[-1])

        log(f"  最新收盘: {latest_close} @ {latest_dt}")
        results.append({
            "Date": str(latest_dt.date()),
            "Ticker": ticker,
            "Close_Price": latest_close,
            "Market": market,
        })
        log(f"  ✓ 成功")

    except Exception as e:
        tb = traceback.format_exc()
        log(f"  × 错误: {e}")
        log(f"    {tb.strip()}")
        errors.append(f"{ticker}: {e}")

log(f"\n=== 结果: {len(results)}/{len(tickers_config)} 成功 ===")

if errors:
    log(f"失败: {errors}")

if results:
    df_result = pd.DataFrame(results)
    df_pivot = df_result.pivot(index="Date", columns="Ticker", values="Close_Price")
    df_pivot.index.name = "Date"

    df_pivot.to_csv(output_csv, encoding="utf-8-sig")
    log(f"CSV 保存: {output_csv}")

    try:
        df_pivot.to_excel(output_xlsx)
        log(f"XLSX 保存: {output_xlsx}")
    except Exception as e:
        log(f"XLSX 保存失败: {e}")

    log(f"\n{df_pivot.round(4).to_string()}")
    log("\n✅ 完成")
else:
    log("\n❌ 全部失败，退出")
    sys.exit(1)
