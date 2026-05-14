# -*- coding: utf-8 -*-

import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
import yfinance as yf
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =========================================================
# 基础配置
# =========================================================

OUTPUT_DIR = "output"
LOG_FILE = f"{OUTPUT_DIR}/fetch_log.txt"

MAX_WORKERS = 5
RETRY_TIMES = 3
DOWNLOAD_PERIOD = "10d"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================================================
# Ticker 配置
# =========================================================

TICKERS = {
    "CRUD.L": "London",
    "BRNT.L": "London",
    "DBO": "NewYork",
    "BNO": "NewYork",
    "USO": "NewYork",
    "3175.HK": "HongKong",
}


# =========================================================
# 日志
# =========================================================

def log(msg=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"[{now}] {msg}"

    print(text)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


# =========================================================
# 创建带重试 Session
# =========================================================

def create_session():

    session = Session()

    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retries)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


session = create_session()


# =========================================================
# 下载单个 ticker
# =========================================================

def fetch_ticker(ticker, market):

    for attempt in range(1, RETRY_TIMES + 1):

        try:

            log(f"[{ticker}] 开始下载 (第 {attempt} 次)")

            df = yf.download(
                ticker,
                period=DOWNLOAD_PERIOD,
                interval="1d",
                auto_adjust=True,
                progress=False,
                timeout=20,
                threads=False,
                session=session
            )

            if df.empty:
                raise Exception("返回数据为空")

            # 统一时间索引
            if df.index.tz is None:
                df.index = pd.to_datetime(df.index).tz_localize("UTC")
            else:
                df.index = df.index.tz_convert("UTC")

            # 兼容 MultiIndex
            close_col = df["Close"]

            if isinstance(close_col, pd.DataFrame):
                close_series = close_col.iloc[:, 0]
            else:
                close_series = close_col

            latest_dt = df.index[-1]
            latest_close = float(close_series.iloc[-1])

            log(f"[{ticker}] 成功: {latest_close}")

            return {
                "Date": str(latest_dt.date()),
                "Ticker": ticker,
                "Market": market,
                "Close_Price": round(latest_close, 6),
            }

        except Exception as e:

            log(f"[{ticker}] 失败: {e}")

            if attempt == RETRY_TIMES:
                traceback_str = traceback.format_exc()
                log(traceback_str)

            time.sleep(2)

    return None


# =========================================================
# 主程序
# =========================================================

def main():

    log("=" * 60)
    log("开始获取 QDII 收盘数据")
    log("=" * 60)

    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = {
            executor.submit(fetch_ticker, ticker, market): ticker
            for ticker, market in TICKERS.items()
        }

        for future in as_completed(futures):

            ticker = futures[future]

            try:
                result = future.result()

                if result:
                    results.append(result)

            except Exception as e:
                log(f"[{ticker}] Future 异常: {e}")

    # =====================================================
    # 输出结果
    # =====================================================

    if not results:

        log("全部获取失败")
        sys.exit(1)

    df_result = pd.DataFrame(results)

    df_pivot = df_result.pivot_table(
        index="Date",
        columns="Ticker",
        values="Close_Price"
    )

    date_str = datetime.now().strftime("%Y%m%d")

    csv_path = f"{OUTPUT_DIR}/qdii_market_close_{date_str}.csv"
    xlsx_path = f"{OUTPUT_DIR}/qdii_market_close_{date_str}.xlsx"

    df_pivot.to_csv(csv_path, encoding="utf-8-sig")

    try:
        df_pivot.to_excel(xlsx_path)
    except Exception as e:
        log(f"Excel 保存失败: {e}")

    log("")
    log(df_pivot.round(4).to_string())

    log("")
    log(f"CSV:  {csv_path}")
    log(f"XLSX: {xlsx_path}")

    log("")
    log(f"完成: 成功 {len(results)} / 总计 {len(TICKERS)}")


if __name__ == "__main__":
    main()
