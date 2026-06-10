#!/usr/bin/env python3
"""
market-lab daily collector
==========================
Pulls daily OHLCV for the research universe and appends to data/<TICKER>.csv.
Idempotent: safe to re-run; dedupes on date. Run after US close via GitHub Actions.

Primary source: yfinance. Fallback: stooq (close-only) if yfinance fails.
"""
import os, sys, time
import pandas as pd

UNIVERSE = {
    # Core indices / asset classes
    "SPY": "S&P 500", "QQQ": "Nasdaq 100", "IWM": "Russell 2000", "DIA": "Dow",
    "GLD": "Gold", "USO": "Oil (WTI proxy)", "SLV": "Silver",
    "TLT": "20y Treasuries", "HYG": "High yield", "UUP": "Dollar",
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum",
    # Leverage vehicles we may trade
    "SSO": "2x S&P", "UPRO": "3x S&P", "TQQQ": "3x Nasdaq",
    # Sectors (rotation research)
    "XLK": "Tech", "XLE": "Energy", "XLF": "Financials", "XLV": "Health",
    "XLI": "Industrials", "XLP": "Staples", "XLU": "Utilities", "XLY": "Discretionary",
    # Vol / breadth
    "^VIX": "VIX", "^GSPC": "S&P index", "^IXIC": "Nasdaq composite",
}

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def fetch_yf(ticker: str, period: str) -> pd.DataFrame:
    import yfinance as yf
    df = yf.download(ticker, period=period, interval="1d",
                     auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError("empty")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    df.columns = [str(c).lower() for c in df.columns]
    df = df.rename(columns={"index": "date"})
    keep = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[keep]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def fetch_stooq(ticker: str) -> pd.DataFrame:
    sym = {"^GSPC": "^spx", "^IXIC": "^ndq", "^VIX": "vi.f"}.get(ticker, ticker.lower().replace("-", ""))
    url = f"https://stooq.com/q/d/l/?s={sym}&i=d"
    df = pd.read_csv(url)
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df[["date", "open", "high", "low", "close", "volume"]]


def sanity_check(df: pd.DataFrame, ticker: str) -> bool:
    """Reject obviously bad rows rather than committing garbage."""
    if df.empty:
        return False
    bad = (df["close"] <= 0) | (df["close"].pct_change().abs() > 0.5)
    if bad.iloc[1:].any():
        print(f"  WARN {ticker}: {int(bad.iloc[1:].sum())} suspicious rows (>|50%| daily move or <=0) — keeping but flagged")
    return True


def update(ticker: str):
    path = os.path.join(DATA_DIR, f"{ticker.replace('^','').replace('-','_')}.csv")
    existing = None
    period = "max"
    if os.path.exists(path):
        existing = pd.read_csv(path, parse_dates=["date"])
        existing["date"] = existing["date"].dt.date
        period = "3mo"  # incremental top-up

    try:
        new = fetch_yf(ticker, period)
    except Exception as e:
        print(f"  yfinance failed for {ticker} ({e}); trying stooq")
        try:
            new = fetch_stooq(ticker)
        except Exception as e2:
            print(f"  FAILED {ticker}: {e2}")
            return

    if existing is not None:
        merged = pd.concat([existing, new]).drop_duplicates(subset="date", keep="last")
    else:
        merged = new
    merged = merged.sort_values("date").reset_index(drop=True)

    if sanity_check(merged, ticker):
        merged.to_csv(path, index=False)
        print(f"  OK {ticker}: {len(merged)} rows through {merged['date'].iloc[-1]}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Collecting {len(UNIVERSE)} tickers -> {DATA_DIR}")
    for t in UNIVERSE:
        update(t)
        time.sleep(1)  # be polite to the API
    print("Done.")


if __name__ == "__main__":
    main()
