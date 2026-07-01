# CSV Normalizer — Data Processing Task

The working directory contains a messy CSV file (`input.csv`) with inconsistent formatting:
- Categories have mixed case (electronics, Electronics, ELECTRONICS)
- Notes have leading/trailing whitespace
- Amounts are strings, not formatted consistently

Your task:
1. Read `input.csv` to understand the data
2. Read `test_normalize.py` to understand the expected behaviour
3. Write a Python script called `normalize.py` that:
   - Takes two command-line arguments: input file path and output file path
   - Reads the input CSV
   - Normalizes the data:
     - Categories: lowercase + stripped
     - Notes: stripped (empty string if only whitespace)
     - Amounts: formatted as floats with exactly 2 decimal places
     - Dates: preserved as-is
     - Products: preserved as-is
   - Writes the normalized data to the output CSV
   - Preserves the same column headers and row order
4. Run the tests (`python -m pytest test_normalize.py -v`) to verify
5. Signal done when all tests pass

Do NOT modify `test_normalize.py` or `input.csv`.
