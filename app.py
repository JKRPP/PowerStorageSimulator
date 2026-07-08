import streamlit as st

from utils.ui_elements import button_columns, charge_metrics, data_selector_columns, pp_metrics, charge_visualization, simulation_options, residual_load_bars, plant_selector
from utils.external_data import get_prices, get_generation_mix
from utils.power_plant import StoragePowerPlant

## Configuration

st.set_page_config(
    page_title="Netzspeichersimulation",
    layout="wide",
)

data_loaded = False

if "price_df" in st.session_state:
    data_loaded = True

## User interface

st.title("Simulation eines Netzspeichers")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True, horizontal_alignment="right"):
        st.subheader("Stromdaten laden")
        selections = data_selector_columns("Startdatum", "Enddatum")
        if button_columns("Daten des Fraunhofer-Instituts laden", "Daten laden"):
            st.session_state["price_df"] = get_prices(**selections)
            data_loaded = True
        if data_loaded:
            st.success("Daten erfolgreich geladen!")

    ## Only render rest of page if data is loaded

    if not data_loaded:
        st.stop()

    with st.container(border=True):
        if data_loaded:
            st.subheader("Strompreis (Day-Ahead)")
            with st.spinner("Grafik wird gerendert, bitte warten..."):
                prices = st.session_state["price_df"]
                st.line_chart(prices, y="price_eur_mwh")

    with st.container(border=True):
        st.subheader("Simulierter Netzspeicher")
        title, metrics = plant_selector()
        plant = StoragePowerPlant(**metrics)
        pp_metrics(plant)
        day, alg, simulate_ok = simulation_options(st.session_state["price_df"])

## Only render rest of page if user has started simulation

if not simulate_ok:
    st.stop()

with col2:
    result_container = st.container(border=True)
    with result_container:
        st.subheader("Simulationsergebnis")
        if simulate_ok:
            date_df = st.session_state["price_df"][st.session_state["price_df"]["date"] == day]
            day_results = plant.process_day(date_df, alg)

            charge_metrics(day_results)
            charge_visualization(day_results)

            mix_day = get_generation_mix([day,day], "de")
            residual_load_bars(mix_day, day_results)