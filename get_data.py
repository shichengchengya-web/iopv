# fetch_qdii_daily.py
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz
import time
import random

def fetch_qdii_daily():
    """
    获取日线数据，用于 T-1 净值计算
    - 全部转为北京时间
    - 保留 .ffill() （按你的要求）
    """
    tickers = {
        # 伦敦
        "CRUD.L": "CRUD.L",
        "BRNT.L": "BRNT.L",
        # 纽约
        "DBO": "DBO",
        "BNO": "BNO",
        "USO": "USO",
        "IAU": "IAU",
        "GLD": "GLD",
        "AAAU": "AAAU",
        "SGOL": "SGOL",
        "FTGC": "FTGC",
        "BCD": "BCD",
        "SLV": "SLV",
        "CL=F": "CL=F",
        "BZ=F": "BZ=F",
        "GC=F": "GC=F",
        "SI=F": "SI=F",
        # 香港交易所
        "3175.HK": "3175.HK"
    }

    os.makedirs("output", exist_ok=True)
    bj_tz = pytz.timezone('Asia/Shanghai')
    bj_now = datetime.now(bj_tz)
    date_str = bj_now.strftime("%Y%m%d")
    
    output_file = os.path.join("output", f"qdii_daily_{date_str}.csv")
    print(f"[{bj_now.strftime('%Y-%m-%d %H:%M:%S')}] 开始获取日线数据...")

    data_list = []
    success = 0

    for name, symbol in tickers.items():
        print(f"  → {name:8} ", end="")
        try:
            df = yf.download(
                symbol,
                period="60d",
                interval="1d",
                auto_adjust=True,
                progress=False,
                timeout=20
            )
            
            if df.empty:
                print("× 无数据")
                continue

            # 只保留 Close
            df = df[['Close']].copy()
            
            # === 关键：严格转为北京时间 ===
            if df.index.tz is None:
                df.index = pd.to_datetime(df.index).tz_localize('UTC')
            df.index = df.index.tz_convert('Asia/Shanghai')
            
            df.columns = [name]
            data_list.append(df)
            print(f"✓ ({len(df)} 条)")
            success += 1

            time.sleep(random.uniform(0.8, 1.6))

        except Exception as e:
            print(f"× 错误: {e}")

    if not data_list:
        print("全部获取失败")
        return

    # 合并 + ffill（保留你的要求）
    combined = pd.concat(data_list, axis=1)
    combined = combined.sort_index(ascending=True)
    combined = combined.ffill()          # ← 你要求的保留

    # 保存
    combined.to_csv(output_file, encoding='utf-8-sig')
    
    print(f"\n{'='*70}")
    print(f"✅ 数据获取完成！成功 {success}/{len(tickers)} 个品种")
    print(f"文件: {output_file}")
    print(f"时间范围: {combined.index.min()} ~ {combined.index.max()}")
    print(f"{'='*70}")

    # 最后一天预览（非常重要）
    print("\n最后一天数据预览（北京时间）:")
    last_day = combined.index[-1].date()
    preview = combined[combined.index.date == last_day].tail(5)
    print(preview.round(4))

    # 生成 Excel 方便查看
    combined.to_excel(output_file.replace('.csv', '.xlsx'))
    print(f"已生成 Excel 文件")

    return combined


if __name__ == "__main__":
    fetch_qdii_daily()
