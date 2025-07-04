from typing import Dict, Optional, List
from .interface import BrokerageInterface
from src.models.brokerage_connection import BrokerageConnection
from src.models.broker import Broker # Import Broker model
from src.utils.redis_utils import redis_client # Import redis_client
import requests
import base64
import urllib.parse
import json
from datetime import datetime, timedelta, timezone

class TradierAdapter(BrokerageInterface):
    """Tradier brokerage adapter implementation."""

    def __init__(self, broker: Broker, connection: BrokerageConnection, _version="v1"):
        self._base_url = broker.base_url
        self._version = _version
        self._connection = connection # Store the connection object

    def connect(self) -> bool:
        """Establish connection to the Tradier API using decrypted tokens."""
        if not self._connection.decrypt_access_token():
            print("No access token found. Attempting to refresh or obtain new token.")
            return self.refresh_access_token()
 
        try:
            headers = self._get_auth_headers()
            response = requests.get(f"{self._base_url}/{self._version}/user/profile", headers=headers)
            response.raise_for_status()
            self._connection.connection_status = "connected"
            self._connection.last_connected = datetime.now(timezone.utc)
            return True
        except requests.exceptions.RequestException as e:
            error_message = f"Tradier connection failed: {e}"
            if e.response is not None:
                error_message += f"\nStatus Code: {e.response.status_code}"
                error_message += f"\nResponse Body: {e.response.text}"
            print(error_message)
            self._connection.connection_status = "error"
            return False
        except ValueError as e:
            print(f"Tradier connection failed: {e}")
            self._connection.connection_status = "error"
            return False
 
    def _get_auth_headers(self) -> Dict:
        # access_token = self._connection.decrypt_access_token()
        access_token = self._connection.decrypted_access_token
        if not access_token:
            raise ValueError("Access token is not set. Cannot make authenticated request.")
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

    async def get_option_chain(self, symbol: str, expiration: str) -> List[Dict]:
        """
        Retrieve option chain data for a given symbol from Tradier API, with Redis caching.
        """
        cache_key = f"option_chain:{symbol}"
        if redis_client:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

        url = f"{self._base_url}/{self._version}/markets/options/chains"
        headers = self._get_auth_headers()
        params = {
            "symbol": symbol,
            "expiration": expiration
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            option_chain_data = response.json().get('options', {}).get('option', [])
            
            if redis_client:
                # Cache for 1 hour (3600 seconds)
                await redis_client.setex(cache_key, 3600, json.dumps(option_chain_data))
            
            return option_chain_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching option chain for {symbol}: {e}")
            return []

    async def place_order(self, symbol: str, quantity: float, order_type: str, order_class: str, duration: str, side: str, price: Optional[float] = None) -> Dict:
        """
        Place an order for a given symbol via Tradier API.
        """
        api_key = self._connection.decrypted_api_key
        url = f"{self._base_url}/{self._version}/accounts/{api_key}/orders"
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = {
            "class": order_class,
            "symbol": symbol,
            "duration": duration,
            "side": side,
            "quantity": quantity,
            "type": order_type,
        }
        if price:
            data["price"] = price

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json().get('order', {})
        except requests.exceptions.RequestException as e:
            print(f"Error placing order for {symbol}: {e}")
            return {}

    def get_positions(self) -> List[Dict]:
        """
        Retrieve all current positions in the account from Tradier API.
        """
        api_key = self._connection.decrypted_api_key
        url = f"{self._base_url}/{self._version}/accounts/{api_key}/positions"
        headers = self._get_auth_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('positions', {}).get('position', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching positions: {e}")
            return []

    async def get_quotes(self, symbols: List[str]) -> Dict:
        """
        Retrieve current market quotes for specified symbols from Tradier API, with Redis caching.
        """
        symbols_str = ",".join(symbols)
        cache_key = f"quotes:{symbols_str}"
        if redis_client:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

        url = f"{self._base_url}/{self._version}/markets/quotes"
        headers = self._get_auth_headers()
        params = {
            "symbols": symbols_str
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            quotes_data = response.json().get('quotes', {}).get('quote', [])
            quotes_dict = {quote['symbol']: quote for quote in quotes_data}
            
            if redis_client:
                # Cache for 5 minutes (300 seconds)
                await redis_client.setex(cache_key, 300, json.dumps(quotes_dict))
            
            return quotes_dict
        except requests.exceptions.RequestException as e:
            print(f"Error fetching quotes for {symbols}: {e}")
            return {}

    def get_orders(self) -> List[Dict]:
        """
        Retrieve all active and historical orders from Tradier API.
        """
        api_key = self._connection.decrypted_api_key
        url = f"{self._base_url}/{self._version}/accounts/{api_key}/orders"
        headers = self._get_auth_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('orders', {}).get('order', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching orders: {e}")
            return []

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order via Tradier API.
        """
        api_key = self._connection.decrypted_api_key
        url = f"{self._base_url}/{self._version}/accounts/{api_key}/orders/{order_id}"
        headers = self._get_auth_headers()
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            return response.json().get('order', {}).get('status') == 'ok'
        except requests.exceptions.RequestException as e:
            print(f"Error canceling order {order_id}: {e}")
            return False

    def get_account_balance(self) -> Optional[Dict]:
        """
        Retrieve the current account balance and related details from Tradier API.
        """
        api_key = self._connection.decrypted_api_key
        url = f"{self._base_url}/{self._version}/accounts/{api_key}/balances"
        headers = self._get_auth_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('balances', {})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching account balance: {e}")
            return None