# get_market_close_prices_final.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os

def is_us_summer_time(dt):
    """判断是否为美国夏令时（3月第二个周日 ~ 11月第一个周日，简化版）"""
    return 3 < dt.month < 11   # 5月份肯定是夏令时

def fetch_market_close_prices():
    """
    按各市场真实收盘时间提取价格（强烈推荐用于 T-1 净值计算）
    """
    tickers_config = {
        # 伦敦 LSE ≈ 北京时间 00:30
        "CRUD.L": {"symbol": "CRUD.L", "market": "London",  "close_time": "00:30"},
        "BRNT.L": {"symbol": "BRNT.L", "market": "London",  "close_time": "00:30"},
        
        # 纽约 NYSE
        "DBO":    {"symbol": "DBO",    "market": "NewYork", "close_time": "04:00"},  
        "BNO":    {"symbol": "BNO",    "market": "NewYork", "close_time": "04:00"},
        "USO":    {"symbol": "USO",    "market": "NewYork", "close_time": "04:00"},
        
        # 香港/首尔市场
        "3175.HK":{"symbol": "3175.HK","market": "Seoul",   "close_time": "14:30"},
    }

    os.makedirs("output", exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = f"output/qdii_market_close_{date_str}.csv"

    print("开始获取各市场收盘价（北京时间）...\n")

    results = []
    for name, cfg in tickers_config.items():
        symbol = cfg["symbol"]
        market = cfg["market"]
        base_close_time = cfg["close_time"]
        
        print(f"  → {name:8} ({market}) ", end="")
        
        try:
            # 下载日线
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

            df = df[['Close']].copy()
            
            # 严格转为北京时间
            if df.index.tz is None:
                df.index = pd.to_datetime(df.index).tz_localize('UTC')
            df.index = df.index.tz_convert('Asia/Shanghai')

            # 获取最近一天
            latest_date = df.index.max().date()
            
            # 处理纽约夏令时
            if market == "NewYork":
                hour = 4 if is_us_summer_time(latest_date) else 5
                target_str = f"{latest_date} {hour:02d}:00:00+08:00"
            else:
                target_str = f"{latest_date} {base_close_time}:00+08:00"
            
            target = pd.to_datetime(target_str)
            
            # 提取最接近的价格（日线只有一条，所以用 asof）
            close_price = df['Close'].asof(target)
            
            if pd.notna(close_price):
                print(f"✓ {close_price:.4f} @ {target.strftime('%H:%M')}")
                results.append({
                    'Date': latest_date,
                    'Ticker': name,
                    'Close_Price': close_price,
                    'Market': market,
                    'Close_Time_BJT': target.strftime('%H:%M')
                })
            else:
                print("× 价格为空")
                
        except Exception as e:
            print(f"× 错误: {e}")

    # 生成结果
    if results:
        df_result = pd.DataFrame(results)
        df_pivot = df_result.pivot(index='Date', columns='Ticker', values='Close_Price')
        
        df_pivot.to_csv(output_file, encoding='utf-8-sig')
        df_pivot.to_excel(output_file.replace('.csv', '.xlsx'))
        
        print(f"\n✅ 完成！共处理 {len(df_pivot)} 天数据")
        print(f"文件保存: {output_file}")
        print("\n最新收盘价预览:")
        print(df_pivot.tail(5).round(4))
    else:
        print("未获取到任何数据")

if __name__ == "__main__":
    fetch_market_close_prices()
