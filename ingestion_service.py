# ingestion_service.py
#
# This is the main service responsible for orchestrating the data ingestion process.
# It handles symbol synchronization, historical backfilling, and continuous updates.

import time
import pandas as pd
from datetime import datetime, timedelta

from database import DatabaseManager
from data_fetcher import fetch_yfinance_data

class IngestionService:
    """
    Orchestrates the entire data ingestion workflow.
    """
    def __init__(self):
        """
        Initializes the service and the database manager.
        """
        print("Initializing Ingestion Service...")
        self.db_manager = DatabaseManager()

    def _backfill_symbol(self, symbol_id, symbol_name):
        """
        Performs a historical backfill for a given symbol.

        This process is designed to handle the limitations of yfinance, specifically
        that deep historical data is only available at daily granularity, while 1-minute
        data is only available for the last 7 days.

        Args:
            symbol_id (int): The database ID of the symbol.
            symbol_name (str): The ticker name of the symbol.
        """
        print(f"--- Starting Backfill Process for {symbol_name} ---")
        latest_ts = self.db_manager.get_latest_timestamp(symbol_id)

        if latest_ts is None:
            print(f"No existing data for {symbol_name}. Performing full historical backfill.")
            # 1. Fetch max available daily data for the initial large backfill.
            print(f"  Step 1: Fetching max available daily data for {symbol_name}...")
            daily_df = fetch_yfinance_data(symbol_name, interval='1d')
            if daily_df is not None and not daily_df.empty:
                # 2. Resample daily data to 1-minute intervals to create a baseline.
                # 'ffill' will carry the OHLC values forward for each minute of the day.
                # Volume will be split across the minutes in a trading day (approx. 390 mins for stocks).
                print(f"  Step 2: Resampling daily data to 1-minute frequency for {symbol_name}...")
                daily_df.rename(columns={'Volume': 'DailyVolume'}, inplace=True)
                minutely_df = daily_df.resample('1min').ffill()
                minutely_df['Volume'] = minutely_df['DailyVolume'] / (60 * 6.5) # Approximate for US market
                minutely_df.drop(columns=['DailyVolume'], inplace=True)

                # Insert the resampled data
                inserted_count = self.db_manager.insert_ohlcv_data(minutely_df, symbol_id)
                print(f"  Inserted {inserted_count} rows of resampled historical data for {symbol_name}.")
            else:
                print(f"  Could not fetch daily historical data for {symbol_name}. Skipping baseline backfill.")

        # 3. Fetch the last 7 days of 1-minute data to get accurate recent history.
        # This will overwrite the resampled data for the overlapping period.
        print(f"  Step 3: Fetching recent 1-minute data for {symbol_name} (last 7 days)...")
        start_date_1m = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
        recent_1m_df = fetch_yfinance_data(symbol_name, interval='1m', start_date=start_date_1m)

        if recent_1m_df is not None and not recent_1m_df.empty:
            inserted_count = self.db_manager.insert_ohlcv_data(recent_1m_df, symbol_id)
            print(f"  Inserted/updated {inserted_count} rows of recent 1-minute data for {symbol_name}.")
        else:
            print(f"  No recent 1-minute data found for {symbol_name}.")

        print(f"--- Backfill Process for {symbol_name} Complete ---")

    def _update_symbols(self):
        """
        Fetches the latest 1-minute data for all active symbols and updates the database.
        """
        print("\n--- Starting Scheduled Update Cycle ---")
        active_symbols = self.db_manager.get_active_symbols()
        if not active_symbols:
            print("No active symbols found. Waiting for next cycle.")
            return

        print(f"Found {len(active_symbols)} active symbols to update.")
        for symbol in active_symbols:
            symbol_id, symbol_name = symbol['id'], symbol['symbol']
            print(f"Updating {symbol_name}...")

            # Fetch data for the last 2 days to ensure we don't miss any bars.
            # The ON CONFLICT clause in the DB will handle duplicates.
            start_date = (datetime.utcnow() - timedelta(days=2)).strftime('%Y-%m-%d')
            latest_df = fetch_yfinance_data(symbol_name, interval='1m', start_date=start_date)

            if latest_df is not None and not latest_df.empty:
                inserted_count = self.db_manager.insert_ohlcv_data(latest_df, symbol_id)
                print(f"  -> Inserted {inserted_count} new 1-minute bars for {symbol_name}.")
            else:
                print(f"  -> No new 1-minute data found for {symbol_name}.")
            # Small delay to avoid hitting API rate limits
            time.sleep(2)

        print("--- Scheduled Update Cycle Complete ---")

    def run(self):
        """
        The main entry point to start the ingestion service.
        """
        print("--- Service Starting ---")
        # 1. Sync symbols from config file to DB
        self.db_manager.sync_symbols()

        # 2. Perform initial backfill for all active symbols.
        # This is especially important for newly added symbols.
        print("\n--- Checking for Initial Backfills ---")
        all_symbols = self.db_manager.get_active_symbols()
        for symbol in all_symbols:
            self._backfill_symbol(symbol['id'], symbol['symbol'])
            time.sleep(5) # Be respectful of the API

        # 3. Start the continuous update loop
        print("\n--- Starting Continuous Update Loop (every 60 seconds) ---")
        while True:
            try:
                self._update_symbols()
                sleep_duration = 60
                print(f"Waiting for {sleep_duration} seconds until the next update...")
                time.sleep(sleep_duration)
            except KeyboardInterrupt:
                print("\nService stopped by user. Exiting.")
                break
            except Exception as e:
                print(f"An unexpected error occurred in the main loop: {e}")
                print("Restarting loop after 60 seconds...")
                time.sleep(60)

if __name__ == '__main__':
    service = IngestionService()
    service.run()
