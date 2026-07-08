from scipy.optimize import linprog
import pandas as pd
import numpy as np
import math


def single_cycle(plant, day_data: pd.DataFrame):
    """
    Calculates a Loading pattern based on a greedy single-cycle approach.

    Args:
        plant: StoragePowerPlant to run the simulation on
        day_data: DataFrame with column "price_eur_mwh", sorted by timestamp

    Returns:
        data: DataFrame, copy of day_data with column "Loading" added
    """
    data = day_data.copy()
    data["Loading"] = 0.0
    ## Calculate intervals needed for charging
    interval_energy = plant.power / 4  # Energy per 15-min interval
    required_intervals = plant.flexibility / interval_energy
    full_power_intervals = math.floor(required_intervals)
    partial_power_interval = required_intervals % 1

    ## Find cheapest times to charge
    price_sorted = data.sort_values("price_eur_mwh")
    charge_indices = []
    for i in range(full_power_intervals):
        idx = price_sorted.index[i]
        data.loc[idx, "Loading"] = interval_energy
        charge_indices.append(idx)

    if partial_power_interval > 0:
        partial_power_idx = price_sorted.index[full_power_intervals]
        data.loc[partial_power_idx, "Loading"] = (
            partial_power_interval * interval_energy
        )

    ## Find most profitable times to discharge
    price_sorted_desc = data.sort_values("price_eur_mwh", ascending=False)
    used_for_discharge = set()

    # For each charge time, find the best later discharge time
    for charge_idx in charge_indices:
        # Find the most expensive later time
        later_times = price_sorted_desc[
            (price_sorted_desc.index > charge_idx)
            & (price_sorted_desc["Loading"] == 0.0)
            & (~price_sorted_desc.index.isin(used_for_discharge))
        ]
        ## Remove the charge if there is no time to discharge
        if len(later_times) == 0:
            data.loc[charge_idx, "Loading"] = 0
            continue

        discharge_idx = later_times.index[0]
        data.loc[discharge_idx, "Loading"] = -interval_energy
        used_for_discharge.add(discharge_idx)

    if partial_power_interval > 0:
        later_times = price_sorted_desc[
            (price_sorted_desc.index > partial_power_idx)
            & (price_sorted_desc["Loading"] == 0.0)
            & (~price_sorted_desc.index.isin(used_for_discharge))
        ]
        ## Remove the charge if there is no time to discharge
        if len(later_times) == 0:
            data.loc[partial_power_idx, "Loading"] = 0
        else:
            discharge_idx = later_times.index[0]
            data.loc[discharge_idx, "Loading"] = (
                interval_energy * partial_power_interval * -1
            )

    return data


def optimal_linalg(plant, day_data: pd.DataFrame):
    """
    Calculates a loading pattern for a given power plant based on linear optimization

    Args:
        plant: StoragePowerPlant to run the simulation on
        day_data: DataFrame with column "price_eur_mwh", sorted by timestamp

    Returns:
        data: DataFrame, copy of day_data with column "Loading" added
    """
    data = day_data.copy()
    data["Loading"] = 0.0
    prices = data["price_eur_mwh"].to_numpy()
    N = len(prices)
    interval_energy = plant.power / 4  # max MWh moved per 15-min interval

    ## Create cost vectors for charge and discharge
    cost_charge = (prices + plant.degradation) / 4
    cost_discharge = (plant.degradation - plant.efficiency * prices) / 4
    cost_total = np.concatenate([cost_charge, cost_discharge])

    ## Set up limit matrices to enforce charge within limits
    bounds = [(0, interval_energy)] * (2 * N)
    L = np.tril(np.ones((N, N)))
    A_ub = np.block(
        [
            [L, -L],
            [-L, L],
        ]
    )
    b_ub = np.concatenate(
        [
            np.full(N, plant.flexibility),
            np.zeros(N),
        ]
    )

    ## Compute linear solve and return result
    result = linprog(cost_total, A_ub=A_ub, b_ub=b_ub, bounds=bounds)
    charge, discharge = np.split(result.x, 2)
    load_col = charge - discharge
    data["Loading"] = load_col

    return data
