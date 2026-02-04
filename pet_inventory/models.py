"""Data models for pet inventory system."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Category(Enum):
    """Product categories for pet inventory."""
    FOOD = "food"
    TOYS = "toys"
    ACCESSORIES = "accessories"
    MEDICATION = "medication"
    GROOMING = "grooming"
    BEDDING = "bedding"
    OTHER = "other"


@dataclass
class Product:
    """Represents a product in inventory."""
    product_id: str
    name: str
    category: Category
    unit_price: float
    reorder_point: int = 10  # Minimum stock before reorder alert
    reorder_quantity: int = 50  # Suggested quantity to reorder
    lead_time_days: int = 7  # Days to receive new stock

    def __hash__(self):
        return hash(self.product_id)

    def __eq__(self, other):
        if isinstance(other, Product):
            return self.product_id == other.product_id
        return False


@dataclass
class Sale:
    """Represents a single sale transaction."""
    date: date
    product_id: str
    quantity: int
    unit_price: Optional[float] = None

    @property
    def total(self) -> float:
        """Calculate total sale amount."""
        if self.unit_price:
            return self.quantity * self.unit_price
        return 0.0


@dataclass
class InventoryItem:
    """Represents current inventory for a product."""
    product: Product
    quantity_on_hand: int
    last_restock_date: Optional[date] = None

    @property
    def needs_reorder(self) -> bool:
        """Check if product needs to be reordered."""
        return self.quantity_on_hand <= self.product.reorder_point

    @property
    def stock_status(self) -> str:
        """Get human-readable stock status."""
        if self.quantity_on_hand == 0:
            return "OUT OF STOCK"
        elif self.quantity_on_hand <= self.product.reorder_point:
            return "LOW STOCK"
        else:
            return "IN STOCK"


@dataclass
class Forecast:
    """Represents a demand forecast for a product."""
    product_id: str
    product_name: str
    forecast_date: date
    predicted_demand: float
    method: str
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None

    def __str__(self) -> str:
        conf = ""
        if self.confidence_lower and self.confidence_upper:
            conf = f" (range: {self.confidence_lower:.1f} - {self.confidence_upper:.1f})"
        return f"{self.forecast_date}: {self.predicted_demand:.1f} units{conf}"


@dataclass
class ReorderRecommendation:
    """Recommendation for reordering a product."""
    product: Product
    current_stock: int
    forecasted_demand: float
    days_until_stockout: Optional[int]
    recommended_order_quantity: int
    urgency: str  # "critical", "soon", "planned"

    def __str__(self) -> str:
        return (
            f"{self.product.name}: Order {self.recommended_order_quantity} units "
            f"(Current: {self.current_stock}, Forecast: {self.forecasted_demand:.0f}/period) "
            f"[{self.urgency.upper()}]"
        )
