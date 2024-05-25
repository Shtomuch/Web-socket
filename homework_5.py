import aiohttp
import asyncio
import sys
from datetime import datetime, timedelta

API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="


class CurrencyRatesFetcher:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def fetch_rates(self, date: str):
        async with self.session.get(f"{API_URL}{date}") as response:
            if response.status == 200:
                return await response.json()
            else:
                response.raise_for_status()

    async def close(self):
        await self.session.close()

class CurrencyRatesService:
    def __init__(self, fetcher: CurrencyRatesFetcher):
        self.fetcher = fetcher

    async def get_currency_rates(self, days: int):
        results = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%d.%m.%Y')
            try:
                data = await self.fetcher.fetch_rates(date)
                rates = self.parse_rates(data)
                if rates:
                    results.append({date: rates})
            except Exception as e:
                print(f"Error fetching data for {date}: {e}")
        return results

    def parse_rates(self, data):
        try:
            rates = {
                "EUR": {
                    "sale": next(item for item in data['exchangeRate'] if item["currency"] == "EUR")["saleRate"],
                    "purchase": next(item for item in data['exchangeRate'] if item["currency"] == "EUR")["purchaseRate"]
                },
                "USD": {
                    "sale": next(item for item in data['exchangeRate'] if item["currency"] == "USD")["saleRate"],
                    "purchase": next(item for item in data['exchangeRate'] if item["currency"] == "USD")["purchaseRate"]
                }
            }
            return rates
        except Exception as e:
            print(f"Error parsing data: {e}")
            return None

async def main(days: int):
    fetcher = CurrencyRatesFetcher()
    service = CurrencyRatesService(fetcher)
    rates = await service.get_currency_rates(days)
    await fetcher.close()
    print(rates)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: py .\\main.py <number_of_days>")
        sys.exit(1)

    days = int(sys.argv[1])
    if days < 1 or days > 10:
        print("Please enter a number between 1 and 10")
        sys.exit(1)

    asyncio.run(main(days))
