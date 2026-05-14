# get_market_close_prices_final.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
import traceback
import sys

LOG_FILE = "output/fetch_log.txt"

def log(msg):
    """同时打印和写入日志文件"""
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

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
    xlsx_file = output_file.replace('.csv', '.xlsx')

    log("开始获取各市场收盘价（北京时间）...")

    results = []
    errors = []

    for name, cfg in tickers_config.items():
        symbol = cfg["symbol"]
        market = cfg["market"]
        base_close_time = cfg["close_time"]

        log(f"  → {name:8} ({market}) ", end="")

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
                log("× 无数据")
                errors.append(f"{name}: 无数据")
                continue

            # 保留 Close 列并确保是单层列名
            if isinstance(df.columns, pd.MultiIndex):
                df = df["Close"]
            else:
                df = df[['Close']].squeeze()

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
                target_str = f"{latest_date} {base_close_time}:00:00+08:00"

            target = pd.to_datetime(target_str)

            # 提取价格：优先用 asof，fallback 到最新可用数据
            close_price = df.asof(target)

            if pd.notna(close_price):
                log(f"✓ {close_price:.4f} @ {target.strftime('%H:%M')} (数据日期: {latest_date})")
                results.append({
                    'Date': latest_date,
                    'Ticker': name,
                    'Close_Price': float(close_price),
                    'Market': market,
                    'Close_Time_BJT': target.strftime('%H:%M')
                })
            else:
                # Fallback：直接取当天的收盘价
                today_data = df[df.index.date == latest_date]
                if not today_data.empty:
                    close_price = float(today_data.iloc[-1])
                    log(f"✓ {close_price:.4f} @ {latest_date} (fallback，直接取收盘)")
                    results.append({
                        'Date': latest_date,
                        'Ticker': name,
                        'Close_Price': close_price,
                        'Market': market,
                        'Close_Time_BJT': 'fallback'
                    })
                else:
                    log("× 价格为空")
                    errors.append(f"{name}: 价格为空")

        except Exception as e:
            tb = traceback.format_exc()
            log(f"× 错误: {e}")
            errors.append(f"{name}: {e}")
            log(f"  Stack: {tb.strip()}")

    # 生成结果
    log(f"\n本次处理结果: {len(results)}/{len(tickers_config)} 成功")
    if errors:
        log(f"失败列表: {errors}")

    if results:
        df_result = pd.DataFrame(results)
        df_pivot = df_result.pivot(index='Date', columns='Ticker', values='Close_Price')

        df_pivot.to_csv(output_file, encoding='utf-8-sig')
        log(f"CSV 已保存: {output_file}")

        try:
            df_pivot.to_excel(xlsx_file)
            log(f"XLSX 已保存: {xlsx_file}")
        except Exception as e:
            log(f"XLSX 保存失败（无需处理）: {e}")

        log(f"\n最新收盘价预览:")
        preview = df_pivot.tail(5).round(4)
        log(str(preview))
        log("\n✅ 完成!")
    else:
        log("\n❌ 未获取到任何数据，请检查日志")
        sys.exit(1)

if __name__ == "__main__":
    fetch_market_close_prices()
