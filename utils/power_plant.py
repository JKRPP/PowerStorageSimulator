import pandas as pd
from utils.algorithms import optimal_linalg, single_cycle
import numpy as np


class StoragePowerPlant:
    def __init__(
        self,
        power=10.0,
        capacity=15.0,
        efficiency=0.9,
        upper_limit=0.9,
        lower_limit=0.1,
        degradation=5.0,
    ):
        self.power = power
        self.capacity = capacity
        self.efficiency = efficiency
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.degradation = degradation

        self.flexibility = self.capacity * upper_limit - self.capacity * lower_limit

    def process_day(self, day_data: pd.DataFrame, algorithm="Single Cycle"):
        """
        Processes a day for the Power plant, following a given algorithm.

        Args:
            day_data: A dataframe with a "price_eur_mwh" column for costs, sorted by time
            algorithm: An algorithm to simulate on. Currently available: "Single Cycle" and "Optimal"

        Returns:
            data: A dataframe with added columns for action, cost and profit.
        """
        match algorithm:
            case "Single Cycle":
                data = single_cycle(self, day_data)
            case "Optimal":
                data = optimal_linalg(self, day_data)
            case _:
                raise Exception(f"Unknown algorithm: {algorithm}")

        return self._calculate_charge(data)

    def _calculate_charge(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the resulting charge and profits from an action supplied in data.

        Args:
            data: Dataframe with "Loading" and "price_eur_mwh" columns.

        Returns:
            out: DataFrame with added "current_charge", "power_profit", "degradation_cost" and "total_profit" columns.
        """
        charge = data["Loading"].to_numpy().copy()
        charge[0] = charge[0] + self.lower_limit * self.capacity

        ## Compute charge and profit
        data["current_charge"] = np.cumsum(charge)
        data["power_cost"] = 0.0
        data["power_revenue"] = 0.0

        charge_ts = data["Loading"] > 0
        discharge_ts = data["Loading"] < 0

        data.loc[charge_ts, "power_cost"] = (
            data.loc[charge_ts, "price_eur_mwh"] * data.loc[charge_ts, "Loading"] / 4
        )
        data.loc[discharge_ts, "power_revenue"] = (
            -1
            * self.efficiency
            * data.loc[discharge_ts, "price_eur_mwh"]
            * data.loc[discharge_ts, "Loading"]
            / 4
        )

        data["degradation_cost"] = self.degradation * data["Loading"].abs() / 4
        data["total_profit"] = data["power_revenue"] - (
            data["degradation_cost"] + data["power_cost"]
        )

        return data
