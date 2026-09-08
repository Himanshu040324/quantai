import yfinance as yf

TICKER = "RELIANCE.NS"

print(f"Downloading 5 years of daily data for {TICKER}...")

data = yf.download(
    TICKER,
    period="5y",
    interval="1d",
    auto_adjust=False,
    progress=False,
)

if data.empty:
    print("ERROR: No data was returned.")
    raise SystemExit(1)

print("\nSUCCESS!")
print(f"Rows downloaded: {len(data)}")
print(f"Date range: {data.index.min()} -> {data.index.max()}")

print("\nOHLCV Data:")
print(data)