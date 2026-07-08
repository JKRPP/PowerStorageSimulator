# PowerStorageSimulator

Simulates a Storage Power Plant connected to the german electricity market based on historical day-ahead prices.

## Project structure

```
app.py                     Streamlit entry point / page layout
utils/
  external_data.py         Fetches price and generation-mix data from the energy-charts API
  power_plant.py           StoragePowerPlant model and profit calculation
  algorithms.py            Load planning algorithms (single_cycle, optimal_linalg)
  ui_elements.py            Streamlit UI components (metrics, charts, selectors)
tests.py                    Pytest unit tests for the storage plant logic
```

## Installation

Requires Python 3.10+.

To install, run:
```bash
pip install streamlit pandas numpy scipy plotly requests pytest
```

## Usage

Run:
```bash
streamlit run app.py
```

Then, in the app:
1. Select a start/end date and load the day-ahead price data.
2. Choose a storage plant type.
3. Pick a day and planning algorithm, then run the simulation.

## Testing

```bash
pytest tests.py
```
