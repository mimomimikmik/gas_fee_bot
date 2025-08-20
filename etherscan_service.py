import requests
from config import Config

class EtherscanService:
    @staticmethod
    def get_gas_prices():
        params = {
            "module": "gastracker",
            "action": "gasoracle",
            "apikey": Config.ETHERSCAN_API_KEY
        }
        
        try:
            response = requests.get(Config.ETHERSCAN_URL, params=params)
            data = response.json()
            
            if data["status"] == "1":
                return {
                    "safe": int(data["result"]["SafeGasPrice"]),
                    "propose": int(data["result"]["ProposeGasPrice"]),
                    "fast": int(data["result"]["FastGasPrice"]),
                    "suggestBaseFee": float(data["result"]["suggestBaseFee"]),
                    "timestamp": int(data["result"]["LastBlock"])
                }
            else:
                raise Exception(f"Etherscan API error: {data['message']}")
        except Exception as e:
            raise Exception(f"Failed to fetch gas prices: {str(e)}")