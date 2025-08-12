# config.py
#
# This file contains the configuration for the data ingestion system.
# It includes database connection details and the list of symbols to track.

# --- Database Configuration ---
# In a production environment, it is highly recommended to use environment variables
# for these settings to avoid hardcoding credentials in the source code.
DATABASE_CONFIG = {
    "user": "your_username",      # Replace with your PostgreSQL username
    "password": "your_password",  # Replace with your PostgreSQL password
    "host": "localhost",          # Replace with your database host
    "port": "5432",               # Replace with your database port
    "dbname": "market_data"       # The name of the database created for this project
}

# --- Symbol Configuration ---
# This is the master list of symbols the system should track.
# The ingestion service will automatically add any new symbols from this list
# to the database and begin fetching data for them.
#
# Asset types are inferred from the yfinance ticker format where possible,
# but can be manually specified or refined in the database later.
#
# Format: 'TICKER': {'asset_type': 'Type'}
SYMBOLS_TO_TRACK = {
    # Stocks
    'AAPL': {'asset_type': 'Stock'},
    'GOOG': {'asset_type': 'Stock'},
    'MSFT': {'asset_type': 'Stock'},
    'AMZN': {'asset_type': 'Stock'},
    'NVDA': {'asset_type': 'Stock'},
    'TSLA': {'asset_type': 'Stock'},
    'JPM': {'asset_type': 'Stock'},
    'V': {'asset_type': 'Stock'},
    'BABA': {'asset_type': 'Stock'},
    'TM': {'asset_type': 'Stock'},
    'SIE.DE': {'asset_type': 'Stock'},

    # Crypto
    'BTC-USD': {'asset_type': 'Crypto'},
    'ETH-USD': {'asset_type': 'Crypto'},
    'XRP-USD': {'asset_type': 'Crypto'},
    'ADA-USD': {'asset_type': 'Crypto'},
    'DOGE-USD': {'asset_type': 'Crypto'},
    'SOL-USD': {'asset_type': 'Crypto'},

    # Forex
    'EURUSD=X': {'asset_type': 'Forex'},
    'GBPUSD=X': {'asset_type': 'Forex'},
    'JPY=X': {'asset_type': 'Forex'},
    'AUDUSD=X': {'asset_type': 'Forex'},
    'USDCAD=X': {'asset_type': 'Forex'},
    'USDCHF=X': {'asset_type': 'Forex'},
    'NZDUSD=X': {'asset_type': 'Forex'},

    # Indices
    '^GSPC': {'asset_type': 'Index'},
    '^IXIC': {'asset_type': 'Index'},
    '^DJI': {'asset_type': 'Index'},
    '^FTSE': {'asset_type': 'Index'},
    '^N225': {'asset_type': 'Index'},
    '^STOXX50E': {'asset_type': 'Index'},

    # Commodities & Metals
    'GC=F': {'asset_type': 'Commodity'}, # Gold
    'CL=F': {'asset_type': 'Commodity'}, # Crude Oil
    'SI=F': {'asset_type': 'Commodity'}, # Silver
    'PL=F': {'asset_type': 'Commodity'}, # Platinum
    'NG=F': {'asset_type': 'Commodity'}, # Natural Gas
    'ZB=F': {'asset_type': 'Commodity'}, # T-Bond Futures
}
