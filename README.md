# Raw Market Data Storage & Update System

This project provides a scalable database and ingestion service to store and update raw market data for multiple financial symbols. It is designed to be robust, easy to configure, and scalable to handle a large number of symbols.

The system uses **PostgreSQL** with the **TimescaleDB** extension for efficient time-series data storage and **Python** for the ingestion service. Data is sourced from **yfinance**.

## Key Features

- **Scalable Time-Series Database**: Uses TimescaleDB for high-performance storage and querying of market data.
- **Automated Historical Backfill**: When a new symbol is added, the system automatically fetches the maximum available historical data.
- **Continuous Minute-by-Minute Updates**: All active symbols are updated with the latest 1-minute OHLCV data every 60 seconds.
- **Idempotent & Robust**: The ingestion logic is designed to prevent duplicate data entries and handle service interruptions gracefully.
- **Easy Configuration**: Adding new symbols is as simple as adding an entry to a Python dictionary in the config file.

## Project Structure

```
.
├── config.py             # Configuration for DB credentials and symbol list
├── data_fetcher.py       # Module for fetching data from yfinance
├── database.py           # Module for all database interactions
├── ingestion_service.py  # The main application entry point
├── README.md             # This file
├── requirements.txt      # Python dependencies
└── schema.sql            # SQL script for setting up the database schema
```

---

## System Setup

Follow these steps to set up and run the data ingestion system.

### 1. Database Setup (PostgreSQL + TimescaleDB)

You need a PostgreSQL database with the TimescaleDB extension installed.

1.  **Install PostgreSQL and TimescaleDB**:
    Follow the official installation guide for your operating system: [TimescaleDB Installation](https://docs.timescale.com/install/latest/self-hosted/)

2.  **Create a Database and User**:
    Connect to PostgreSQL (e.g., using `psql`) and create a database for the project and a user with a secure password.

    ```sql
    CREATE DATABASE market_data;
    CREATE USER myuser WITH PASSWORD 'mypassword';
    GRANT ALL PRIVILEGES ON DATABASE market_data TO myuser;
    ```

3.  **Enable the TimescaleDB Extension**:
    Connect to your newly created database and run the following command:

    ```sql
    \c market_data
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    ```

4.  **Create the Schema**:
    Run the `schema.sql` script provided in this project to create the necessary tables (`symbols`, `ohlcv_1m`) and hypertables.

    ```bash
    psql -d market_data -U myuser < schema.sql
    ```

### 2. Python Environment Setup

1.  **Clone the Repository**:
    Get the project files on your local machine.

2.  **Install Dependencies**:
    It is recommended to use a virtual environment. Navigate to the project directory and run:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

### 3. System Configuration

1.  **Edit `config.py`**:
    Open the `config.py` file and update the `DATABASE_CONFIG` dictionary with the credentials for the user and database you created in Step 1.

    ```python
    # config.py
    DATABASE_CONFIG = {
        "user": "myuser",
        "password": "mypassword",
        "host": "localhost",
        "port": "5432",
        "dbname": "market_data"
    }
    ```

---

## How to Use

### Adding New Symbols

To start tracking a new symbol, simply add its ticker to the `SYMBOLS_TO_TRACK` dictionary in `config.py`. The service will automatically detect the new symbol on its next run, add it to the database, and begin the historical backfill process.

Example: To add Microsoft (`MSFT`), add the following line:

```python
# config.py
SYMBOLS_TO_TRACK = {
    'AAPL': {'asset_type': 'Stock'},
    'GOOG': {'asset_type': 'Stock'},
    'MSFT': {'asset_type': 'Stock'}, # <-- Add new symbol here
    # ... other symbols
}
```

### Running the Ingestion Service

Once the setup and configuration are complete, you can start the service by running the `main.py` script:

```bash
python main.py
```

The service will perform the following actions on startup:
1.  **Sync Symbols**: Add any new symbols from `config.py` to the database.
2.  **Initial Backfill**: Check all symbols for missing historical data and backfill them.
3.  **Start Update Loop**: Begin the continuous loop of fetching new 1-minute data every 60 seconds.

You can stop the service at any time by pressing `Ctrl+C`.

---

## Important Note on `yfinance` Limitations

This implementation uses `yfinance` as the data source, which has important limitations for a production environment:

- **1-Minute Data History**: `yfinance` only provides access to 1-minute OHLCV data for the **last 7 days**. The backfill process in this service works around this by using daily data to create a long-term history and then overwriting the last 7 days with high-fidelity 1-minute data.
- **No Spread Data**: `yfinance` does not provide bid/ask spread data.
- **Reliability**: As it relies on scraping public Yahoo Finance APIs, it is not a guaranteed service and may be subject to rate limiting or API changes.

For a production-grade system, it is highly recommended to adapt the `data_fetcher.py` module to use a professional, paid data provider API.
