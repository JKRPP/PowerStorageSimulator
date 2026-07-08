import requests
import datetime
import pandas as pd

BASE = "https://api.energy-charts.info"

def get_prices(start_time, end_time, zone="DE-LU") -> pd.DataFrame:
    """
    Requests the price data for german electricity prices (per mwh) as a dataframe between specific dates.

    Args:
        times: An interable of two timestamps (to be converted to iso strings)
        zone: Zone from which to pull prices (default "DE-LU" (germany))

    Returns:
        out: pd.DataFrame of prices, ordered by time
    """
    [start, end] = _get_time_strings([start_time, end_time])
    r = requests.get(f"{BASE}/price", params={
        "bzn": zone,
        "start": start,
        "end": end
    })
    data = r.json()
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(data["unix_seconds"], unit="s", utc=True),
        "price_eur_mwh": data["price"]
    })
    return _clean_times(df)

def get_generation_mix(times, country="de"):
    [start, end] = _get_time_strings(times)
    r = requests.get(f"{BASE}/public_power", params={
        "country": country,
        "start": start,
        "end": end
    })
    data = r.json()
    timestamps = pd.to_datetime(data["unix_seconds"], unit="s", utc=True)
    df = pd.DataFrame({"timestamp": timestamps})
    for series in data["production_types"]:
        df[series["name"]] = series["data"]
    return df.set_index("timestamp")

def _get_time_strings(timestamps) -> list:
    """
    Converts timestamps to iso strings
    """
    return [x.isoformat() for x in timestamps]


def _clean_times(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a Dataframe with the timestamp column as an index and columns for hour of day and day of year added.

    Args:
        df: pd.DataFrame with one column "timestamp"
    Returns:
        out: pd.DataFrame with converted and added columns
    """
    df["timestamp"] = df["timestamp"].dt.tz_convert("Europe/Berlin")
    df["date"] = df["timestamp"].dt.date
    return df.set_index("timestamp")