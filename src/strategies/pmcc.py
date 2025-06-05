from typing import Dict, List, Optional, Any
from datetime import datetime, date
from .base import Strategy
from src.position_sizing.kelly import calculate_kelly_percentage, calculate_position_size, calculate_fractional_kelly
from src.config import settings

class PMCCStrategy(Strategy):
    """Poor Man's Covered Call trading strategy implementation."""

    def __init__(self, brokerage,
                 name: str = "PMCC Strategy",
                 description: str = "Poor Man's Covered Call trading strategy implementation.",
                 risk_level: str = "medium",
                 target_delta: float = 0.75,
                 min_dte_long: int = 90,
                 max_dte_long: int = 730, # 2 years
                 min_delta_short: float = 0.2,
                 max_delta_short: float = 0.4,
                 max_dte_short: int = 45,
                 max_net_debit: float = 500.0,
                 risk_free_rate: float = 0.05): # Default risk-free rate
        super().__init__(name, description, risk_level)
        self.brokerage = brokerage
        self._target_delta = target_delta
        self._min_dte_long = min_dte_long
        self._max_dte_long = max_dte_long
        self._min_delta_short = min_delta_short
        self._max_delta_short = max_delta_short
        self._max_dte_short = max_dte_short
        self._max_net_debit = max_net_debit
        self._risk_free_rate = risk_free_rate
        self.current_trade = None
        self.load_parameters_from_config()

    def analyze(self, data: Dict) -> bool:
        """
        Analyze if PMCC conditions are met.
        :param data: Dictionary containing market data, including 'option_chain' and 'current_price'.
        """
        option_chain = data.get('option_chain')
        current_price = data.get('current_price')

        if not option_chain or not current_price:
            return False

        long_call = self._select_long_call(option_chain)
        short_call = self._select_short_call(option_chain)

        if long_call and short_call:
            trade = self._identify_trade(long_call, short_call, current_price)
            if trade:
                self.current_trade = trade
                return True
        self.current_trade = None
        return False

    def execute(self) -> Dict:
        """
        Execute PMCC strategy.
        Places the long and short call orders if a valid trade has been identified.
        """
        if not hasattr(self, 'current_trade') or not self.current_trade:
            return {"status": "failed", "message": "No valid trade identified to execute."}

        num_contracts = self.current_trade.get('num_contracts', 1) # Default to 1 if not calculated
        
        long_call_order_params = {
            "symbol": self.current_trade['underlying_symbol'],
            "quantity": num_contracts,
            "order_type": "limit",
            "price": self.current_trade['long_call']['ask'],
            "option_symbol": self.current_trade['long_call']['symbol']
        }
 
        short_call_order_params = {
            "symbol": self.current_trade['underlying_symbol'],
            "quantity": num_contracts,
            "order_type": "limit",
            "price": self.current_trade['short_call']['bid'],
            "option_symbol": self.current_trade['short_call']['symbol']
        }

        try:
            long_order_result = self.brokerage.place_order(long_call_order_params)
            if long_order_result.get('status') != 'success':
                return {"status": "failed", "message": "Failed to place long call order.", "details": long_order_result}

            short_order_result = self.brokerage.place_order(short_call_order_params)
            if short_order_result.get('status') != 'success':
                self.brokerage.cancel_order(long_order_result.get('order_id'))
                return {"status": "failed", "message": "Failed to place short call order.", "details": short_order_result}

            return {
                "status": "success",
                "message": "PMCC trade executed successfully.",
                "long_order": long_order_result,
                "short_order": short_order_result,
                "trade_details": self.current_trade
            }
        except Exception as e:
            return {"status": "error", "message": f"An error occurred during trade execution: {str(e)}"}

    def validate(self) -> bool:
        """
        Validate the PMCC strategy's parameters.
        """
        if not (0 <= self._target_delta <= 1):
            print("Validation Error: target_delta must be between 0 and 1.")
            return False
        if not (self._min_dte_long > 0 and self._max_dte_long >= self._min_dte_long):
            print("Validation Error: min_dte_long must be positive and max_dte_long must be >= min_dte_long.")
            return False
        if not (0 <= self._min_delta_short <= 1 and 0 <= self._max_delta_short <= 1 and self._max_delta_short >= self._min_delta_short):
            print("Validation Error: short call deltas must be between 0 and 1 and max_delta_short >= min_delta_short.")
            return False
        if not (self._max_dte_short > 0):
            print("Validation Error: max_dte_short must be positive.")
            return False
        if not (self._max_net_debit > 0):
            print("Validation Error: max_net_debit must be positive.")
            return False
        return True

    def get_parameters(self) -> Dict[str, Any]:
        """
        Get the current parameters of the PMCC strategy.
        """
        return {
            "name": self.name,
            "description": self.description,
            "risk_level": self.risk_level,
            "target_delta": self._target_delta,
            "min_dte_long": self._min_dte_long,
            "max_dte_long": self._max_dte_long,
            "min_delta_short": self._min_delta_short,
            "max_delta_short": self._max_delta_short,
            "max_dte_short": self._max_dte_short,
            "max_net_debit": self._max_net_debit,
            "risk_free_rate": self._risk_free_rate
        }

    def set_parameters(self, parameters: Dict[str, Any]):
        """
        Set the parameters for the PMCC strategy.
        """
        if "name" in parameters:
            self._name = parameters["name"]
        if "description" in parameters:
            self._description = parameters["description"]
        if "risk_level" in parameters:
            self._risk_level = parameters["risk_level"]
        if "target_delta" in parameters:
            self._target_delta = parameters["target_delta"]
        if "min_dte_long" in parameters:
            self._min_dte_long = parameters["min_dte_long"]
        if "max_dte_long" in parameters:
            self._max_dte_long = parameters["max_dte_long"]
        if "min_delta_short" in parameters:
            self._min_delta_short = parameters["min_delta_short"]
        if "max_delta_short" in parameters:
            self._max_delta_short = parameters["max_delta_short"]
        if "max_dte_short" in parameters:
            self._max_dte_short = parameters["max_dte_short"]
        if "max_net_debit" in parameters:
            self._max_net_debit = parameters["max_net_debit"]
        if "risk_free_rate" in parameters:
            self._risk_free_rate = parameters["risk_free_rate"]
        if not self.validate():
            print("Warning: Parameters set but validation failed. Check parameters.")

    def load_parameters_from_config(self):
        """
        Load strategy parameters from the application settings.
        This method is called on initialization to ensure the strategy uses
        the latest configured parameters.
        """
        self._target_delta = settings.pmcc_target_delta
        self._min_dte_long = settings.pmcc_min_dte_long
        self._max_dte_long = settings.pmcc_max_dte_long
        self._min_delta_short = settings.pmcc_min_delta_short
        self._max_delta_short = settings.pmcc_max_delta_short
        self._max_dte_short = settings.pmcc_max_dte_short
        self._max_net_debit = settings.pmcc_max_net_debit
        self._risk_free_rate = settings.pmcc_risk_free_rate

    def _select_long_call(self, option_chain: List[Dict]) -> Optional[Dict]:
        """
        Selects the appropriate long call option based on PMCC strategy criteria.
        """
        long_calls = []
        for option in option_chain:
            if option.get('optionType') == 'CALL':
                delta = option.get('greeks', {}).get('delta')
                if delta is None:
                    continue

                try:
                    expiration_date = datetime.strptime(option.get('expirationDate'), '%Y-%m-%d').date()
                    today = datetime.now().date()
                    days_to_expiry = (expiration_date - today).days
                except (ValueError, TypeError):
                    continue

                if delta >= self._target_delta and \
                   self._min_dte_long <= days_to_expiry <= self._max_dte_long:
                    long_calls.append(option)

        long_calls.sort(key=lambda x: x.get('delta', 0), reverse=True)
        return long_calls[0] if long_calls else None

    def _select_short_call(self, option_chain: List[Dict]) -> Optional[Dict]:
        """
        Selects the appropriate short call option based on PMCC strategy criteria.
        """
        # First, filter for OTM daily calls using the new helper method
        current_price = self.brokerage.get_current_price(option_chain[0]['symbol']) # Assuming symbol is consistent
        if not current_price:
            return None
            
        otm_daily_calls = self._filter_otm_daily_calls(option_chain, current_price)

        short_calls = []
        for option in otm_daily_calls: # Iterate over the pre-filtered options
            delta = option.get('greeks', {}).get('delta')
            
            # If delta is not available, attempt to fetch quotes for the option
            if delta is None:
                try:
                    quote_data = self.brokerage.get_quotes(option.get('symbol'))
                    if quote_data and 'greeks' in quote_data:
                        delta = quote_data['greeks'].get('delta')
                        # Update the option dictionary with the fetched delta
                        option.setdefault('greeks', {})['delta'] = delta
                except Exception as e:
                    print(f"Error fetching quotes for {option.get('symbol')}: {e}")
                    
            if delta is None: # If delta is still None after attempting to fetch, skip
                continue

            try:
                expiration_date = datetime.strptime(option.get('expirationDate'), '%Y-%m-%d').date()
                today = datetime.now().date()
                days_to_expiry = (expiration_date - today).days
            except (ValueError, TypeError):
                continue

            if self._min_delta_short <= delta <= self._max_delta_short and \
               days_to_expiry <= self._max_dte_short:
                short_calls.append(option)

        target_mid_delta = (self._min_delta_short + self._max_delta_short) / 2
        
        short_calls.sort(key=lambda x: (x.get('expirationDate', '9999-12-31'), abs(x.get('greeks', {}).get('delta', 0) - target_mid_delta)))
        return short_calls[0] if short_calls else None

    def _filter_otm_daily_calls(self, option_chain: List[Dict], current_price: float) -> List[Dict]:
        """
        Filters the option chain for out-of-the-money (OTM) call options with daily expiry.
        """
        otm_daily_calls = []
        today = datetime.now().date()
        
        # Group options by expiration date
        options_by_expiry = {}
        for option in option_chain:
            if option.get('optionType') == 'CALL' and option.get('strike') > current_price:
                try:
                    expiration_date_str = option.get('expirationDate')
                    expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
                    
                    # Check for daily expiry (e.g., next few days, or specific pattern)
                    # For MVP, let's consider options expiring within the next 7 days as 'daily'
                    # This can be refined based on brokerage data for actual 'daily' contracts
                    if 0 <= (expiration_date - today).days <= 7: # Adjust this range as needed for 'daily'
                        if expiration_date_str not in options_by_expiry:
                            options_by_expiry[expiration_date_str] = []
                        options_by_expiry[expiration_date_str].append(option)
                except (ValueError, TypeError):
                    continue
        
        # Find the nearest daily expiry and collect options for that date
        if options_by_expiry:
            nearest_expiry_date = min(options_by_expiry.keys())
            otm_daily_calls = options_by_expiry[nearest_expiry_date]
        return otm_daily_calls
 
    def _identify_trade(self, long_call: Dict, short_call: Dict, current_price: float) -> Optional[Dict]:
        """
        Identifies a valid PMCC trade by combining selected long and short calls,
        ensuring all strategy constraints and risk checks are met, and determines
        position size using the Kelly criterion.
        """
        if not long_call or not short_call:
            return None

        if long_call.get('optionType') != 'CALL' or short_call.get('optionType') != 'CALL':
            return None
        if long_call.get('symbol') != short_call.get('symbol'):
            return None

        try:
            long_call_price = long_call.get('ask')
            short_call_price = short_call.get('bid')
            long_call_strike = long_call.get('strike')
            short_call_strike = short_call.get('strike')
            
            long_call_expiration_str = long_call.get('expirationDate')
            short_call_expiration_str = short_call.get('expirationDate')

            if None in [long_call_price, short_call_price, long_call_strike, short_call_strike,
                        long_call_expiration_str, short_call_expiration_str]:
                return None

            try:
                long_call_expiration = datetime.strptime(long_call_expiration_str, '%Y-%m-%d').date()
                short_call_expiration = datetime.strptime(short_call_expiration_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return None

            # Validation 1: Short call strike must be higher than long call strike
            if short_call_strike <= long_call_strike:
                print(f"Validation Failed: Short call strike ({short_call_strike}) <= Long call strike ({long_call_strike})")
                return None
 
            # Validation 2: Short call expiration must be earlier than long call expiration
            if short_call_expiration >= long_call_expiration:
                print(f"Validation Failed: Short call expiration ({short_call_expiration}) >= Long call expiration ({long_call_expiration})")
                return None
 
            net_debit = (long_call_price - short_call_price) * 100
            breakeven = long_call_strike + (net_debit / 100)
 
            capital_required = net_debit
 
            # Validation 3: Profitability check
            # [(Short call strike – LEAPS strike) + short call premium] > Cost of LEAPS option
            # Note: 'premium' here refers to the price received for selling the short call,
            # and 'cost of LEAPS' refers to the price paid for the long call.
            profitability_check = ((short_call_strike - long_call_strike) * 100) + (short_call_price * 100) > (long_call_price * 100)
            print(f"Debug: long_call_price={long_call_price}, short_call_price={short_call_price}")
            print(f"Debug: long_call_strike={long_call_strike}, short_call_strike={short_call_strike}")
            print(f"Debug: net_debit={net_debit}")
            print(f"Debug: profitability_check={profitability_check}")
            print(f"Debug: capital_required={capital_required}, _max_net_debit={self._max_net_debit}")

            if not profitability_check:
                print("Validation Failed: Profitability check failed.")
                return None
 
            if capital_required > self._max_net_debit:
                print(f"Validation Failed: Capital required ({capital_required}) > Max net debit ({self._max_net_debit})")
                return None

            # Fetch available capital
            account_balance = self.brokerage.get_account_balance()
            if not account_balance or 'equity' not in account_balance:
                print("Could not retrieve account balance for position sizing.")
                return None
            
            available_capital = account_balance['equity'] # Use total equity for now

            # Calculate Kelly Bet
            # Win probability (p) can be estimated by the probability of the short call expiring OTM.
            # This is roughly 1 - delta of the short call.
            win_probability = 1 - short_call.get('greeks', {}).get('delta', 0.5) # Rough estimate

            # Payout ratio (b) = (Max Profit / Max Loss)
            # Max Profit = (short_call_strike - long_call_strike) * 100 - net_debit
            # Max Loss = net_debit
            
            max_profit_per_contract = (short_call_strike - long_call_strike) * 100 - net_debit
            max_loss_per_contract = net_debit

            if max_loss_per_contract <= 0: # Avoid division by zero or negative loss
                print("Max loss per contract is zero or negative, cannot calculate Kelly bet.")
                return None

            payout_ratio = max_profit_per_contract / max_loss_per_contract if max_loss_per_contract > 0 else 0.1 # Default to 0.1 if no profit

            if win_probability <= 0 or payout_ratio <= 0:
                print("Invalid win probability or payout ratio for Kelly calculation.")
                return None

            # Use the Kelly formula to determine the fraction of capital to bet
            full_kelly_percentage = calculate_kelly_percentage(win_probability, payout_ratio)
            fractional_kelly_percentage = calculate_fractional_kelly(full_kelly_percentage)
            
            if fractional_kelly_percentage <= 0:
                print("Fractional Kelly percentage is zero or negative, not placing trade.")
                return None

            # Calculate the number of contracts based on Kelly fraction and capital required per contract
            # Each contract of PMCC requires 'net_debit' capital.
            # Total capital to allocate = available_capital * fractional_kelly_percentage
            # Number of contracts = (available_capital * fractional_kelly_percentage) / capital_required
            
            # Ensure capital_required is not zero to avoid division by zero
            if capital_required == 0:
                print("Capital required per contract is zero, cannot determine number of contracts.")
                return None

            # The number of contracts should be an integer
            num_contracts = calculate_position_size(
                total_capital=available_capital,
                fractional_kelly_percentage=fractional_kelly_percentage,
                contract_price=capital_required # Here, contract_price is the capital required per contract
            )
            
            if num_contracts <= 0:
                print("Calculated number of contracts is zero or negative, not placing trade.")
                return None

            trade = {
                'underlying_symbol': long_call.get('symbol'),
                'long_call': long_call,
                'short_call': short_call,
                'net_debit': net_debit,
                'breakeven': breakeven,
                'capital_required': capital_required,
                'trade_type': 'PMCC',
                'num_contracts': num_contracts # Add the calculated number of contracts
            }
            return trade

        except (TypeError, ValueError):
            return None

    def _calculate_intrinsic_extrinsic_value(self, option: Dict, current_price: float) -> Dict:
        """
        Calculates the intrinsic and extrinsic value of an option.
        """
        option_type = option.get('type')
        strike = option.get('strike')
        last_price = option.get('last')

        if option_type == 'call':
            intrinsic_value = max(0, current_price - strike)
        elif option_type == 'put':
            intrinsic_value = max(0, strike - current_price)
        else:
            intrinsic_value = 0

        extrinsic_value = max(0, last_price - intrinsic_value) if last_price is not None else 0

        return {
            "intrinsic_value": intrinsic_value,
            "extrinsic_value": extrinsic_value
        }