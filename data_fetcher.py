import yfinance as yf
import pandas as pd
import datetime

def fetch_yfinance_data(symbol, interval, start_date=None, end_date=None):
    """
    Fetches historical data from yfinance for a given symbol and interval.

    Args:
        symbol (str): The ticker symbol (e.g., 'AAPL', 'BTC-USD', 'EURUSD=X').
        interval (str): The data interval (e.g., '1d', '1wk', '1mo', '1h').
                        Be aware of yfinance's limitations on historical depth for smaller intervals.
        start_date (str, optional): Start date for data in 'YYYY-MM-DD' format.
                                    If None, fetches from the earliest available date for the interval.
        end_date (str, optional): End date for data in 'YYYY-MM-DD' format.
                                  If None, fetches up to the most recent data.

    Returns:
        pd.DataFrame: A DataFrame with 'Open', 'High', 'Low', 'Close', 'Volume'
                      and a DatetimeIndex, or None if fetching fails or no data.
    """
    try:
        if start_date is None and end_date is None:
            # Fetch all available data for the given interval
            print(f"  Attempting to fetch ALL available data for {symbol} at {interval} interval.")
            df = yf.download(symbol, interval=interval, period='max')
        else:
            print(f"  Attempting to fetch data for {symbol} at {interval} interval from {start_date} to {end_date}.")
            df = yf.download(symbol, start=start_date, end=end_date, interval=interval)

        if df.empty:
            print(f"  No data returned from yfinance for {symbol} - {interval}.")
            return None

        # Select the desired columns: Open, High, Low, Close, Volume
        # yfinance often includes 'Adj Close', which we don't need for this specific output.
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']

        # Check if all required columns exist, and only select those that do
        available_cols = [col for col in required_cols if col in df.columns]
        if len(available_cols) < len(required_cols):
            missing_cols = set(required_cols) - set(available_cols)
            print(f"  Warning: Missing columns {missing_cols} for {symbol} - {interval}. Proceeding with available data.")

        df = df[available_cols]

        # yfinance returns timezone-aware datetimes for recent data, but historical
        # data might be naive. We need to ensure all timestamps are in UTC.
        if df.index.tz is None:
            # If timezone naive, localize to the exchange's timezone (or a common default)
            # and then convert to UTC. Most equities are 'America/New_York'.
            # For a robust system, this could be specified per-symbol.
            try:
                df.index = df.index.tz_localize('America/New_York').tz_convert('UTC')
            except Exception:
                # Fallback for non-market times or other issues
                df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')

        return df
    except Exception as e:
        print(f"  Error fetching yfinance data for {symbol} - {interval}: {e}")
        return None
