# get_close_prices.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

# ====================== 配置 ======================
tickers = {
    # ETF
    "CRUD.L": "CRUD.L",
    "BRNT.L": "BRNT.L",
    "DBO": "DBO",
    "BNO": "BNO",
    "USO": "USO",
    "3175.HK": "3175.HK",
    # 对应期货（用于T日跟踪）
    "CL=F": "CL=F",      # WTI
    "BZ=F": "BZ=F",      # Brent
}

os.makedirs("output", exist_ok=True)
date_str = datetime.now().strftime("%Y%m%d")
output_file = f"output/qdii_close_{date_str}.csv"

print("开始获取收盘价数据（用于 T-1 计算）...\n")

data_list = []

for name, symbol in tickers.items():
    print(f"获取 {name:8} ({symbol}) ...", end=" ")
    try:
        df = yf.download(
            symbol,
            period="60d",           # 近60天
            interval="1d",          # 先用日线，保证收盘价完整
            auto_adjust=True,
            progress=False
        )
        
        if df.empty:
            print("无数据")
            continue
            
        df = df[['Close']].copy()
        df.columns = [name]
        data_list.append(df)
        print(f"成功 ({len(df)} 条)")
        
    except Exception as e:
        print(f"失败: {e}")

if not data_list:
    print("全部失败")
    exit()

# 合并
combined = pd.concat(data_list, axis=1)
combined = combined.sort_index()

# 保存
combined.to_csv(output_file, encoding='utf-8-sig')
print(f"\n✅ 收盘价数据获取完成！")
print(f"文件路径: {output_file}")
print(f"总行数: {len(combined)}")
print(f"时间范围: {combined.index.min()} ~ {combined.index.max()}")
print("\n最后5条预览:")
print(combined.tail())

# 同时保存一份方便查看的 Excel
combined.to_excel(f"output/qdii_close_{date_str}.xlsx")
print(f"已同时生成 Excel 文件")
