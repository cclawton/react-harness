"""Tests for the inventory management system — do not modify this file.

These tests describe the CORRECT behaviour. The inventory.py file
has bugs that cause these tests to fail. Fix the bugs in inventory.py.
"""
import pytest
from inventory import InventorySystem, Movement


# --- Helpers ----------------------------------------------------------------

def make_system(reorder_point=10):
    return InventorySystem(reorder_point=reorder_point)


def add_movements(system, movements):
    """Add movements in the given order (not necessarily chronological)."""
    for m in movements:
        system.add_movement(m)


# --- Test data --------------------------------------------------------------

# SKU-001: Simple stock in/out
MOVEMENTS_SIMPLE = [
    Movement("m1", "SKU-001", "in",  100, "2026-07-01T08:00:00Z", unit_cost=10.00),
    Movement("m2", "SKU-001", "out",  30, "2026-07-01T10:00:00Z"),
    Movement("m3", "SKU-001", "out",  20, "2026-07-01T12:00:00Z"),
]

# SKU-002: Movements added OUT OF ORDER — chronological sort matters
MOVEMENTS_OUT_OF_ORDER = [
    Movement("m1", "SKU-002", "in",   50, "2026-07-01T12:00:00Z", unit_cost=20.00),
    Movement("m2", "SKU-002", "in",   50, "2026-07-01T08:00:00Z", unit_cost=10.00),
    Movement("m3", "SKU-002", "out",  30, "2026-07-01T10:00:00Z"),
    Movement("m4", "SKU-002", "in",   20, "2026-07-01T14:00:00Z", unit_cost=30.00),
]

# SKU-003: With reservations and pending outbound
MOVEMENTS_RESERVED = [
    Movement("m1", "SKU-003", "in",      100, "2026-07-01T08:00:00Z", unit_cost=15.00),
    Movement("m2", "SKU-003", "reserve",  30, "2026-07-01T09:00:00Z"),
    Movement("m3", "SKU-003", "out",      20, "2026-07-01T10:00:00Z"),
    Movement("m4", "SKU-003", "reserve",  10, "2026-07-01T11:00:00Z"),
]

# SKU-004: Multiple price tiers for FIFO valuation
MOVEMENTS_FIFO = [
    Movement("m1", "SKU-004", "in",  100, "2026-07-01T08:00:00Z", unit_cost=5.00),
    Movement("m2", "SKU-004", "in",  100, "2026-07-01T10:00:00Z", unit_cost=8.00),
    Movement("m3", "SKU-004", "in",   50, "2026-07-01T12:00:00Z", unit_cost=12.00),
    Movement("m4", "SKU-004", "out", 180, "2026-07-01T14:00:00Z"),
]


class TestMovementOrdering:
    """Movements must be processed in chronological order (by timestamp)."""

    def test_movements_sorted_chronologically(self):
        sys = make_system()
        add_movements(sys, MOVEMENTS_OUT_OF_ORDER)
        moves = sys.get_movements("SKU-002")
        timestamps = [m.timestamp for m in moves]
        assert timestamps == sorted(timestamps)

    def test_out_of_order_stock_calculation(self):
        """If movements are added out of chronological order, stock
        should still be calculated based on chronological order."""
        sys = make_system()
        add_movements(sys, MOVEMENTS_OUT_OF_ORDER)
        stock = sys.calculate_stock("SKU-002")
        # Chronological: in(50@08:00), out(30@10:00), in(50@12:00), in(20@14:00)
        # current = 50 - 30 + 50 + 20 = 90
        assert stock.current_stock == 90


class TestStockCalculation:
    def test_simple_stock(self):
        sys = make_system()
        add_movements(sys, MOVEMENTS_SIMPLE)
        stock = sys.calculate_stock("SKU-001")
        # 100 in - 30 out - 20 out = 50
        assert stock.current_stock == 50

    def test_reserved_stock(self):
        sys = make_system()
        add_movements(sys, MOVEMENTS_RESERVED)
        stock = sys.calculate_stock("SKU-003")
        # 100 in - 20 out = 80 current, 30 + 10 = 40 reserved
        assert stock.current_stock == 80
        assert stock.reserved == 40

    def test_available_subtracts_reserved(self):
        sys = make_system()
        add_movements(sys, MOVEMENTS_RESERVED)
        stock = sys.calculate_stock("SKU-003")
        # available = current - reserved = 80 - 40 = 40
        assert stock.available == 40

    def test_available_subtracts_pending_outbound(self):
        """Available should also subtract pending outbound movements."""
        sys = make_system()
        add_movements(sys, MOVEMENTS_RESERVED)
        stock = sys.calculate_stock("SKU-003")
        # current=80, reserved=40, pending_outbound=20
        # available = 80 - 40 - 20 = 20
        assert stock.available == 20
        assert stock.pending_outbound == 20

    def test_no_movements(self):
        sys = make_system()
        stock = sys.calculate_stock("SKU-999")
        assert stock.current_stock == 0
        assert stock.reserved == 0
        assert stock.available == 0
        assert stock.pending_outbound == 0


class TestFIFOValuation:
    """FIFO: oldest inventory sold first. Remaining stock valued at
    most recent purchase prices."""

    def test_simple_fifo(self):
        sys = make_system()
        add_movements(sys, MOVEMENTS_SIMPLE)
        val = sys.calculate_valuation("SKU-001")
        # 100 in @ $10, 30 out, 20 out -> 50 remaining
        # FIFO: 50 remaining valued at $10 (oldest layer)
        assert val.total_units == 50
        assert val.total_value == pytest.approx(500.00)
        assert val.avg_cost == pytest.approx(10.00)

    def test_multi_tier_fifo(self):
        sys = make_system()
        add_movements(sys, MOVEMENTS_FIFO)
        val = sys.calculate_valuation("SKU-004")
        # 100@5 + 100@8 + 50@12 = 250 in, 180 out -> 70 remaining
        # FIFO: oldest (100@5, 100@8) sold first. Remaining:
        #   70 units from the most recent layers:
        #   50@12 = 600
        #   20@8 = 160
        #   total = 760
        assert val.total_units == 70
        assert val.total_value == pytest.approx(760.00)
        assert val.avg_cost == pytest.approx(760.00 / 70)

    def test_out_of_order_fifo(self):
        """Movements added out of chronological order — FIFO must use
        chronological order to determine which inventory is 'oldest'."""
        sys = make_system()
        add_movements(sys, MOVEMENTS_OUT_OF_ORDER)
        val = sys.calculate_valuation("SKU-002")
        # Chronological order:
        #   in(50@08:00, $10), out(30@10:00), in(50@12:00, $20), in(20@14:00, $30)
        # Total in: 120, total out: 30, remaining: 90
        # FIFO: oldest sold first. 30 units sold from the $10 layer.
        #   Remaining: 20@10 + 50@20 + 20@30
        #   = 200 + 1000 + 600 = 1800
        assert val.total_units == 90
        assert val.total_value == pytest.approx(1800.00)
        assert val.avg_cost == pytest.approx(1800.00 / 90)

    def test_zero_stock_valuation(self):
        sys = make_system()
        add_movements(sys, [
            Movement("m1", "SKU-005", "in",  10, "2026-07-01T08:00:00Z", unit_cost=5.00),
            Movement("m2", "SKU-005", "out", 10, "2026-07-01T10:00:00Z"),
        ])
        val = sys.calculate_valuation("SKU-005")
        assert val.total_units == 0
        assert val.total_value == 0.0
        assert val.avg_cost == 0.0


class TestReorderLogic:
    def test_reorder_when_available_low(self):
        """Reorder when AVAILABLE stock (not current stock) is below reorder point."""
        sys = make_system(reorder_point=30)
        add_movements(sys, MOVEMENTS_RESERVED)
        # current=80, reserved=40, pending_outbound=20, available=20
        # 20 < 30 -> needs reorder
        assert sys.needs_reorder("SKU-003") is True

    def test_no_reorder_when_available_sufficient(self):
        sys = make_system(reorder_point=30)
        add_movements(sys, MOVEMENTS_RESERVED)
        # If we lower the reorder point, available=20 >= 10 -> no reorder
        sys.reorder_point = 10
        assert sys.needs_reorder("SKU-003") is False

    def test_reorder_uses_available_not_current(self):
        """This test specifically catches Bug 3: using current_stock instead of available."""
        sys = make_system(reorder_point=30)
        add_movements(sys, MOVEMENTS_RESERVED)
        # current=80 (above 30), but available=20 (below 30)
        # If using current_stock: 80 >= 30 -> no reorder (WRONG)
        # If using available: 20 < 30 -> reorder (CORRECT)
        assert sys.needs_reorder("SKU-003") is True

    def test_no_reorder_when_stock_zero(self):
        sys = make_system(reorder_point=10)
        # No movements for this SKU
        assert sys.needs_reorder("SKU-999") is True


class TestReport:
    def test_report_structure(self):
        sys = make_system()
        add_movements(sys, MOVEMENTS_SIMPLE)
        add_movements(sys, MOVEMENTS_FIFO)
        report = sys.generate_report(["SKU-001", "SKU-004"])
        assert "items" in report
        assert "total_inventory_value" in report
        assert "total_skus_needing_reorder" in report
        assert "report_timestamp" in report

    def test_report_total_value_is_float(self):
        """Total inventory value must be a float, not truncated to int."""
        sys = make_system()
        add_movements(sys, MOVEMENTS_FIFO)
        report = sys.generate_report(["SKU-004"])
        # 760.00 — must not be truncated to 760 as int (this catches Bug 5)
        assert isinstance(report["total_inventory_value"], float)
        assert report["total_inventory_value"] == pytest.approx(760.00)

    def test_report_item_fields(self):
        sys = make_system()
        add_movements(sys, MOVEMENTS_SIMPLE)
        report = sys.generate_report(["SKU-001"])
        item = report["items"][0]
        assert "sku" in item
        assert "current_stock" in item
        assert "available" in item
        assert "reserved" in item
        assert "pending_outbound" in item
        assert "total_value" in item
        assert "avg_cost" in item
        assert "needs_reorder" in item

    def test_report_reorder_count(self):
        sys = make_system(reorder_point=10)
        # SKU-001: current=50, reserved=0, pending=50, available=0 -> needs reorder
        add_movements(sys, MOVEMENTS_SIMPLE)
        report = sys.generate_report(["SKU-001"])
        assert report["total_skus_needing_reorder"] == 1

    def test_report_multiple_skus(self):
        sys = make_system(reorder_point=10)
        add_movements(sys, MOVEMENTS_SIMPLE)
        add_movements(sys, MOVEMENTS_FIFO)
        report = sys.generate_report(["SKU-001", "SKU-004"])
        assert len(report["items"]) == 2
        # SKU-001: available = 50 - 0 - 50 = 0 < 10 -> reorder
        # SKU-004: available = 70 - 0 - 180... wait, pending_outbound = 180
        # current = 250 - 180 = 70, pending_outbound = 180
        # available = 70 - 0 - 180 = -110 < 10 -> reorder
        assert report["total_skus_needing_reorder"] == 2


class TestInteractingBugs:
    """These tests specifically verify that MULTIPLE bugs are fixed together.
    Fixing only one bug will still cause these to fail."""

    def test_fifo_with_out_of_order_and_reserved(self):
        """Chronological ordering + FIFO + available stock — all three must be correct."""
        sys = make_system(reorder_point=25)
        movements = [
            Movement("m1", "SKU-X", "in",      100, "2026-07-01T14:00:00Z", unit_cost=30.00),
            Movement("m2", "SKU-X", "in",       50, "2026-07-01T08:00:00Z", unit_cost=10.00),
            Movement("m3", "SKU-X", "reserve",  20, "2026-07-01T09:00:00Z"),
            Movement("m4", "SKU-X", "in",       50, "2026-07-01T10:00:00Z", unit_cost=20.00),
            Movement("m5", "SKU-X", "out",      40, "2026-07-01T12:00:00Z"),
        ]
        add_movements(sys, movements)

        # Chronological order: m2(08:00,in,50@$10), m3(09:00,res,20), m4(10:00,in,50@$20), m5(12:00,out,40), m1(14:00,in,100@$30)
        # current = 50 + 50 + 100 - 40 = 160
        # reserved = 20
        # pending_outbound = 40
        # available = 160 - 20 - 40 = 100
        stock = sys.calculate_stock("SKU-X")
        assert stock.current_stock == 160
        assert stock.available == 100
        assert stock.pending_outbound == 40

        # FIFO valuation:
        # Total in: 200, total out: 40, remaining: 160
        # FIFO: 40 sold from oldest ($10 layer)
        #   Remaining: 10@10 + 50@20 + 100@30 = 100 + 1000 + 3000 = 4100
        val = sys.calculate_valuation("SKU-X")
        assert val.total_units == 160
        assert val.total_value == pytest.approx(4100.00)

        # Reorder: available=100 >= 25 -> no reorder
        assert sys.needs_reorder("SKU-X") is False

    def test_report_with_all_bugs_fixed(self):
        """End-to-end test: report must be correct when all bugs are fixed."""
        sys = make_system(reorder_point=50)
        add_movements(sys, [
            Movement("m1", "SKU-R", "in",      100, "2026-07-01T12:00:00Z", unit_cost=20.00),
            Movement("m2", "SKU-R", "in",      100, "2026-07-01T08:00:00Z", unit_cost=10.00),
            Movement("m3", "SKU-R", "out",      50, "2026-07-01T10:00:00Z"),
            Movement("m4", "SKU-R", "reserve",  30, "2026-07-01T09:00:00Z"),
        ])

        report = sys.generate_report(["SKU-R"])
        item = report["items"][0]

        # Chronological: in(100@$10@08:00), reserve(30@09:00), out(50@10:00), in(100@$20@12:00)
        # current = 100 + 100 - 50 = 150
        # reserved = 30, pending_outbound = 50
        # available = 150 - 30 - 50 = 70
        assert item["current_stock"] == 150
        assert item["available"] == 70
        assert item["reserved"] == 30
        assert item["pending_outbound"] == 50

        # FIFO: 50 sold from oldest ($10 layer)
        # Remaining: 50@10 + 100@20 = 500 + 2000 = 2500
        assert item["total_value"] == pytest.approx(2500.00)
        assert item["avg_cost"] == pytest.approx(2500.00 / 150)

        # available=70 >= 50 -> no reorder
        assert item["needs_reorder"] is False

        # Total value must be float (Bug 5)
        assert isinstance(report["total_inventory_value"], float)
        assert report["total_inventory_value"] == pytest.approx(2500.00)

        # Reorder count
        assert report["total_skus_needing_reorder"] == 0
