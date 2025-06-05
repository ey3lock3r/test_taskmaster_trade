import pytest
from src.position_sizing.kelly import (
    validate_input_parameters,
    calculate_kelly_percentage,
    calculate_fractional_kelly,
    calculate_position_size,
    GOLDEN_RATIO
)

def test_validate_input_parameters():
    # Test valid inputs
    validate_input_parameters(0.5, 2.0)
    validate_input_parameters(0.0, 0.1)
    validate_input_parameters(1.0, 100.0)

    # Test invalid win_probability
    with pytest.raises(ValueError, match="Win probability must be between 0 and 1."):
        validate_input_parameters(-0.1, 2.0)
    with pytest.raises(ValueError, match="Win probability must be between 0 and 1."):
        validate_input_parameters(1.1, 2.0)

    # Test invalid win_loss_ratio
    with pytest.raises(ValueError, match="Win/loss ratio must be positive."):
        validate_input_parameters(0.5, 0.0)
    with pytest.raises(ValueError, match="Win/loss ratio must be positive."):
        validate_input_parameters(0.5, -1.0)

def test_calculate_kelly_percentage():
    # Test cases with positive edge
    assert calculate_kelly_percentage(0.6, 1.5) == pytest.approx(0.3333333333333333)
    assert calculate_kelly_percentage(0.7, 2.0) == pytest.approx(0.55)
    assert calculate_kelly_percentage(0.5, 1.0) == pytest.approx(0.0) # No edge, should be 0

    # Test cases with negative edge (should return 0)
    assert calculate_kelly_percentage(0.4, 1.5) == pytest.approx(0.0)
    assert calculate_kelly_percentage(0.3, 0.5) == pytest.approx(0.0)

    # Test boundary values for win_probability
    assert calculate_kelly_percentage(0.0, 2.0) == pytest.approx(0.0)
    assert calculate_kelly_percentage(1.0, 2.0) == pytest.approx(1.0)

    # Test boundary values for win_loss_ratio (already handled by validate_input_parameters)
    # These tests assume validate_input_parameters is called before, so only valid ratios are passed.
    assert calculate_kelly_percentage(0.6, 0.0001) == pytest.approx(0.0) # Very low ratio, likely negative Kelly
    assert calculate_kelly_percentage(0.6, 10000.0) == pytest.approx(0.59996) # Very high ratio, close to win_probability

def test_calculate_fractional_kelly():
    # Test with positive full Kelly percentage
    assert calculate_fractional_kelly(0.2666666666666666) == pytest.approx(0.2666666666666666 * GOLDEN_RATIO)
    assert calculate_fractional_kelly(0.45) == pytest.approx(0.45 * GOLDEN_RATIO)
    assert calculate_fractional_kelly(0.0) == pytest.approx(0.0)
    assert calculate_fractional_kelly(1.0) == pytest.approx(1.0 * GOLDEN_RATIO)

    # Test with negative full Kelly percentage (should raise ValueError)
    with pytest.raises(ValueError, match="Full Kelly percentage cannot be negative."):
        calculate_fractional_kelly(-0.1)

def test_calculate_position_size():
    # Test basic calculation
    # total_capital = 10000, fractional_kelly = 0.1, contract_price = 100
    # capital_to_allocate = 10000 * 0.1 = 1000
    # num_contracts = 1000 / 100 = 10
    assert calculate_position_size(10000, 0.1, 100) == 10

    # Test with fractional contracts (should round down)
    # capital_to_allocate = 10000 * 0.05 = 500
    # num_contracts = 500 / 120 = 4.16 -> 4
    assert calculate_position_size(10000, 0.05, 120) == 4

    # Test with max_position_percentage
    # capital_to_allocate = 10000 * 0.2 = 2000
    # max_capital_for_position = 10000 * 0.15 = 1500
    # min(2000, 1500) = 1500
    # num_contracts = 1500 / 100 = 15
    assert calculate_position_size(10000, 0.2, 100, max_position_percentage=0.15) == 15

    # Test edge cases for inputs
    with pytest.raises(ValueError, match="Total capital must be positive."):
        calculate_position_size(0, 0.1, 100)
    with pytest.raises(ValueError, match="Total capital must be positive."):
        calculate_position_size(-100, 0.1, 100)

    with pytest.raises(ValueError, match="Fractional Kelly percentage must be between 0 and 1."):
        calculate_position_size(10000, -0.1, 100)
    with pytest.raises(ValueError, match="Fractional Kelly percentage must be between 0 and 1."):
        calculate_position_size(10000, 1.1, 100)

    with pytest.raises(ValueError, match="Contract price must be positive."):
        calculate_position_size(10000, 0.1, 0)
    with pytest.raises(ValueError, match="Contract price must be positive."):
        calculate_position_size(10000, 0.1, -10)

    with pytest.raises(ValueError, match="Max position percentage must be between 0 and 1."):
        calculate_position_size(10000, 0.1, 100, max_position_percentage=-0.1)
    with pytest.raises(ValueError, match="Max position percentage must be between 0 and 1."):
        calculate_position_size(10000, 0.1, 100, max_position_percentage=1.1)

    # Test zero contract price (should raise ValueError as per validation)
    with pytest.raises(ValueError, match="Contract price must be positive."):
        calculate_position_size(10000, 0.1, 0)