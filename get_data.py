import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz

def fetch_qdii_aligned():
    tickers = {
        "CRUD.L": "CRUD.L", "BRNT.L": "BRNT.L", # 伦敦
        "USO": "USO", "BNO": "BNO", "DBO": "DBO", # 纽约
        "3175.HK": "3175.HK", # 香港
        "CL=F": "CL=F", "BZ=F": "BZ=F", "GC=F": "GC=F", "SI=F": "SI=F" # 期货
    }

    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_now = datetime.now(bj_tz)
    start_date = (bj_now - timedelta(days=60)).strftime('%Y-%m-%d')

    all_data = {}

    for name, symbol in tickers.items():
        try:
            # 抓取数据
            df = yf.download(symbol, start=start_date, interval="1d", progress=False)
            if df.empty: continue
            
            # 提取收盘价
            series = df['Close'].copy()
            
            # 核心对齐逻辑：
            # 1. 将所有市场的索引转为北京时间
            # 2. normalize() 强制去掉时分秒，只留日期 (YYYY-MM-DD)
            # 3. 这样不同市场在“同一天”的数据就会被合并到同一行
            series.index = series.index.tz_convert('Asia/Shanghai').normalize()
            
            all_data[name] = series
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    # 合并数据
    combined = pd.DataFrame(all_data)
    
    # 排序并填充
    # 此时的 ffill() 是良性的，因为它只在“节假日”起作用，而不会在“时差小时”起作用
    combined = combined.sort_index().ffill()
    
    # 格式化日期，只保留日期部分
    combined.index = combined.index.strftime('%Y-%m-%d')
    combined.index.name = 'Date'

    # 只输出最后一行作为“昨日锚点”
    output_path = os.path.join("output", "qdii_daily_latest.csv")
    combined.to_csv(output_path)
    print(f"Aligned data saved to {output_path}")

if __name__ == "__main__":
    fetch_qdii_aligned()
