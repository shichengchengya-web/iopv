#!/usr/bin/env python3
"""
fetch_korea_fundamentals.py
获取三星电子(005930.KS)和SK海力士(000660.KS)基本面数据
"""

import yfinance as yf
import json
import os
from datetime import datetime

KOREAN_TZ = "Asia/Shanghai"  # 与A股时区一致


def fetch_fundamentals(ticker: str, name: str) -> dict:
    """获取单只股票的基本面数据"""
    print(f"Fetching {name} ({ticker})...")
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # 核心指标
        data = {
            "name": name,
            "ticker": ticker,
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "market_cap": info.get("marketCap"),
            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),
            "eps_trailing": info.get("trailingEps"),
            "eps_forward": info.get("forwardEps"),
            "dividend_yield": info.get("dividendYield"),
            "dividend_rate": info.get("dividendRate"),
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "analyst_target": info.get("targetMeanPrice"),
            "recommendation": info.get("recommendationKey"),
            "profit_margin": info.get("profitMargins"]),
            "operating_margin": info.get("operatingMargins"]),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"]),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "book_value": info.get("bookValue"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "full_time_employees": info.get("fullTimeEmployees"),
        }

        # 转换为可序列化类型
        for k, v in data.items():
            if v is None or v == "N/A":
                data[k] = None

        print(f"  -> {name} OK (PE={data['pe_ratio']}, PB={data['pb_ratio']})")
        return data

    except Exception as e:
        print(f"  -> {name} FAILED: {e}")
        return {"name": name, "ticker": ticker, "error": str(e)}


def main():
    stocks = [
        ("005930.KS", "三星电子"),
        ("000660.KS", "SK海力士"),
    ]

    results = []
    for ticker, name in stocks:
        data = fetch_fundamentals(ticker, name)
        results.append(data)

    # 输出到output目录
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"korea_fundamentals_{timestamp}.json")
    summary_file = os.path.join(output_dir, "korea_fundamentals_latest.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {output_file}")

    # 打印摘要
    print("\n========== 摘要 ==========")
    for r in results:
        if "error" in r:
            print(f"{r['name']}: ERROR - {r['error']}")
        else:
            pe = r.get("pe_ratio")
            pb = r.get("pb_ratio")
            mktcap = r.get("market_cap", 0)
            mktcap_t = mktcap / 1e12 if mktcap else 0
            print(f"{r['name']} ({r['ticker']}): PE={pe}, PB={pb}, 市值={mktcap_t:.1f}万亿韩元")


if __name__ == "__main__":
    main()
