import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import pytz

def fetch_qdii_data():
    # 1. 定义品种映射表 (yfinance Ticker)
    tickers = {
        "CRUD.L": "CRUD.L",   # 伦敦 WTI
        "BRNT.L": "BRNT.L",   # 伦敦 Brent
        "DBO": "DBO",         # 纽约 Oil
        "BNO": "BNO",         # 纽约 Brent
        "USO": "USO",         # 纽约 Oil
        "3175.HK": "3175.HK", # 首尔/香港 Samsung
        "IAU": "IAU",         # 黄金
        "GLD": "GLD",         # 黄金
        "AAAU": "AAAU",       # 黄金
        "SGOL": "SGOL",       # 黄金
        "FTGC": "FTGC",       # 商品
        "BCD": "BCD",         # 商品
        "SLV": "SLV",         # 白银
        "hf_CL": "CL=F",      # WTI期货
        "hf_OIL": "BZ=F",     # 布油期货
        "hf_GC": "GC=F",      # 黄金期货
        "hf_SI": "SI=F"       # 白银期货
    }

    all_data = pd.DataFrame()

    for name, symbol in tickers.items():
        print(f"正在获取 {name} ({symbol})...")
        try:
            # 获取最近 30 天的数据，使用 30 分钟间隔以确保重采样精度
            ticker = yf.Ticker(symbol)
            # 注意：1m数据最多只能获取最近30天，符合你的需求
            df = ticker.history(period="30d", interval="30m")
            
            if df.empty:
                print(f"警告：{name} 未获取到数据，跳过")
                continue

            # 提取收盘价
            df = df[['Close']]
            
            # 2. 统一转换为北京时间
            # yfinance 返回的是带时区的 UTC，我们转为 Asia/Shanghai
            df.index = df.index.tz_convert('Asia/Shanghai')
            
            # 3. 瘦身：重采样为 30 分钟线
            # 使用 '30T'，label='right' 确保包含 00:30, 14:30 筈关键点
            df_30m = df['Close'].resample('30T').last().ffill()
            
            # 4. 合并数据
            df_30m.name = name
            if all_data.empty:
                all_data = df_30m.to_frame()
            else:
                all_data = all_data.join(df_30m, how='outer')
                
        except Exception as e:
            print(f"获取 {name} 出错: {e}")

    if all_data.empty:
        print("错误：所有品种均未获取到数据，请检查网络或 yfinance 状态")
        return

    # 5. 按日期保存文件
    # 获取北京时间的当前日期
    bj_now = datetime.now(pytz.timezone('Asia/Shanghai'))
    date_str = bj_now.strftime("%Y%m%d")
    file_name = f"qdii_30m_{date_str}.csv"

    # 确保 output 文件夹存在
    os.makedirs("output", exist_ok=True)
    
    # 时间倒序排列（最新的在上面）
    all_data.sort_index(ascending=False, inplace=True)
    
    # 路径拼接并保存
    save_path = os.path.join("output", file_name)
    all_data.to_csv(save_path)
    print(f"--- 任务完成 ---")
    print(f"数据已保存至: {save_path}")
    print(f"包含品种数量: {len(all_data.columns)}")

if __name__ == "__main__":
    fetch_qdii_data()