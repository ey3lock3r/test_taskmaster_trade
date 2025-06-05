from typing import Dict, Optional, List
from .interface import BrokerageInterface
from src.models.brokerage_connection import BrokerageConnection
from src.config import settings
import requests
import base64
import urllib.parse
import json
from datetime import datetime, timedelta

class TradierAdapter(BrokerageInterface):
    """Tradier brokerage adapter implementation."""

    def __init__(self, connection: Optional[BrokerageConnection] = None):
        self._base_url = settings.tradier_base_url
        self._access_token = None
        self._refresh_token = None
        self._token_expiry = None
        self._account_id = settings.tradier_account_id
        self._connection = connection # Store the connection object
        if connection:
            self._access_token = connection.decrypt_access_token()
            self._refresh_token = connection.decrypt_refresh_token()
            # Assuming token_expiry is stored as a string or timestamp in connection
            # For now, we'll assume it's not directly in connection and will be managed internally


    def connect(self, connection: BrokerageConnection) -> bool:
        """Establish connection to the Tradier API using decrypted tokens."""
        self._connection = connection
        self._access_token = connection.decrypt_access_token()
        self._refresh_token = connection.decrypt_refresh_token()

        if not self._access_token:
            print("No access token found. Attempting to refresh or obtain new token.")
            return self.refresh_access_token(connection)

        if self._token_is_expired():
            print("Access token expired. Attempting to refresh.")
            return self.refresh_access_token(connection)

        try:
            headers = self._get_auth_headers()
            response = requests.get(f"{self._base_url}user/profile", headers=headers)
            response.raise_for_status()
            connection.connection_status = "connected"
            connection.last_connected = datetime.now(timezone.utc)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Tradier connection failed: {e}")
            connection.connection_status = "error"
            return False
        except ValueError as e:
            print(f"Tradier connection failed: {e}")
            connection.connection_status = "error"
            return False

    def _get_auth_headers(self) -> Dict:
        if not self._access_token:
            raise ValueError("Access token is not set. Cannot make authenticated request.")
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json"
        }

    def _token_is_expired(self) -> bool:
        # Implement actual token expiry check if Tradier provides expiry time
        # For now, assume tokens might expire and try to refresh if connection fails
        return False # Placeholder, actual implementation would check self._token_expiry

    def refresh_access_token(self, connection: BrokerageConnection) -> bool:
        """
        Refresh the access token using the refresh token.
        """
        if not self._refresh_token:
            print("No refresh token available. Cannot refresh access token.")
            return False

        token_url = "https://api.tradier.com/oauth/accesstoken" # Tradier's token endpoint
        client_id = settings.tradier_client_id
        client_secret = settings.tradier_client_secret

        if not client_id or not client_secret:
            print("Tradier client ID or client secret is missing. Cannot refresh token.")
            return False

        auth_string = f"{client_id}:{client_secret}"
        encoded_auth_string = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

        headers = {
            "Authorization": f"Basic {encoded_auth_string}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token
        }

        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in") # seconds until expiry

            if new_access_token:
                self._access_token = new_access_token
                connection.access_token = new_access_token # Update encrypted token
                if new_refresh_token:
                    self._refresh_token = new_refresh_token
                    connection.refresh_token = new_refresh_token # Update encrypted token
                
                if expires_in:
                    self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                
                connection.connection_status = "connected"
                connection.last_connected = datetime.now(timezone.utc)
                print("Access token refreshed successfully.")
                return True
            else:
                print("Failed to get new access token from refresh response.")
                connection.connection_status = "error"
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error refreshing Tradier access token: {e}")
            connection.connection_status = "error"
            return False

    def get_authorization_url(self, redirect_uri: str) -> str:
        """
        Generates the Tradier OAuth 2.0 authorization URL.
        """
        client_id = settings.tradier_client_id
        if not client_id:
            raise ValueError("Tradier client ID is not configured.")

        params = {
            "client_id": client_id,
            "scope": "read write trade market", # Adjust scopes as needed
            "state": "some_unique_state", # CSRF protection, generate dynamically
            "response_type": "code",
            "redirect_uri": redirect_uri
        }
        query_string = urllib.parse.urlencode(params)
        return f"https://api.tradier.com/oauth/authorize?{query_string}"

    def exchange_code_for_token(self, authorization_code: str, redirect_uri: str) -> Optional[Dict]:
        """
        Exchanges an authorization code for access and refresh tokens.
        """
        token_url = "https://api.tradier.com/oauth/accesstoken"
        client_id = settings.tradier_client_id
        client_secret = settings.tradier_client_secret

        if not client_id or not client_secret:
            raise ValueError("Tradier client ID or client secret is not configured.")

        auth_string = f"{client_id}:{client_secret}"
        encoded_auth_string = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

        headers = {
            "Authorization": f"Basic {encoded_auth_string}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": redirect_uri
        }

        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()

            # Store tokens and expiry
            self._access_token = token_data.get("access_token")
            self._refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")
            if expires_in:
                self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            return token_data
        except requests.exceptions.RequestException as e:
            print(f"Error exchanging code for token: {e}")
            return None

    def get_option_chain(self, symbol: str) -> List[Dict]:
        """
        Retrieve option chain data for a given symbol from Tradier API.
        """
        url = f"{self._base_url}markets/options/chains"
        headers = self._get_auth_headers()
        params = {
            "symbol": symbol
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get('options', {}).get('option', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching option chain for {symbol}: {e}")
            return []

    def place_order(self, symbol: str, quantity: float, order_type: str, price: Optional[float] = None) -> Dict:
        """
        Place an order for a given symbol via Tradier API.
        """
        url = f"{self._base_url}accounts/{self._account_id}/orders"
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = {
            "class": "equity",
            "symbol": symbol,
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
        url = f"{self._base_url}accounts/{self._account_id}/positions"
        headers = self._get_auth_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('positions', {}).get('position', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching positions: {e}")
            return []

    def get_quotes(self, symbols: List[str]) -> Dict:
        """
        Retrieve current market quotes for specified symbols from Tradier API.
        """
        url = f"{self._base_url}markets/quotes"
        headers = self._get_auth_headers()
        params = {
            "symbols": ",".join(symbols)
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            quotes_data = response.json().get('quotes', {}).get('quote', [])
            return {quote['symbol']: quote for quote in quotes_data}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching quotes for {symbols}: {e}")
            return {}

    def get_orders(self) -> List[Dict]:
        """
        Retrieve all active and historical orders from Tradier API.
        """
        url = f"{self._base_url}accounts/{self._account_id}/orders"
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
        url = f"{self._base_url}accounts/{self._account_id}/orders/{order_id}"
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
        url = f"{self._base_url}accounts/{self._account_id}/balances"
        headers = self._get_auth_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('balances', {})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching account balance: {e}")
            return None