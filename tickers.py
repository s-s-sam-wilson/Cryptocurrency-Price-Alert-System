import requests
import threading
import time
from datetime import datetime
from db import Database

class Ticker:
    RANK_THRESHOLD = 2000
    OUT_OF_RANK_VALUE = 6000

    @staticmethod
    def upsert_ticker(coin_id, name, symbol, price_usd, market_cap_usd, volume_24h_usd, timestamp, rank):
        exists = Database.select(
            table="tickers",
            columns=["coin_id"],
            condition="coin_id = ?",
            params=[coin_id]
        )

        if exists:
            Database.update(
                table="tickers",
                columns=["name", "symbol", "price_usd", "market_cap_usd", "volume_24h_usd", "timestamp", "rank"],
                values=[name, symbol, price_usd, market_cap_usd, volume_24h_usd, timestamp, rank],
                condition="coin_id = ?",
                condition_params=[coin_id]
            )
        else:
            Database.insert(
                table="tickers",
                columns=["coin_id", "name", "symbol", "price_usd", "market_cap_usd", "volume_24h_usd", "timestamp",
                         "rank"],
                values=[coin_id, name, symbol, price_usd, market_cap_usd, volume_24h_usd, timestamp, rank]
            )

    @staticmethod
    def fetch_and_store_tickers():
        url = "https://api.coinpaprika.com/v1/tickers"
        while True:
            try:
                response = requests.get(url)
                response.raise_for_status()
                tickers = response.json()
                current_coin_ids = set()

                for ticker in tickers:
                    coin_id = ticker.get("id")
                    name = ticker.get("name")
                    symbol = ticker.get("symbol")
                    price_usd = ticker["quotes"]["USD"]["price"]
                    market_cap_usd = ticker["quotes"]["USD"]["market_cap"]
                    volume_24h_usd = ticker["quotes"]["USD"]["volume_24h"]
                    timestamp = datetime.utcnow().isoformat()
                    rank = ticker.get("rank")
                    current_coin_ids.add(coin_id)

                    # Use the generic insert method
                    Ticker.upsert_ticker(
                        coin_id=coin_id,
                        name=name,
                        symbol=symbol,
                        price_usd=price_usd,
                        market_cap_usd=market_cap_usd,
                        volume_24h_usd=volume_24h_usd,
                        timestamp=timestamp,
                        rank=rank
                    )


                print("Tickers updated successfully at", timestamp)
            except Exception as e:
                print(f"Error fetching tickers: {e}")

            time.sleep(60)

    @staticmethod
    def start_ticker_thread():
        ticker_thread = threading.Thread(target=Ticker.fetch_and_store_tickers, daemon=True)
        ticker_thread.start()