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
    - 统一转为北京时间 (+08:00)
    - 优化多ticker批量获取 + 单独处理顽固ticker
    - 增加重试机制
    """
    # ETF + 商品列表
    tickers = {
        "CRUD.L": "CRUD.L",      # WTI Crude
        "BRNT.L": "BRNT.L",      # Brent Crude
        "DBO": "DBO",
        "BNO": "BNO",
        "USO": "USO",
        "3175.HK": "3175.HK",    # Samsung Oil ETF
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

    # 近45天（更稳妥，避免边界问题）
    end_date = bj_now.date() + timedelta(days=1)   # 包含今天
    start_date = bj_now - timedelta(days=45)

    print(f"[{bj_now.strftime('%Y-%m-%d %H:%M:%S')}] Fetching Daily Close (interval='1d')...")

    # === 第一步：批量下载（最快）===
    symbols = list(tickers.values())
    print("批量下载尝试...")
    try:
        df_bulk = yf.download(
            tickers=symbols,
            start=start_date,
            end=end_date,
            interval="1d",
            group_by='ticker',
            auto_adjust=False,
            prepost=False,
            threads=True,
            timeout=30
        )
    except Exception as e:
        print(f"批量下载失败: {e}")
        df_bulk = pd.DataFrame()

    new_data_list = []

    for name, symbol in tickers.items():
        print(f"  Processing {name} ({symbol})...", end=" ", flush=True)
        
        try:
            if not df_bulk.empty and symbol in df_bulk.columns.levels[0]:
                # 从批量结果中提取
                df = df_bulk[symbol][['Close']].copy()
            else:
                # 单个ticker重试（针对期货/HK常见问题）
                ticker_obj = yf.Ticker(symbol)
                df = ticker_obj.history(
                    start=start_date,
                    end=end_date,
                    interval="1d",
                    auto_adjust=False
                )
                if df.empty:
                    # 再尝试一次 + 不同参数
                    time.sleep(2)
                    df = ticker_obj.history(
                        period="1mo",
                        interval="1d"
                    )
            
            if df.empty:
                print("no data")
                continue

            # === 关键：统一转北京时间 ===
            # yfinance 返回的 index 通常是 tz-aware (UTC 或交易所时区)
            if df.index.tz is None:
                df.index = pd.to_datetime(df.index).tz_localize('UTC')
            
            # 转为北京时间
            df.index = df.index.tz_convert('Asia/Shanghai')
            
            # 只保留 Close 并重命名
            df = df[['Close']].copy()
            df.columns = [name]
            
            new_data_list.append(df)
            print(f"OK ({len(df)} rows)")

        except Exception as e:
            print(f"Error: {e}")
        
        # 随机延迟防封
        time.sleep(random.uniform(1.8, 3.5))

    if not new_data_list:
        print("Error: No data fetched at all.")
        return

    # 合并
    combined = pd.concat(new_data_list, axis=1)
    
    # 排序 + 前向填充（不同市场休市日期不同）
    combined = combined.sort_index(ascending=True).ffill()
    
    # 格式化索引为北京时间字符串
    combined.index = combined.index.strftime('%Y-%m-%d %H:%M:%S+08:00')
    combined.index.name = 'Datetime'
    
    # 保存两个文件（最新 + 日期版）
    latest_path = os.path.join("output", "qdii_daily_latest.csv")
    combined.to_csv(latest_path)
    combined.to_csv(output_file)
    
    print(f"\n--- Success ---")
    print(f"Latest file: {latest_path}")
    print(f"Date file: {output_file}")
    print(f"Total rows: {len(combined)}, Columns: {combined.shape[1]}")


if __name__ == "__main__":
    fetch_qdii_daily()
