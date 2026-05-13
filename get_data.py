"""
get_data.py - LOF 溢价监控原油期货数据采集
功能：
  1. 首次运行：拉取 CL=F (WTI) + BZ=F (布伦特) 近 7 天分钟线
  2. 后续运行：增量追加最近 5 天数据，按 timestamp 去重
输出：output/oil_minute_data.csv
  列：timestamp, CL=F, BZ=F
"""

import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

OUTPUT_FILE = "output/oil_minute_data.csv"
TICKERS = ["CL=F", "BZ=F"]  # WTI 原油期货, 布伦特原油期货


def fetch_initial_data() -> pd.DataFrame:
    """首次运行：拉取 7 天分钟线（Yahoo 1m 数据上限约 8 天）"""
    dfs = []
    for ticker_sym in TICKERS:
        print(f"  获取 {ticker_sym} 近 7 天数据...")
        ticker = yf.Ticker(ticker_sym)
        # Yahoo Finance 1m  granularity 每次最多约 8 天，用 7d 保险
        df = ticker.history(period="7d", interval="1m")
        if df.empty:
            print(f"  警告：{ticker_sym} 未获取到数据，跳过")
            continue
        # 只保留 Close 列并重命名
        df = df[["Close"]].rename(columns={"Close": ticker_sym})
        dfs.append(df)
        print(f"  {ticker_sym}: {len(df)} 条记录")

    if not dfs:
        raise RuntimeError("所有品种均未获取到数据")

    # 合并：outer join，保留所有时间点
    result = dfs[0]
    for df in dfs[1:]:
        result = result.join(df, how="outer")
    result = result.ffill()  # 前向填充，保持价格连续
    return result


def fetch_recent_data(existing_df: pd.DataFrame) -> pd.DataFrame:
    """后续运行：拉取最近 5 天数据，增量追加"""
    # 统一将已有数据的索引转为 tz-naive UTC
    if existing_df.index.tz is not None:
        existing_df = existing_df.copy()
        existing_df.index = existing_df.index.tz_convert("UTC").tz_localize(None)

    dfs = []
    for ticker_sym in TICKERS:
        print(f"  获取 {ticker_sym} 近 5 天数据...")
        ticker = yf.Ticker(ticker_sym)
        df = ticker.history(period="5d", interval="1m")
        if df.empty:
            print(f"  警告：{ticker_sym} 未获取到数据，跳过")
            continue
        df = df[["Close"]].rename(columns={"Close": ticker_sym})
        dfs.append(df)
        print(f"  {ticker_sym}: {len(df)} 条记录")

    if not dfs:
        raise RuntimeError("所有品种均未获取到数据")

    new_data = dfs[0]
    for df in dfs[1:]:
        new_data = new_data.join(df, how="outer")
    new_data = new_data.ffill()

    # 追加新数据（不覆盖旧数据）
    combined = pd.concat([existing_df, new_data])
    return combined


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """按 timestamp 去重，保留每条记录最新值

    先将索引转为 tz-naive UTC，再去重排序。
    避免 pd.concat 后 tz-naive 与 tz-aware 混在一起导致 sort 报错。
    """
    # 将索引转为 tz-naive UTC（try/except 处理 Index 类型无 tz 属性的情况）
    try:
        if df.index.tz is not None:
            df = df.copy()
            df.index = df.index.tz_convert("UTC").tz_localize(None)
    except AttributeError:
        # 非 DatetimeIndex（如 concat 后变成 object Index），直接转
        df = df.copy()
        df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)

    before = len(df)
    df = df[~df.index.duplicated(keep="last")]
    after = len(df)
    if before != after:
        print(f"  去重：{before} → {after}（移除 {before - after} 条重复）")
    return df.sort_index()


def save_csv(df: pd.DataFrame):
    """保存到 CSV，timestamp 格式统一为 ISO8601"""
    os.makedirs("output", exist_ok=True)
    df.index = df.index.strftime("%Y-%m-%dT%H:%M:%S")
    df.to_csv(OUTPUT_FILE)
    print(f"  已保存 {len(df)} 条记录 → {OUTPUT_FILE}")


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始获取原油期货数据")
    print(f"  目标品种：{TICKERS}")

    if os.path.exists(OUTPUT_FILE):
        # 后续运行：增量追加
        print(f"检测到已有数据文件 ({OUTPUT_FILE})，执行增量追加...")
        existing = pd.read_csv(OUTPUT_FILE, index_col=0, parse_dates=True)
        print(f"  现有记录：{len(existing)} 条")
        combined = fetch_recent_data(existing)
        combined = deduplicate(combined)
        save_csv(combined)
        print(f"  最终记录：{len(combined)} 条")
    else:
        # 首次运行：拉取 7 天（Yahoo 1m 上限约 8 天）
        print("首次运行，拉取近 7 天数据...")
        df = fetch_initial_data()
        df = deduplicate(df)
        save_csv(df)
        print(f"  共 {len(df)} 条记录")

    print("数据获取完成")


if __name__ == "__main__":
    main()
