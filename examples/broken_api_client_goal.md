# Broken API Client — Debugging Task

The working directory contains a Python project with a weather API client (`client.py`) and a test suite (`test_client.py`).

There are THREE bugs in `client.py`:

1. `get_forecast()` returns days in reversed order (chronological order is wrong)
2. `hottest_day` property finds the day with the highest `temp_low` instead of `temp_high`
3. `coldest_day` property finds the day with the lowest `temp_high` instead of `temp_low`

Your task:
1. Read `client.py` and `test_client.py` to understand the code and expected behaviour
2. Run the tests to see which ones fail
3. Fix all three bugs in `client.py` — do NOT modify `test_client.py`
4. Run the tests again to confirm all tests pass
5. Signal done when all tests pass
