from utils.power_plant import StoragePowerPlant
import pandas as pd
import pytest


def test_plant_init():
    plant = StoragePowerPlant(power=10.0, capacity=15.0, upper_limit=0.9, lower_limit=0.1)
    assert plant.flexibility == pytest.approx(15.0 * 0.9 - 15.0 * 0.1)


def test_charge_calc_profit_arithmetic():
    plant = StoragePowerPlant(efficiency=0.9, degradation=5.0, capacity=15.0, lower_limit=0.1, upper_limit=0.9)
    test_df = pd.DataFrame()
    test_df["price_eur_mwh"] = [100, 100, 100, 100, 100, 100]
    test_df["Loading"] = [0, 1, 1, -1, -1, 0]

    result = plant._calculate_charge(test_df)

    ## Check result against hand-computed values
    expected_cost = 2 * (100 * 1 / 4)
    expected_revenue = 2 * (0.9 * 100 * 1 / 4)
    expected_degradation = 4 * (5.0 * 1 / 4)

    assert result["power_cost"].sum() == pytest.approx(expected_cost)
    assert result["power_revenue"].sum() == pytest.approx(expected_revenue)
    assert result["degradation_cost"].sum() == pytest.approx(expected_degradation)
    assert result["total_profit"].sum() == pytest.approx(
        expected_revenue - expected_cost - expected_degradation
    )


def test_correct_charges():
    plant = StoragePowerPlant()
    test_df = pd.DataFrame()

    ## Create time series of cheap and expensive steps
    test_df["price_eur_mwh"] = [100, 0, 0, 100, 0, 0, 100, 0, 0, 100, 0, 0, 100, 0, 0]

    result = plant.process_day(test_df, "Single Cycle")

    ## Chargins should only occur at the cheap spots
    expensive = result["price_eur_mwh"] == 100

    assert (result.loc[expensive, "Loading"] <= 0).all()
    assert result["Loading"].sum() == pytest.approx(0.0)


def test_single_cycle_no_last_ts_charge():
    plant = StoragePowerPlant()
    test_df = pd.DataFrame()

    ## Create time series in which the cheapest price is at end
    test_df["price_eur_mwh"] = [50, 40, 30, 20, 10, 0]

    result = plant.process_day(test_df, "Single Cycle")

    ## Charging should not occur in the last step
    assert result["Loading"].iloc[-1] == 0
    assert result["Loading"].sum() == pytest.approx(0.0)


def test_single_cycle_handles_partial_interval():
    plant = StoragePowerPlant()
    test_df = pd.DataFrame()

    ## Create strictly increasing price development
    test_df["price_eur_mwh"] = list(range(0, 24, 2))

    result = plant.process_day(test_df, "Single Cycle")

    ## Charging should only occur on the five cheapest timesteps
    cheapest_five = set(test_df.sort_values("price_eur_mwh").index[:5])
    charged = result.index[result["Loading"] > 0]
    assert set(charged).issubset(cheapest_five)


def test_optim_single():
    plant = StoragePowerPlant()
    test_df = pd.DataFrame()
    test_df["price_eur_mwh"] = [100, 0, 0, 100, 0, 0, 100, 0, 0, 100, 0, 0, 100, 0, 0]
    result_single_cycle = plant.process_day(test_df, "Single Cycle")

    assert result_single_cycle["Loading"].sum() == pytest.approx(0.0)


def test_optimal_within_capacity_bounds():
    plant = StoragePowerPlant()
    test_df = pd.DataFrame()
    test_df["price_eur_mwh"] = [100, 0, 0, 100, 0, 0, 100, 0, 0, 100, 0, 0, 100, 0, 0]

    result = plant.process_day(test_df, "Optimal")

    ## Check that optimizer stays within capacity and returns to 0
    assert result["current_charge"].max() <= plant.capacity * plant.upper_limit + 1e-6
    assert result["current_charge"].min() >= plant.capacity * plant.lower_limit - 1e-6
    assert result["Loading"].sum() == pytest.approx(0.0)


def test_optimal_no_cycling_when_prices_flat():
    plant = StoragePowerPlant()
    test_df = pd.DataFrame()
    test_df["price_eur_mwh"] = [50] * 12

    result = plant.process_day(test_df, "Optimal")

    # With flat prices, any cycling only pays degradation cost for no gain.
    assert result["Loading"].abs().sum() == pytest.approx(0.0, abs=1e-6)
