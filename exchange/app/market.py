import requests
#importing BTC value from CoinMarketCap API
class Report:

    def __init__(self):
        # API Parameters
        self.url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        self.params = {
            'start': '1',
            'limit': '1',
            'convert': 'USD'
        }
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': 'a3b1ae02-3cec-431e-94c3-80ef02445a1a'
        }

    def get_data(self):
        # Gathering data
        r = requests.get(url=self.url, headers=self.headers, params=self.params).json()

        return round(r['data'][0]['quote']['USD']['price'], 8)