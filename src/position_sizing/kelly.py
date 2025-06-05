def validate_input_parameters(win_probability: float, win_loss_ratio: float):
    """
    Validates input parameters for Kelly Criterion calculations.

    Args:
        win_probability: The probability of a winning trade (W).
        win_loss_ratio: The ratio of average win to average loss (R).

    Raises:
        ValueError: If input parameters are out of valid range.
    """
    if not (0 <= win_probability <= 1):
        raise ValueError("Win probability must be between 0 and 1.")
    if win_loss_ratio <= 0:
        raise ValueError("Win/loss ratio must be positive.")

GOLDEN_RATIO = 0.618

def calculate_kelly_percentage(win_probability: float, win_loss_ratio: float) -> float:
    """
    Calculates the optimal Kelly percentage based on win probability and win/loss ratio.

    Args:
        win_probability: The probability of a winning trade (W). Must be between 0 and 1.
        win_loss_ratio: The ratio of average win to average loss (R). Must be positive.

    Returns:
        The optimal Kelly percentage (K%). Returns 0 if the formula results in a negative value.

    Raises:
        ValueError: If input parameters are out of valid range.
    """
    validate_input_parameters(win_probability, win_loss_ratio)

    # Kelly formula: K% = W - [(1-W)/R]
    kelly_percentage = win_probability - ((1 - win_probability) / win_loss_ratio)

    # If Kelly percentage is negative, it means no edge, so no position should be taken.
    return max(0.0, kelly_percentage)

def calculate_fractional_kelly(full_kelly_percentage: float) -> float:
    """
    Applies the Golden Ratio as a fractional multiplier to the full Kelly percentage.

    Args:
        full_kelly_percentage: The optimal Kelly percentage calculated from calculate_kelly_percentage.

    Returns:
        The fractional Kelly percentage.
    """
    if full_kelly_percentage < 0:
        raise ValueError("Full Kelly percentage cannot be negative.")
    return full_kelly_percentage * GOLDEN_RATIO

def calculate_position_size(
    total_capital: float,
    fractional_kelly_percentage: float,
    contract_price: float,
    max_position_percentage: float = 1.0
) -> int:
    """
    Calculates the recommended number of contracts to trade based on fractional Kelly percentage.

    Args:
        total_capital: The total capital available for trading. Must be positive.
        fractional_kelly_percentage: The fractional Kelly percentage. Must be between 0 and 1.
        contract_price: The price of one contract. Must be positive.
        max_position_percentage: The maximum percentage of capital to risk on a single position.
                                 Defaults to 1.0 (100%).

    Returns:
        The recommended number of contracts (integer).

    Raises:
        ValueError: If input parameters are out of valid range.
    """
    if total_capital <= 0:
        raise ValueError("Total capital must be positive.")
    if not (0 <= fractional_kelly_percentage <= 1):
        raise ValueError("Fractional Kelly percentage must be between 0 and 1.")
    if contract_price <= 0:
        raise ValueError("Contract price must be positive.")
    if not (0 <= max_position_percentage <= 1):
        raise ValueError("Max position percentage must be between 0 and 1.")

    # Calculate the capital to allocate based on fractional Kelly
    capital_to_allocate = total_capital * fractional_kelly_percentage

    # Apply maximum position size limit
    max_capital_for_position = total_capital * max_position_percentage
    capital_to_allocate = min(capital_to_allocate, max_capital_for_position)

    # Calculate number of contracts
    if contract_price == 0: # Avoid division by zero
        return 0
    num_contracts = capital_to_allocate / contract_price

    # Round down to the nearest whole contract
    return int(num_contracts)