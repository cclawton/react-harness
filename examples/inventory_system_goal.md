# Inventory System — Interacting Bugs Task

The working directory contains an inventory management system (`inventory.py`) with FIVE bugs and a test suite (`test_inventory.py`) with 20+ tests describing the correct behaviour.

Your task:
1. Read `test_inventory.py` to understand the correct behaviour
2. Read `inventory.py` to understand the code and find the bugs
3. Fix ALL five bugs in `inventory.py` — do NOT rewrite the file, fix the bugs in place
4. Run the tests (`python -m pytest test_inventory.py -v`) to verify
5. Signal done when all tests pass

Do NOT modify `test_inventory.py`.

THE FIVE BUGS (you must find and fix all of them):

1. **Movement ordering**: `get_movements()` returns movements sorted by ID (arrival order) instead of by timestamp (chronological order). This affects everything downstream.

2. **Valuation method**: `calculate_valuation()` uses LIFO (most recent first) instead of FIFO (oldest first). The direction of the `in_moves` iteration is wrong.

3. **Reorder check**: `needs_reorder()` compares `current_stock` against the reorder point, but should compare `available` stock (which accounts for reserved and pending outbound).

4. **Available stock**: `calculate_stock()` computes `available` as `current - reserved` but should be `current - reserved - pending_outbound`.

5. **Currency truncation**: `generate_report()` converts `total_value` to `int`, truncating decimals. It should remain a `float`.

CRITICAL — WHY THESE BUGS INTERACT:

Fixing bug 4 (available stock) changes what `available` means, which interacts with bug 3 (reorder uses the wrong field). If you fix bug 4 but not bug 3, the reorder check still uses `current_stock` instead of the now-correct `available`.

Fixing bug 1 (chronological order) changes which inventory layers are "oldest", which interacts with bug 2 (FIFO vs LIFO). If you fix bug 2 (reverse the direction) without also fixing bug 1 (sort by timestamp), the valuation uses chronological order with LIFO direction — still wrong.

The tests in `TestInteractingBugs` specifically verify that multiple bugs are fixed together. Fixing only one bug at a time will not make these tests pass. You must understand the whole system before making changes.

APPROACH SUGGESTION: Read the code, identify all five bugs, then fix them ALL before running tests. Running tests after fixing only one or two bugs will still show failures — which is expected. Don't chase individual test failures; fix the root causes.
