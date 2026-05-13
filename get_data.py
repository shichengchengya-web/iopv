import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import pytz

def fetch_qdii_data():
    # 1. 瀹氫箟鍝佺鏄犲皠琛?(yfinance Ticker)
    tickers = {
        "CRUD.L": "CRUD.L",   # 浼︽暒 WTI
        "BRNT.L": "BRNT.L",   # 浼︽暒 Brent
        "DBO": "DBO",         # 绾界害 Oil
        "BNO": "BNO",         # 绾界害 Brent
        "USO": "USO",         # 绾界害 Oil
        "3175.HK": "3175.HK", # 棣栧皵/棣欐腐 Samsung
        "IAU": "IAU",         # 榛勯噾
        "GLD": "GLD",         # 榛勯噾
        "AAAU": "AAAU",       # 榛勯噾
        "SGOL": "SGOL",       # 榛勯噾
        "FTGC": "FTGC",       # 鍟嗗搧
        "BCD": "BCD",         # 鍟嗗搧
        "SLV": "SLV",         # 鐧介摱
        "hf_CL": "CL=F",      # WTI鏈熻揣
        "hf_OIL": "BZ=F",     # 甯冩补鏈熻揣
        "hf_GC": "GC=F",      # 榛勯噾鏈熻揣
        "hf_SI": "SI=F"       # 鐧介摱鏈熻揣
    }

    all_data = pd.DataFrame()

    for name, symbol in tickers.items():
        print(f"姝ｅ湪鑾峰彇 {name} ({symbol})...")
        try:
            # 鑾峰彇鏈€杩?30 澶╃殑鏁版嵁锛屼娇鐢?1 鍒嗛挓闂撮殧浠ョ‘淇濋噸閲囨牱绮惧害
            ticker = yf.Ticker(symbol)
            # 娉ㄦ剰锛?m鏁版嵁鏈€澶氬彧鑳借幏鍙栨渶杩?0澶╋紝绗﹀悎浣犵殑闇€姹?            df = ticker.history(period="30d", interval="1m")
            
            if df.empty:
                print(f"璀﹀憡锛歿name} 鏈幏鍙栧埌鏁版嵁锛岃烦杩?)
                continue

            # 鎻愬彇鏀剁洏浠?            df = df[['Close']]
            
            # 2. 缁熶竴杞崲涓哄寳浜椂闂?            # yfinance 杩斿洖鐨勬槸甯︽椂鍖虹殑 UTC锛屾垜浠浆涓?Asia/Shanghai
            df.index = df.index.tz_convert('Asia/Shanghai')
            
            # 3. 鐦﹁韩锛氶噸閲囨牱涓?30 鍒嗛挓绾?            # 浣跨敤 '30T'锛宭abel='right' 纭繚鍖呭惈 00:30, 14:30 绛夊叧閿偣
            df_30m = df['Close'].resample('30T').last().ffill()
            
            # 4. 鍚堝苟鏁版嵁
            df_30m.name = name
            if all_data.empty:
                all_data = df_30m.to_frame()
            else:
                all_data = all_data.join(df_30m, how='outer')
                
        except Exception as e:
            print(f"鑾峰彇 {name} 鍑洪敊: {e}")

    if all_data.empty:
        print("閿欒锛氭墍鏈夊搧绉嶅潎鏈幏鍙栧埌鏁版嵁锛岃妫€鏌ョ綉缁滄垨 yfinance 鐘舵€?)
        return

    # 5. 鎸夋棩鏈熶繚瀛樻枃浠?    # 鑾峰彇鍖椾含鏃堕棿鐨勫綋鍓嶆棩鏈?    bj_now = datetime.now(pytz.timezone('Asia/Shanghai'))
    date_str = bj_now.strftime("%Y%m%d")
    file_name = f"qdii_30m_{date_str}.csv"

    # 纭繚 output 鏂囦欢澶瑰瓨鍦?    os.makedirs("output", exist_ok=True)
    
    # 鏃堕棿鍊掑簭鎺掑垪锛堟渶鏂扮殑鍦ㄤ笂闈級
    all_data.sort_index(ascending=False, inplace=True)
    
    # 璺緞鎷兼帴骞朵繚瀛?    save_path = os.path.join("output", file_name)
    all_data.to_csv(save_path)
    print(f"--- 浠诲姟瀹屾垚 ---")
    print(f"鏁版嵁宸蹭繚瀛樿嚦: {save_path}")
    print(f"鍖呭惈鍝佺鏁伴噺: {len(all_data.columns)}")

if __name__ == "__main__":
    fetch_qdii_data()