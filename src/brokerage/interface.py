from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from src.models.brokerage_connection import BrokerageConnection

class BrokerageInterface(ABC):
    """Abstract base class for brokerage adapters."""

    @abstractmethod
    def connect(self, connection: BrokerageConnection) -> bool:
        """Establish connection to the brokerage."""
        pass

    @abstractmethod
    def get_option_chain(self, symbol: str) -> List[Dict]:
        """
        Retrieve option chain data for a given symbol.
        :param symbol: The stock symbol.
        :return: A list of dictionaries, each representing an option contract.
        """
        pass

    @abstractmethod
    def place_order(self, symbol: str, quantity: float, order_type: str, price: Optional[float] = None) -> Dict:
        """
        Place an order for a given symbol.
        :param symbol: The stock symbol.
        :param quantity: The number of shares/contracts.
        :param order_type: Type of order (e.g., 'market', 'limit').
        :param price: Optional limit price for limit orders.
        :return: A dictionary containing order confirmation details.
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict]:
        """
        Retrieve all current positions in the account.
        :return: A list of dictionaries, each representing a position.
        """
        pass

    @abstractmethod
    def get_quotes(self, symbols: List[str]) -> Dict:
        """
        Retrieve current market quotes for specified symbols.
        :param symbols: A list of stock symbols.
        :return: A dictionary where keys are symbols and values are their quotes.
        """
        pass

    @abstractmethod
    def get_orders(self) -> List[Dict]:
        """
        Retrieve all active and historical orders.
        :return: A list of dictionaries, each representing an order.
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.
        :param order_id: The ID of the order to cancel.
        :return: True if cancellation was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_account_balance(self) -> Optional[Dict]:
        """
        Retrieve the current account balance and related details.
        :return: A dictionary containing account balance information, or None if unavailable.
        """
        pass