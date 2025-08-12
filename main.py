# main.py
#
# This is the main entry point for the Raw Market Data Storage & Update System.
# To run the service, execute this file from your terminal:
#
# python main.py
#

from ingestion_service import IngestionService

if __name__ == '__main__':
    # Create an instance of the ingestion service
    service = IngestionService()

    # Start the service. This will handle symbol syncing, backfilling,
    # and the continuous update loop.
    service.run()
