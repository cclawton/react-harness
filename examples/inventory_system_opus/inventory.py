"""Inventory management system — has multiple interacting bugs.

DO NOT REWRITE THIS FILE. Fix the bugs in place. The tests in
test_inventory.py describe the correct behaviour.

This module manages:
- Stock movements (in/out/reserve)
- Stock level calculations
- Inventory valuation (FIFO)
- Reorder point checking
- Reporting
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Movement:
    """A stock movement — in, out, or reserve."""
    id: str
    sku: str
    type: str  # "in", "out", "reserve"
    quantity: int
    timestamp: str  # ISO-8601
    unit_cost: float = 0.0  # Only meaningful for "in" movements


@dataclass
class StockLevel:
    """Current stock state for a SKU."""
    sku: str
    current_stock: int
    reserved: int
    pending_outbound: int
    available: int
    reorder_point: int


@dataclass
class Valuation:
    """FIFO valuation for a SKU."""
    sku: str
    total_units: int
    total_value: float
    avg_cost: float


class InventorySystem:
    def __init__(self, reorder_point: int = 10):
        self.movements: list[Movement] = []
        self.reorder_point = reorder_point

    def add_movement(self, movement: Movement) -> None:
        """Add a stock movement to the system."""
        self.movements.append(movement)

    def get_movements(self, sku: str) -> list[Movement]:
        """Get all movements for a SKU, sorted by timestamp (chronological)."""
        sku_moves = [m for m in self.movements if m.sku == sku]
        return sorted(sku_moves, key=lambda m: m.timestamp)

    def calculate_stock(self, sku: str) -> StockLevel:
        """Calculate current stock level for a SKU."""
        moves = self.get_movements(sku)
        current = 0
        reserved = 0
        pending_outbound = 0

        for m in moves:
            if m.type == "in":
                current += m.quantity
            elif m.type == "out":
                current -= m.quantity
                pending_outbound += m.quantity
            elif m.type == "reserve":
                reserved += m.quantity

        available = current - reserved - pending_outbound

        return StockLevel(
            sku=sku,
            current_stock=current,
            reserved=reserved,
            pending_outbound=pending_outbound,
            available=available,
            reorder_point=self.reorder_point,
        )

    def calculate_valuation(self, sku: str) -> Valuation:
        """Calculate FIFO valuation for a SKU.

        FIFO (First In First Out): The oldest inventory is sold first.
        Value the remaining stock at the most recent purchase prices.
        """
        moves = self.get_movements(sku)
        total_in = sum(m.quantity for m in moves if m.type == "in")
        total_out = sum(m.quantity for m in moves if m.type == "out")
        remaining = total_in - total_out

        # BUG 2: Uses LIFO instead of FIFO.
        # Gets the most recent "in" movements first (reversed),
        # which is LIFO. Should get oldest first (chronological),
        # which is FIFO.
        in_moves = [m for m in moves if m.type == "in"]
        in_moves_reversed = list(reversed(in_moves))

        total_value = 0.0
        units_to_value = remaining
        for m in in_moves_reversed:
            if units_to_value <= 0:
                break
            units_from_this = min(m.quantity, units_to_value)
            total_value += units_from_this * m.unit_cost
            units_to_value -= units_from_this

        avg_cost = total_value / remaining if remaining > 0 else 0.0

        return Valuation(
            sku=sku,
            total_units=remaining,
            total_value=total_value,
            avg_cost=avg_cost,
        )

    def needs_reorder(self, sku: str) -> bool:
        """Check if a SKU needs reordering.

        Reorder when available stock falls below the reorder point.
        Available = current stock - reserved - pending_outbound.
        """
        stock = self.calculate_stock(sku)
        return stock.available < self.reorder_point

    def generate_report(self, skus: list[str]) -> dict:
        """Generate an inventory report for multiple SKUs."""
        items = []
        for sku in skus:
            stock = self.calculate_stock(sku)
            valuation = self.calculate_valuation(sku)
            items.append({
                "sku": sku,
                "current_stock": stock.current_stock,
                "available": stock.available,
                "reserved": stock.reserved,
                "pending_outbound": stock.pending_outbound,
                "total_value": valuation.total_value,
                "avg_cost": valuation.avg_cost,
                "needs_reorder": self.needs_reorder(sku),
            })

        total_value = sum(i["total_value"] for i in items)
        total_reorder = sum(1 for i in items if i["needs_reorder"])

        # BUG 5: Formats currency as int (truncates decimals)
        return {
            "items": items,
            "total_inventory_value": total_value,
            "total_skus_needing_reorder": total_reorder,
            "report_timestamp": datetime.now().isoformat(),
        }
