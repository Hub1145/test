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
    'AAPL': {'asset_type': 'Stock'},
    'GOOG': {'asset_type': 'Stock'},
    'MSFT': {'asset_type': 'Stock'},
    'BTC-USD': {'asset_type': 'Crypto'},
    'ETH-USD': {'asset_type': 'Crypto'},
    'EURUSD=X': {'asset_type': 'Forex'},
    'GBPUSD=X': {'asset_type': 'Forex'},
    'JPY=X': {'asset_type': 'Forex'},
    'GC=F': {'asset_type': 'Commodity'},
    'CL=F': {'asset_type': 'Commodity'},
    '^GSPC': {'asset_type': 'Index'},
    '^IXIC': {'asset_type': 'Index'},
}
