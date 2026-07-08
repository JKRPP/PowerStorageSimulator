import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from utils.power_plant import StoragePowerPlant


def button_columns(label_text: str, button_text: str):
    """
    Creates a Button with explanatory text to its left
    Args:
        label_text: Explanatory text for the button
        button_text: Text on the button itself
    Returns:
        out: Boolean of whether the button is pressed
    """
    col1, col2 = st.columns([1, 1])
    with col1:
        st.text(label_text)
    with col2:
        out = st.button(button_text, use_container_width=True)
    return out


def data_selector_columns(left_text: str, right_text: str):
    """
    Creates two date selectors selector side by side.
    Args:
        left_text: Text on the left selector
        right_text: Text on the right selector
    Returns:
        out: Set of the left and right date as datetime.date
    """

    col1, col2 = st.columns([1, 1])
    with col1:
        out_start = st.date_input(left_text, value="2026-07-01")
    with col2:
        out_end = st.date_input(right_text)

    return {"start_time": out_start, "end_time": out_end}


def pp_metrics(plant: StoragePowerPlant):
    """
    Creates two rows of metrics for a given storage power plant object
    Args:
        plant: StoragePowerPlant object that simulates a plant
    Returns:
        None
    """
    col11, col12, col13 = st.columns(3)
    col21, col22, col23 = st.columns(3)

    col11.metric("Leistung", str(plant.power) + " MW")
    col12.metric("Kapazität", str(plant.capacity) + " MWh")
    col13.metric("Effizienz", str(plant.efficiency * 100) + " %")
    col21.metric("Unteres Ladelimit", str(plant.lower_limit * 100) + " %")
    col22.metric("Oberes Ladelimit", str(plant.upper_limit * 100) + " %")
    col23.metric("Abnutzungskosten", str(plant.degradation) + " €/MWh")


def charge_visualization(data: pd.DataFrame):
    """
    Creates a visualization of a simulated day for the power plant as a plotly line graph showing cost and charge throughout the day.
    Args:
        data: DataFrame with timestamps as an index and "price_eur_mwh" and "current_charge" columns.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["price_eur_mwh"],
            mode="lines",
            name="Preis (EUR/MWh)",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["current_charge"],
            mode="lines",
            name="Aktuelle Ladung (MWh)",
        ),
        secondary_y=True,
    )

    fig.update_yaxes(title_text="Stromkosten (€/MWh)", secondary_y=False)
    fig.update_yaxes(title_text="Ladung des Netzspeichers (MWh)", secondary_y=True)

    fig.update_layout(
        legend=dict(orientation="h"),
        yaxis=dict(
            side="left",
        ),
        yaxis2=dict(
            overlaying="y",
            tickmode="sync",
        ),
    )

    return st.plotly_chart(fig)


def residual_load_bars(mix_data: pd.DataFrame, result_data: pd.DataFrame):
    """
    Displays additional information about the power mix during charging and discharging

    Args:
        mix_data: A dataframe with columns "Residual load" and "Renewable share of load"
        result_data: A dataframe with the column "Loading"
    """
    charge_indices = result_data[result_data["Loading"] > 0].index
    discharge_indices = result_data[result_data["Loading"] < 0].index

    residual_charge = mix_data[mix_data.index.isin(charge_indices)][
        "Residual load"
    ].mean()
    residual_discharge = mix_data[mix_data.index.isin(discharge_indices)][
        "Residual load"
    ].mean()

    renewable_charge = mix_data[mix_data.index.isin(charge_indices)][
        "Renewable share of load"
    ].mean()
    renewable_discharge = mix_data[mix_data.index.isin(discharge_indices)][
        "Renewable share of load"
    ].mean()

    result_df = pd.DataFrame()
    result_df["Operation"] = ["Ladung", "Entladung"]
    result_df["Residuallast"] = [residual_charge, residual_discharge]
    result_df["Anteil Erneuerbare"] = [renewable_charge, renewable_discharge]

    percent_change_residual = (
        (residual_discharge - residual_charge) * 100 / residual_discharge
    ).__round__(2)
    percent_change_renewables = (
        (renewable_charge - renewable_discharge) * 100 / renewable_charge
    ).__round__(2)

    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(
            result_df, x="Operation", y="Residuallast", color="Yellow", sort=False
        )
        st.metric(
            "Residuallast während der Entladung",
            str(residual_discharge.__round__(2)) + " MWh",
            str(percent_change_residual) + " %",
        )
    with col2:
        st.bar_chart(
            result_df, x="Operation", y="Anteil Erneuerbare", color="Green", sort=False
        )
        st.metric(
            "Anteil erneuerbarer während der Ladung",
            str(renewable_charge.__round__(2)) + " %",
            str(percent_change_renewables) + " %",
        )


def charge_metrics(data: pd.DataFrame):
    """
    Displays metrics for the computed cycle.

    Args:
        data: A dataframe with columns "power_revenue", "power_cost", "degradation_cost" and "total_profit"
    """
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Einnahmen", str(data["power_revenue"].sum().round(2)) + " €")
    col2.metric("Stromkosten", str(data["power_cost"].sum().round(2)) + " €")
    col3.metric("Abnutzungskosten", str(data["degradation_cost"].sum().round(2)) + " €")
    col4.metric("Gesamtprofit", str(data["total_profit"].sum().round(2)) + " €")


def simulation_options(data: pd.DataFrame):
    """
    Selectors for the day and algorithm to use for a simulation

    Args:
        data: A dataframe with a "date" column for the date selection.

    returns:
        day: The day the user selected
        alg: The algorithm the user selected
        simulate: If the "Simulate" button was clicked
    """
    col1, col2 = st.columns(2)

    days = data["date"].unique()

    day = col1.selectbox("Datum auswählen", days)
    alg = col2.selectbox("Algorithmus auswählen", ["Single Cycle", "Optimal"])
    simulate = st.button("Simulation starten", use_container_width=True)

    return day, alg, simulate


def plant_selector():
    """
    Allows the user to select a different kind of storage power plant.

    Args:

    Returns:
        selected: The type of plant the user selected
        metrics: The metrics associated with that plant
    """
    plant_types = {
        "Klein (Li-ion)": {
            "power": 10.0,
            "capacity": 15.0,
            "efficiency": 0.9,
            "upper_limit": 0.9,
            "lower_limit": 0.1,
            "degradation": 10.0,
        },
        "Groß (Li-ion)": {
            "power": 50.0,
            "capacity": 150.0,
            "efficiency": 0.9,
            "upper_limit": 0.9,
            "lower_limit": 0.1,
            "degradation": 7.5,
        },
        "Redox-Flow": {
            "power": 20.0,
            "capacity": 120.0,
            "efficiency": 0.7,
            "upper_limit": 0.9,
            "lower_limit": 0.1,
            "degradation": 4.0,
        },
        "Pumpspeicher": {
            "power": 300.0,
            "capacity": 1800.0,
            "efficiency": 0.8,
            "upper_limit": 0.9,
            "lower_limit": 0.1,
            "degradation": 3.0,
        },
        "Elektroauto": {
            "power": 0.008,
            "capacity": 0.095,
            "efficiency": 0.9,
            "upper_limit": 0.9,
            "lower_limit": 0.5,
            "degradation": 20.0,
        },
    }

    selected = st.selectbox(
        "Simulierten Netzspeichertyp auswählen:", plant_types.keys()
    )

    return selected, plant_types[selected]
