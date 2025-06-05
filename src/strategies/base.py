from abc import ABC, abstractmethod
from typing import Dict, List, Any

class Strategy(ABC):
    """Base class for trading strategies."""

    def __init__(self, name: str, description: str, risk_level: str):
        self._name = name
        self._description = description
        self._risk_level = risk_level

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def risk_level(self) -> str:
        return self._risk_level

    @abstractmethod
    def analyze(self, data: Dict) -> bool:
        """Analyze market data and determine if trade should be executed."""
        pass

    @abstractmethod
    def execute(self) -> Dict:
        """Execute the trading strategy."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the strategy's parameters and state."""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get the current parameters of the strategy."""
        pass

    @abstractmethod
    def set_parameters(self, parameters: Dict[str, Any]):
        """Set the parameters for the strategy."""
        pass