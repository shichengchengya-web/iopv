import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import pytz

def fetch_qdii_data():
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

    os.makedirs("output", exist_ok=True)
    bj_now = datetime.now(pytz.timezone('Asia/Shanghai'))
    date_str = bj_now.strftime("%Y%m%d")
    output_file = os.path.join("output", f"qdii_30m_{date_str}.csv")

    # Load existing data if exists
    if os.path.exists(output_file):
        existing_data = pd.read_csv(output_file, index_col=0, parse_dates=True)
        print(f"Loaded existing data: {len(existing_data)} rows")
    else:
        existing_data = pd.DataFrame()
        print("No existing data, will fetch full history")

    # Get date range
    end_date = bj_now
    start_date = end_date - timedelta(days=7)
    print(f"Fetching data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    new_data_list = []

    for name, symbol in tickers.items():
        print(f"Fetching {name} ({symbol})...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="30m")
            
            if df.empty:
                print(f"Warning: {name} no data, skipping")
                continue

            df = df[['Close']]
            df.index = df.index.tz_convert('Asia/Shanghai')
            
            df_30m = df['Close']
            df_30m.name = name
            new_data_list.append(df_30m)
            
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    if not new_data_list:
        print("Error: All tickers failed. Check network or yfinance status")
        return

    # Merge new data
    new_data = pd.concat(new_data_list, axis=1)
    
    # Filter to last 2 days only to avoid huge files
    cutoff = bj_now - timedelta(days=2)
    new_data = new_data[new_data.index >= cutoff]
    print(f"New data (last 2 days): {len(new_data)} rows")

    # Merge with existing, drop duplicates (keep newer)
    if not existing_data.empty:
        combined = pd.concat([existing_data, new_data])
        # Remove duplicates, keeping the last occurrence (newer data)
        combined = combined[~combined.index.duplicated(keep='last')]
        combined = combined.sort_index(ascending=False)
    else:
        combined = new_data.sort_index(ascending=False)

    combined.to_csv(output_file)
    print(f"--- Done ---")
    print(f"Saved to: {output_file}")
    print(f"Total rows: {len(combined)}")
    print(f"Columns (tickers): {len(combined.columns)}")

if __name__ == "__main__":
    fetch_qdii_data()