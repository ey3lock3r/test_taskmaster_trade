import pytest
from unittest.mock import Mock
from src.strategies.pmcc import PMCCStrategy
from datetime import datetime, date, timedelta

@pytest.fixture
def mock_brokerage():
    """Mock brokerage object for PMCCStrategy."""
    mock = Mock()
    mock.place_order.return_value = {"status": "success", "order_id": "mock_order_123"}
    mock.cancel_order.return_value = True
    mock.get_current_price.return_value = 100.0 # Default mock for current price
    mock.get_quotes.return_value = {"greeks": {"delta": 0.30}} # Default mock for get_quotes
    mock.get_account_balance.return_value = {"equity": 100000.0} # Default mock for account balance
    return mock

@pytest.fixture
def pmcc_parameters():
    """Parameters for PMCCStrategy."""
    return {
        "name": "Test PMCC Strategy",
        "description": "A test strategy for PMCC.",
        "risk_level": "high",
        "target_delta": 0.75,
        "min_dte_long": 90,
        "max_dte_long": 730,
        "min_delta_short": 0.2,
        "max_delta_short": 0.4,
        "max_dte_short": 45,
        "max_net_debit": 1000.0
    }

@pytest.fixture
def mock_option_chain():
    """Mock option chain data."""
    today = date.today()
    long_expiry = (today + timedelta(days=200)).strftime('%Y-%m-%d')
    short_expiry = (today + timedelta(days=5)).strftime('%Y-%m-%d')
 
    return [
        # Long calls (ITM/ATM, long expiry, high delta) - Adjusted for positive net debit
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 90.0, "expirationDate": long_expiry,
            "greeks": {"delta": 0.85}, "bid": 9.5, "ask": 10.0, "type": "equity" # Adjusted ask for positive net debit
        },
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 95.0, "expirationDate": long_expiry,
            "greeks": {"delta": 0.75}, "bid": 5.0, "ask": 5.5, "type": "equity"
        },
        # Short calls (OTM, short expiry, desired delta) - Adjusted for positive net debit and profitability
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 120.0, "expirationDate": short_expiry, # Adjusted strike
            "greeks": {"delta": 0.30}, "bid": 5.0, "ask": 5.2, "type": "equity" # Adjusted bid for positive net debit
        },
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 110.0, "expirationDate": short_expiry,
            "greeks": {"delta": 0.25}, "bid": 0.5, "ask": 0.7, "type": "equity"
        },
        # Invalid options (PUT, wrong expiry, wrong delta)
        {
            "symbol": "SPY", "optionType": "PUT", "strike": 100.0, "expirationDate": long_expiry,
            "greeks": {"delta": -0.5}, "bid": 2.0, "ask": 2.2, "type": "equity"
        },
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 100.0, "expirationDate": (today + timedelta(days=10)).strftime('%Y-%m-%d'),
            "greeks": {"delta": 0.9}, "bid": 3.0, "ask": 3.2, "type": "equity"
        },
    ]

def test_filter_otm_daily_calls(mock_brokerage, pmcc_parameters):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    
    today = date.today()
    # Options for testing OTM and daily expiry
    mock_option_chain_filter = [
        # OTM daily call (should be included)
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 105.0, "expirationDate": (today + timedelta(days=1)).strftime('%Y-%m-%d'),
            "greeks": {"delta": 0.30}, "bid": 1.0, "ask": 1.2, "type": "equity"
        },
        # OTM call, but not daily expiry (should be excluded)
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 105.0, "expirationDate": (today + timedelta(days=30)).strftime('%Y-%m-%d'),
            "greeks": {"delta": 0.30}, "bid": 1.0, "ask": 1.2, "type": "equity"
        },
        # ITM daily call (should be excluded)
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 95.0, "expirationDate": (today + timedelta(days=1)).strftime('%Y-%m-%d'),
            "greeks": {"delta": 0.80}, "bid": 5.0, "ask": 5.5, "type": "equity"
        },
        # PUT option (should be excluded)
        {
            "symbol": "SPY", "optionType": "PUT", "strike": 100.0, "expirationDate": (today + timedelta(days=1)).strftime('%Y-%m-%d'),
            "greeks": {"delta": -0.5}, "bid": 2.0, "ask": 2.2, "type": "equity"
        },
    ]
    
    current_price = 100.0
    filtered_calls = strategy._filter_otm_daily_calls(mock_option_chain_filter, current_price)
    
    assert len(filtered_calls) == 1
    assert filtered_calls[0]['strike'] == 105.0
    assert filtered_calls[0]['expirationDate'] == (today + timedelta(days=1)).strftime('%Y-%m-%d')

def test_select_long_call(mock_brokerage, pmcc_parameters, mock_option_chain):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    long_call = strategy._select_long_call(mock_option_chain)
    assert long_call is not None
    assert long_call['strike'] == 90.0 # Expect the highest delta ITM call

def test_select_short_call(mock_brokerage, pmcc_parameters, mock_option_chain):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    short_call = strategy._select_short_call(mock_option_chain)
    assert short_call is not None
    assert short_call['strike'] == 120.0 # Expect the OTM call with delta 0.30 and short expiry, now with strike 120.0

def test_select_short_call_fetches_greeks_if_missing(mock_brokerage, pmcc_parameters):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    
    today = date.today()
    short_expiry = (today + timedelta(days=5)).strftime('%Y-%m-%d')

    mock_option_chain_missing_greeks = [
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 105.0, "expirationDate": short_expiry,
            "greeks": {}, "bid": 1.0, "ask": 1.2, "type": "equity" # Missing delta
        },
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 110.0, "expirationDate": short_expiry,
            "greeks": {"delta": 0.25}, "bid": 0.5, "ask": 0.7, "type": "equity"
        }
    ]
    
    # Mock get_current_price and get_quotes for the brokerage
    mock_brokerage.get_current_price.return_value = 100.0
    mock_brokerage.get_quotes.return_value = {"greeks": {"delta": 0.30}} # Mocked delta for the first option

    short_call = strategy._select_short_call(mock_option_chain_missing_greeks)
    
    assert short_call is not None
    assert short_call['strike'] == 105.0
    mock_brokerage.get_quotes.assert_called_once_with("SPY") # Verify get_quotes was called

def test_select_short_call_closest_delta(mock_brokerage, pmcc_parameters):
    # Adjust parameters to have a specific target mid-delta
    pmcc_parameters["min_delta_short"] = 0.2
    pmcc_parameters["max_delta_short"] = 0.4
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    
    today = date.today()
    short_expiry_same = (today + timedelta(days=5)).strftime('%Y-%m-%d')

    mock_option_chain_deltas = [
        # OTM daily call, delta 0.22 (closer to 0.2)
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 105.0, "expirationDate": short_expiry_same,
            "greeks": {"delta": 0.22}, "bid": 1.0, "ask": 1.2, "type": "equity"
        },
        # OTM daily call, delta 0.38 (closer to 0.4)
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 106.0, "expirationDate": short_expiry_same,
            "greeks": {"delta": 0.38}, "bid": 0.9, "ask": 1.1, "type": "equity"
        },
        # OTM daily call, delta 0.30 (exactly in the middle)
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 107.0, "expirationDate": short_expiry_same,
            "greeks": {"delta": 0.30}, "bid": 0.8, "ask": 1.0, "type": "equity"
        },
    ]
    
    # mock_brokerage.get_current_price.return_value = 100.0 # Already set in fixture
    
    short_call = strategy._select_short_call(mock_option_chain_deltas)
    
    assert short_call is not None
    assert short_call['strike'] == 107.0 # Expect the one with delta 0.30, as it's exactly in the middle (0.2+0.4)/2 = 0.3

def test_identify_trade_valid(mock_brokerage, pmcc_parameters, mock_option_chain):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    long_call = strategy._select_long_call(mock_option_chain)
    short_call = strategy._select_short_call(mock_option_chain)
    trade = strategy._identify_trade(long_call, short_call, current_price=100.0)

    assert trade is not None
    assert trade['underlying_symbol'] == "SPY"
    assert trade['long_call']['strike'] == 90.0
    assert trade['short_call']['strike'] == 120.0 # Updated to match fixture
    # Calculate expected net debit: (long_ask - short_bid) * 100 = (10.0 - 5.0) * 100 = 500.0
    assert trade['net_debit'] == 500.0
    # Calculate expected breakeven: long_strike + net_debit/100 = 90.0 + 5.0 = 95.0
    assert trade['breakeven'] == 95.0
    assert trade['capital_required'] == 500.0
    assert trade['trade_type'] == 'PMCC'
    assert 'num_contracts' in trade # Ensure num_contracts is present
    assert trade['num_contracts'] > 0 # Ensure a positive number of contracts is calculated

def test_identify_trade_invalid_short_strike_not_higher(mock_brokerage, pmcc_parameters):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    today = date.today()
    long_expiry = (today + timedelta(days=200)).strftime('%Y-%m-%d')
    short_expiry = (today + timedelta(days=5)).strftime('%Y-%m-%d')

    long_call = {"symbol": "SPY", "optionType": "CALL", "strike": 90.0, "expirationDate": long_expiry, "greeks": {"delta": 0.85}, "bid": 10.0, "ask": 10.5}
    # Short call strike is not higher than long call strike
    short_call = {"symbol": "SPY", "optionType": "CALL", "strike": 90.0, "expirationDate": short_expiry, "greeks": {"delta": 0.30}, "bid": 1.0, "ask": 1.2}
    trade = strategy._identify_trade(long_call, short_call, current_price=100.0)
    assert trade is None

def test_identify_trade_invalid_short_expiry_not_earlier(mock_brokerage, pmcc_parameters):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    today = date.today()
    long_expiry = (today + timedelta(days=200)).strftime('%Y-%m-%d')
    # Short call expiry is not earlier than long call expiry
    short_expiry = (today + timedelta(days=200)).strftime('%Y-%m-%d')

    long_call = {"symbol": "SPY", "optionType": "CALL", "strike": 90.0, "expirationDate": long_expiry, "greeks": {"delta": 0.85}, "bid": 10.0, "ask": 10.5}
    short_call = {"symbol": "SPY", "optionType": "CALL", "strike": 105.0, "expirationDate": short_expiry, "greeks": {"delta": 0.30}, "bid": 1.0, "ask": 1.2}
    trade = strategy._identify_trade(long_call, short_call, current_price=100.0)
    assert trade is None

def test_identify_trade_invalid_profitability(mock_brokerage, pmcc_parameters):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    today = date.today()
    long_expiry = (today + timedelta(days=200)).strftime('%Y-%m-%d')
    short_expiry = (today + timedelta(days=5)).strftime('%Y-%m-%d')

    # Make profitability check fail: (short_strike - long_strike) + short_premium <= long_premium
    long_call = {"symbol": "SPY", "optionType": "CALL", "strike": 90.0, "expirationDate": long_expiry, "greeks": {"delta": 0.85}, "bid": 10.0, "ask": 10.5} # Cost of LEAPS = 10.5
    short_call = {"symbol": "SPY", "optionType": "CALL", "strike": 95.0, "expirationDate": short_expiry, "greeks": {"delta": 0.30}, "bid": 0.01, "ask": 0.02} # Short premium = 0.01
    # (95 - 90) + 0.01 = 5.01. This is not > 10.5, so it should fail.
    trade = strategy._identify_trade(long_call, short_call, current_price=100.0)
    assert trade is None

def test_identify_trade_invalid_no_long_call(mock_brokerage, pmcc_parameters):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    short_call = {"symbol": "SPY", "optionType": "CALL", "strike": 105.0, "expirationDate": "2024-06-07", "greeks": {"delta": 0.30}, "bid": 1.0, "ask": 1.2}
    trade = strategy._identify_trade(None, short_call, current_price=100.0)
    assert trade is None

def test_identify_trade_invalid_no_short_call(mock_brokerage, pmcc_parameters):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    long_call = {"symbol": "SPY", "optionType": "CALL", "strike": 90.0, "expirationDate": "2025-01-17", "greeks": {"delta": 0.85}, "bid": 10.0, "ask": 10.5}
    trade = strategy._identify_trade(long_call, None, current_price=100.0)
    assert trade is None

def test_analyze_valid_trade(mock_brokerage, pmcc_parameters, mock_option_chain):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    data = {"option_chain": mock_option_chain, "current_price": 100.0}
    result = strategy.analyze(data)
    assert result is True
    assert strategy.current_trade is not None

def test_analyze_no_trade(mock_brokerage, pmcc_parameters):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    data = {"option_chain": [], "current_price": 100.0} # Empty option chain
    result = strategy.analyze(data)
    assert result is False
    assert strategy.current_trade is None

def test_execute_trade_success(mock_brokerage, pmcc_parameters, mock_option_chain):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    data = {"option_chain": mock_option_chain, "current_price": 100.0}
    strategy.analyze(data) # Identify a trade first

    result = strategy.execute()
    assert result['status'] == 'success'
    from unittest.mock import call
    # Calculate expected number of contracts based on the mock_option_chain fixture values
    # This calculation needs to match the logic in _identify_trade
    long_call_price_fixture = 10.0
    short_call_price_fixture = 5.0
    long_call_strike_fixture = 90.0
    short_call_strike_fixture = 120.0
    net_debit_fixture = (long_call_price_fixture - short_call_price_fixture) * 100 # 500.0
    
    max_profit_per_contract_fixture = (short_call_strike_fixture - long_call_strike_fixture) * 100 - net_debit_fixture # (120-90)*100 - 500 = 3000 - 500 = 2500
    max_loss_per_contract_fixture = net_debit_fixture # 500.0
    win_probability_fixture = 1 - 0.30 # 0.70 (assuming short call delta is 0.30)
    payout_ratio_fixture = max_profit_per_contract_fixture / max_loss_per_contract_fixture # 2500 / 500 = 5.0
    
    from src.position_sizing.kelly import calculate_kelly_percentage, calculate_fractional_kelly, calculate_position_size
    
    full_kelly_percentage_fixture = calculate_kelly_percentage(win_probability_fixture, payout_ratio_fixture) # 0.64
    fractional_kelly_percentage_fixture = calculate_fractional_kelly(full_kelly_percentage_fixture) # 0.64 * 0.618 = 0.39552
    
    # Assuming mock_brokerage.get_account_balance.return_value = {"equity": 100000.0} for this test
    expected_num_contracts_fixture = calculate_position_size(
        total_capital=100000.0, # Use default mock equity
        fractional_kelly_percentage=fractional_kelly_percentage_fixture,
        contract_price=net_debit_fixture # Capital required per contract
    ) # Should be 79
 
    expected_calls = [
        call({
            "symbol": "SPY",
            "quantity": expected_num_contracts_fixture,
            "order_type": "limit",
            "price": mock_option_chain[0]['ask'], # Long call ask
            "option_symbol": mock_option_chain[0]['symbol']
        }),
        call({
            "symbol": "SPY",
            "quantity": expected_num_contracts_fixture,
            "order_type": "limit",
            "price": mock_option_chain[2]['bid'], # Short call bid
            "option_symbol": mock_option_chain[2]['symbol']
        })
    ]
    mock_brokerage.place_order.assert_has_calls(expected_calls)

def test_execute_trade_no_identified_trade(mock_brokerage, pmcc_parameters):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    result = strategy.execute()
    assert result['status'] == 'failed'
    assert "No valid trade identified" in result['message']
    mock_brokerage.place_order.assert_not_called()

def test_execute_trade_long_order_fails(mock_brokerage, pmcc_parameters, mock_option_chain):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    data = {"option_chain": mock_option_chain, "current_price": 100.0}
    strategy.analyze(data)

    mock_brokerage.place_order.side_effect = [
        {"status": "failed", "message": "Long order failed"}, # First call (long order) fails
        {"status": "success", "order_id": "mock_short_order_id"} # Second call (short order) would succeed if reached
    ]

    result = strategy.execute()
    assert result['status'] == 'failed'
    assert "Failed to place long call order" in result['message']
    mock_brokerage.cancel_order.assert_not_called() # No long order to cancel if it failed to place

def test_execute_trade_short_order_fails(mock_brokerage, pmcc_parameters, mock_option_chain):
    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    data = {"option_chain": mock_option_chain, "current_price": 100.0}
    strategy.analyze(data)

    mock_brokerage.place_order.side_effect = [
        {"status": "success", "order_id": "mock_long_order_id"}, # Long order succeeds
        {"status": "failed", "message": "Short order failed"} # Short order fails
    ]

    result = strategy.execute()
    assert result['status'] == 'failed'
    assert "Failed to place short call order" in result['message']
    mock_brokerage.cancel_order.assert_called_once_with("mock_long_order_id") # Long order should be cancelled

def test_pmcc_strategy_with_position_sizing(mock_brokerage, pmcc_parameters, mock_option_chain):
    # Set a specific account balance for this test
    mock_brokerage.get_account_balance.return_value = {"equity": 10000.0}
    
    # Adjust PMCC parameters for a predictable Kelly calculation
    # For simplicity, let's assume a scenario where Kelly bet is easily calculable
    # and results in a reasonable number of contracts.
    # In _identify_trade, we have:
    # win_probability = 1 - short_call.get('greeks', {}).get('delta', 0.5)
    # payout_ratio = max_profit_per_contract / max_loss_per_contract
    # max_profit_per_contract = (short_call_strike - long_call_strike) * 100 - net_debit
    # max_loss_per_contract = net_debit

    # Using mock_option_chain:
    # long_call strike = 90.0, ask = 5.0
    # short_call strike = 105.0, bid = 10.0, delta = 0.30
    # net_debit = (5.0 - 10.0) * 100 = -500.0 (This is actually a credit, should be a debit for PMCC)
    # Let's adjust mock_option_chain to ensure a net debit.
    # Long call ask should be higher than short call bid for a debit spread.
    # Let's assume long_call ask = 10.0, short_call bid = 5.0
    # net_debit = (10.0 - 5.0) * 100 = 500.0

    # Re-mock option chain for this specific test to ensure a net debit and predictable Kelly
    today = date.today()
    long_expiry = (today + timedelta(days=200)).strftime('%Y-%m-%d')
    short_expiry = (today + timedelta(days=5)).strftime('%Y-%m-%d')

    mock_option_chain_adjusted = [
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 90.0, "expirationDate": long_expiry,
            "greeks": {"delta": 0.85}, "bid": 9.5, "ask": 10.0, "type": "equity" # Adjusted ask
        },
        {
            "symbol": "SPY", "optionType": "CALL", "strike": 120.0, "expirationDate": short_expiry, # Adjusted strike
            "greeks": {"delta": 0.30}, "bid": 5.0, "ask": 5.2, "type": "equity" # Adjusted bid
        },
    ]

    # Recalculate expected values based on adjusted mock_option_chain_adjusted
    long_call_price = 10.0
    short_call_price = 5.0
    long_call_strike = 90.0
    short_call_strike = 120.0 # Changed from 105.0
    net_debit = (long_call_price - short_call_price) * 100 # 5.0 * 100 = 500.0

    max_profit_per_contract = (short_call_strike - long_call_strike) * 100 - net_debit # (120-90)*100 - 500 = 3000 - 500 = 2500
    max_loss_per_contract = net_debit # 500.0

    win_probability = 1 - 0.30 # 0.70
    payout_ratio = max_profit_per_contract / max_loss_per_contract # 2500 / 500 = 5.0

    # Kelly formula: (p * b - (1 - p)) / b
    # (0.70 * 5.0 - (1 - 0.70)) / 5.0
    # (3.5 - 0.3) / 5.0 = 3.2 / 5.0 = 0.64
    expected_kelly_fraction = 0.64

    # Expected number of contracts: (available_capital * kelly_fraction) / capital_required
    # (10000 * 0.64) / 500 = 6400 / 500 = 12.8 -> 12 (integer)
    expected_num_contracts = 7 # Corrected based on fractional Kelly calculation

    strategy = PMCCStrategy(mock_brokerage, **pmcc_parameters)
    data = {"option_chain": mock_option_chain_adjusted, "current_price": 100.0}
    
    # Analyze and identify trade
    result_analyze = strategy.analyze(data)
    assert result_analyze is True
    assert strategy.current_trade is not None
    assert strategy.current_trade['num_contracts'] == expected_num_contracts

    # Execute trade and verify quantity
    result_execute = strategy.execute()
    assert result_execute['status'] == 'success'
    
    from unittest.mock import call
    expected_calls = [
        call({
            "symbol": "SPY",
            "quantity": expected_num_contracts,
            "order_type": "limit",
            "price": mock_option_chain_adjusted[0]['ask'],
            "option_symbol": mock_option_chain_adjusted[0]['symbol']
        }),
        call({
            "symbol": "SPY",
            "quantity": expected_num_contracts,
            "order_type": "limit",
            "price": mock_option_chain_adjusted[1]['bid'],
            "option_symbol": mock_option_chain_adjusted[1]['symbol']
        })
    ]
    mock_brokerage.place_order.assert_has_calls(expected_calls)