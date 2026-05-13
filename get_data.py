import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import pytz

def fetch_qdii_data():
    # 1. Define ticker mapping (yfinance Ticker)
    tickers = {
        "CRUD.L": "CRUD.L",
        "BRNT.L": "BRNT.L",
        "DBO": "DBO",
        "BNO": "BNO",
        "USO": "USO",
        "3175.HK": "3175.HK",
        "IAU": "IAU",
        "GLD": "GLD",
        "AAAU": "AAAU",
        "SGOL": "SGOL",
        "FTGC": "FTGC",
        "BCD": "BCD",
        "SLV": "SLV",
        "hf_CL": "CL=F",
        "hf_OIL": "BZ=F",
        "hf_GC": "GC=F",
        "hf_SI": "SI=F"
    }

    all_data = pd.DataFrame()

    for name, symbol in tickers.items():
        print(f"Fetching {name} ({symbol})...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="30d", interval="30m")
            
            if df.empty:
                print(f"Warning: {name} no data, skipping")
                continue

            df = df[['Close']]
            
            # Convert to Beijing time
            df.index = df.index.tz_convert('Asia/Shanghai')
            
            df_30m = df['Close']
            df_30m.name = name
            
            if all_data.empty:
                all_data = df_30m.to_frame()
            else:
                all_data = all_data.join(df_30m, how='outer')
                
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    if all_data.empty:
        print("Error: All tickers failed. Check network or yfinance status")
        os.makedirs("output", exist_ok=True)
        bj_now = datetime.now(pytz.timezone('Asia/Shanghai'))
        date_str = bj_now.strftime("%Y%m%d")
        with open(os.path.join("output", f"qdii_30m_{date_str}_empty.csv"), "w") as f:
            f.write("date,message\n")
            f.write(f"{bj_now.isoformat()},No data available\n")
        return

    # Save by date
    bj_now = datetime.now(pytz.timezone('Asia/Shanghai'))
    date_str = bj_now.strftime("%Y%m%d")
    file_name = f"qdii_30m_{date_str}.csv"

    os.makedirs("output", exist_ok=True)
    
    # Sort descending (newest first)
    all_data.sort_index(ascending=False, inplace=True)
    
    save_path = os.path.join("output", file_name)
    all_data.to_csv(save_path)
    print(f"--- Done ---")
    print(f"Saved to: {save_path}")
    print(f"Tickers: {len(all_data.columns)}")

if __name__ == "__main__":
    fetch_qdii_data()