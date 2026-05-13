import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

def fetch_qdii_daily():
    """
    获取QDII相关品种数据并自动匹配跨时区锚点
    - 时间统一转为北京时间 (UTC+8)
    - 自动识别纽约夏令时/冬令时锚点
    - 输出到 output/qdii_anchor_latest.csv
    """
    # 你的持仓与期货映射表
    tickers = {
        "CRUD.L": "CRUD.L",  # 伦敦 ETF
        "BRNT.L": "BRNT.L",
        "DBO": "DBO",        # 纽约 ETF
        "BNO": "BNO",
        "USO": "USO",
        "3175.HK": "3175.HK",
        "IAU": "IAU",
        "hf_CL": "CL=F",     # WTI 期货
        "hf_OIL": "BZ=F",    # 布油期货
        "hf_GC": "GC=F"
    }

    os.makedirs("output", exist_ok=True)
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_now = datetime.now(bj_tz)
    date_str = bj_now.strftime("%Y%m%d")
    output_file = os.path.join("output", f"qdii_daily_{date_str}.csv")
    latest_file = os.path.join("output", "qdii_anchor_latest.csv") # 软链接式命名，方便实时程序读取

    # 抓取近60天数据
    end_date = bj_now + timedelta(days=1)
    start_date = bj_now - timedelta(days=60)
    
    print(f"[{bj_now.strftime('%Y-%m-%d %H:%M:%S')} BJ] Starting Fetching...")

    new_data_list = []
    
    for name, symbol in tickers.items():
        print(f"  Fetching {name}...", end=" ", flush=True)
        try:
            ticker = yf.Ticker(symbol)
            # 使用1小时或1日线，这里建议用1h以确保能匹配到凌晨的锚点
            df = ticker.history(start=start_date, end=end_date, interval="60m")

            if df.empty:
                print("no data")
                continue

            df = df[['Close']].copy()
            df.index = df.index.tz_convert('Asia/Shanghai')
            df.columns = [name]
            new_data_list.append(df)
            print(f"OK")
            
            # 随机延迟，防止GitHub IP被封
            time.sleep(random.uniform(1.0, 3.0))

        except Exception as e:
            print(f"Error: {e}")

    if not new_data_list:
        return

    # 合并并处理缺失值
    combined = pd.concat(new_data_list, axis=1)
    combined = combined.sort_index(ascending=True).ffill() 

    # --- 锚点提取逻辑 ---
    # 纽约锚点自动识别 (纽约 16:00 收盘时对应的北京时间)
    ny_tz = pytz.timezone('America/New_York')
    # 模拟昨天的收盘时间点
    yesterday = bj_now - timedelta(days=1)
    ny_close_local = ny_tz.localize(datetime(yesterday.year, yesterday.month, yesterday.day, 16, 0))
    ny_anchor_bj = ny_close_local.astimezone(bj_tz).strftime("%H:%M")
    
    # 伦敦锚点通常固定 (伦敦 16:30 收盘对应北京 00:30 或 23:30)
    # 此处假设你主要关注的是 00:30
    lse_anchor_bj = "00:30"

    print(f"\n[Anchor Check] NY Close (BJ Time): {ny_anchor_bj}")
    print(f"[Anchor Check] LSE Close (BJ Time): {lse_anchor_bj}")

    # 转换索引格式方便保存
    combined.index = combined.index.strftime('%Y-%m-%d %H:%M:%S+08:00')

    # 保存每日文件
    combined.to_csv(output_file)
    # 保存最新一份，实时程序固定读取这个文件名
    combined.to_csv(latest_file)
    
    print(f"\n--- Done ---")
    print(f"Files saved in /output/ folder.")

if __name__ == "__main__":
    fetch_qdii_daily()
