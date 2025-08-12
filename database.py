# database.py
#
# This module handles all interactions with the PostgreSQL/TimescaleDB database.
# It uses SQLAlchemy for connection management and executing queries.

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from config import DATABASE_CONFIG, SYMBOLS_TO_TRACK

class DatabaseManager:
    """
    Manages all database operations, including connection, symbol synchronization,
    and data insertion.
    """
    def __init__(self):
        """
        Initializes the database engine and session.
        """
        try:
            connection_uri = (
                f"postgresql+psycopg2://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
                f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['dbname']}"
            )
            self.engine = create_engine(connection_uri, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            print("Database connection established successfully.")
        except Exception as e:
            print(f"Error establishing database connection: {e}")
            raise

    def sync_symbols(self):
        """
        Synchronizes the symbols from the config file with the 'symbols' table in the database.
        - Adds new symbols from the config file to the database.
        - Does not delete symbols from the database if they are removed from the config.
          They can be marked as inactive manually in the database if needed.
        """
        print("Syncing symbols from config file to database...")
        try:
            with self.Session() as session:
                # Get existing symbols from the database
                existing_symbols_query = text("SELECT symbol FROM symbols")
                result = session.execute(existing_symbols_query)
                existing_symbols = {row[0] for row in result}

                # Find new symbols to add
                new_symbols = []
                for symbol, details in SYMBOLS_TO_TRACK.items():
                    if symbol not in existing_symbols:
                        new_symbols.append({
                            "symbol": symbol,
                            "asset_type": details.get('asset_type', 'Unknown'),
                            "exchange": details.get('exchange', None), # yfinance can provide this
                            "is_active": True
                        })

                if not new_symbols:
                    print("No new symbols to add.")
                    return

                # Insert new symbols into the database
                print(f"Found {len(new_symbols)} new symbols to add: {[s['symbol'] for s in new_symbols]}")
                insert_stmt = text("""
                    INSERT INTO symbols (symbol, asset_type, exchange, is_active)
                    VALUES (:symbol, :asset_type, :exchange, :is_active)
                    ON CONFLICT (symbol) DO NOTHING;
                """)
                session.execute(insert_stmt, new_symbols)
                session.commit()
                print("New symbols added to the database successfully.")

        except SQLAlchemyError as e:
            print(f"Error during symbol synchronization: {e}")

    def get_active_symbols(self):
        """
        Retrieves a list of all active symbols from the database.

        Returns:
            list: A list of dictionaries, where each dictionary contains the
                  id and symbol name for an active symbol.
        """
        try:
            with self.Session() as session:
                query = text("SELECT id, symbol FROM symbols WHERE is_active = TRUE ORDER BY symbol")
                result = session.execute(query)
                # Return a list of dicts for easier use later
                return [{"id": row[0], "symbol": row[1]} for row in result]
        except SQLAlchemyError as e:
            print(f"Error fetching active symbols: {e}")
            return []

    def insert_ohlcv_data(self, ohlcv_df, symbol_id):
        """
        Inserts OHLCV data from a pandas DataFrame into the ohlcv_1m table.
        Uses 'ON CONFLICT DO NOTHING' to prevent duplicate entries, making the
        insertion process idempotent.

        Args:
            ohlcv_df (pd.DataFrame): DataFrame containing OHLCV data with a DatetimeIndex.
            symbol_id (int): The foreign key ID of the symbol from the 'symbols' table.
        """
        if ohlcv_df.empty:
            return 0

        try:
            with self.engine.connect() as connection:
                # Prepare data for insertion
                records = []
                for timestamp, row in ohlcv_df.iterrows():
                    records.append({
                        "symbol_id": symbol_id,
                        "time": timestamp,
                        "open": row['Open'],
                        "high": row['High'],
                        "low": row['Low'],
                        "close": row['Close'],
                        "volume": row.get('Volume', 0) # Use .get() for safety if Volume is missing
                    })

                if not records:
                    return 0

                # Use a transaction for bulk insert
                with connection.begin():
                    insert_stmt = text("""
                        INSERT INTO ohlcv_1m (symbol_id, "time", "open", high, low, "close", volume)
                        VALUES (:symbol_id, :time, :open, :high, :low, :close, :volume)
                        ON CONFLICT (symbol_id, "time") DO NOTHING;
                    """)
                    result = connection.execute(insert_stmt, records)
                    return result.rowcount

        except SQLAlchemyError as e:
            print(f"Error inserting OHLCV data: {e}")
            return 0

    def get_latest_timestamp(self, symbol_id):
        """
        Gets the most recent timestamp for a given symbol in the ohlcv_1m table.

        Args:
            symbol_id (int): The ID of the symbol.

        Returns:
            pd.Timestamp or None: The latest timestamp, or None if no data exists.
        """
        try:
            with self.Session() as session:
                query = text("SELECT MAX(time) FROM ohlcv_1m WHERE symbol_id = :symbol_id")
                result = session.execute(query, {"symbol_id": symbol_id}).scalar_one_or_none()
                return pd.to_datetime(result, utc=True) if result else None
        except SQLAlchemyError as e:
            print(f"Error fetching latest timestamp: {e}")
            return None

if __name__ == '__main__':
    # This block is for testing the DatabaseManager class directly.
    # It requires the database and schema to be set up.
    print("Running database module tests...")

    # You would need to have your DB running and config.py filled out to run this.
    # For now, this serves as a placeholder for manual testing.
    try:
        db_manager = DatabaseManager()
        db_manager.sync_symbols()
        active_symbols = db_manager.get_active_symbols()
        print(f"\nFound active symbols: {active_symbols}")

        if active_symbols:
            # Test getting the latest timestamp for the first active symbol
            first_symbol_id = active_symbols[0]['id']
            latest_ts = db_manager.get_latest_timestamp(first_symbol_id)
            print(f"Latest timestamp for symbol ID {first_symbol_id} is: {latest_ts}")

    except Exception as e:
        print(f"\nCould not run database tests. Please ensure your database is running,")
        print(f"the schema from 'schema.sql' is applied, and 'config.py' is correctly filled out.")
        print(f"Error: {e}")
