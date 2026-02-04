"""Data models for pet inventory projection system."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class SKU:
    """Represents a product SKU."""
    sku: str
    name: str
    current_inventory: int
    current_monthly_sales: float  # Current baseline monthly sales (units/month)
    growth_rate: float = 0.0  # Monthly growth rate (e.g., 0.05 = 5%)

    def get_projected_sales(self, months_ahead: int) -> float:
        """
        Calculate projected sales for a future month.

        Month 0 (current month): current_monthly_sales
        Month 1: current_monthly_sales * (1 + growth_rate)
        Month 2: current_monthly_sales * (1 + growth_rate)^2
        etc.
        """
        return self.current_monthly_sales * ((1 + self.growth_rate) ** months_ahead)


@dataclass
class PurchaseOrder:
    """Represents an incoming purchase order."""
    po_number: str
    sku: str
    quantity: int
    expected_arrival: date

    def arrives_in_month(self, year: int, month: int) -> bool:
        """Check if PO arrives in the specified month."""
        return self.expected_arrival.year == year and self.expected_arrival.month == month


@dataclass
class MonthlyProjection:
    """Projection for a single SKU in a single month."""
    sku: str
    sku_name: str
    year: int
    month: int
    beginning_inventory: int
    incoming_pos: int  # Units arriving from POs
    projected_sales: float
    ending_inventory: float

    @property
    def month_label(self) -> str:
        """Get formatted month label like 'Jan 2026'."""
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return f"{month_names[self.month - 1]} {self.year}"

    @property
    def stockout_risk(self) -> bool:
        """Check if ending inventory is negative (stockout)."""
        return self.ending_inventory < 0
