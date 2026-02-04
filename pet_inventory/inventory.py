"""Inventory management for pet products."""

from datetime import date, timedelta
from typing import Optional

from .forecasting import Forecaster
from .models import (
    Category,
    Forecast,
    InventoryItem,
    Product,
    ReorderRecommendation,
    Sale,
)


class InventoryManager:
    """Manages product inventory, sales tracking, and reorder recommendations."""

    def __init__(self):
        """Initialize inventory manager."""
        self.products: dict[str, Product] = {}
        self.inventory: dict[str, InventoryItem] = {}
        self.sales: list[Sale] = []
        self._forecaster: Optional[Forecaster] = None

    @property
    def forecaster(self) -> Forecaster:
        """Get or create forecaster with current sales data."""
        if self._forecaster is None or len(self.sales) > 0:
            self._forecaster = Forecaster(self.sales)
        return self._forecaster

    def add_product(self, product: Product) -> None:
        """Add a new product to the catalog."""
        self.products[product.product_id] = product
        if product.product_id not in self.inventory:
            self.inventory[product.product_id] = InventoryItem(
                product=product, quantity_on_hand=0
            )

    def update_stock(
        self, product_id: str, quantity: int, is_restock: bool = True
    ) -> None:
        """Update stock quantity for a product."""
        if product_id not in self.inventory:
            raise ValueError(f"Product {product_id} not found in inventory")

        item = self.inventory[product_id]
        if is_restock:
            item.quantity_on_hand += quantity
            item.last_restock_date = date.today()
        else:
            item.quantity_on_hand = max(0, item.quantity_on_hand - quantity)

    def record_sale(self, sale: Sale) -> None:
        """Record a sale and update inventory."""
        self.sales.append(sale)
        self._forecaster = None  # Invalidate cached forecaster

        if sale.product_id in self.inventory:
            self.inventory[sale.product_id].quantity_on_hand = max(
                0, self.inventory[sale.product_id].quantity_on_hand - sale.quantity
            )

    def record_sales(self, sales: list[Sale]) -> None:
        """Record multiple sales."""
        for sale in sales:
            self.sales.append(sale)
            if sale.product_id in self.inventory:
                self.inventory[sale.product_id].quantity_on_hand = max(
                    0, self.inventory[sale.product_id].quantity_on_hand - sale.quantity
                )
        self._forecaster = None

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        return self.products.get(product_id)

    def get_inventory_status(self) -> list[InventoryItem]:
        """Get current inventory status for all products."""
        return list(self.inventory.values())

    def get_low_stock_items(self) -> list[InventoryItem]:
        """Get items that need reordering."""
        return [item for item in self.inventory.values() if item.needs_reorder]

    def forecast_demand(
        self, product_id: str, days: int = 14, method: str = "exponential"
    ) -> list[Forecast]:
        """Generate demand forecast for a product."""
        if product_id not in self.products:
            raise ValueError(f"Product {product_id} not found")

        product = self.products[product_id]
        forecasts = self.forecaster.forecast(product_id, method, days)

        # Fill in product names
        for f in forecasts:
            f.product_name = product.name

        return forecasts

    def get_reorder_recommendations(
        self, forecast_days: int = 30
    ) -> list[ReorderRecommendation]:
        """Generate reorder recommendations based on forecasts."""
        recommendations = []

        for product_id, item in self.inventory.items():
            product = item.product

            # Get forecasted demand
            avg_daily_demand = self.forecaster.get_average_daily_demand(
                product_id, days=30
            )
            forecasted_demand = avg_daily_demand * forecast_days

            # Calculate days until stockout
            if avg_daily_demand > 0:
                days_until_stockout = int(item.quantity_on_hand / avg_daily_demand)
            else:
                days_until_stockout = None  # No demand

            # Determine urgency
            if item.quantity_on_hand == 0:
                urgency = "critical"
            elif days_until_stockout and days_until_stockout <= product.lead_time_days:
                urgency = "critical"
            elif item.needs_reorder:
                urgency = "soon"
            elif (
                days_until_stockout
                and days_until_stockout <= product.lead_time_days * 2
            ):
                urgency = "soon"
            else:
                urgency = "planned"

            # Calculate recommended order quantity
            # Order enough to cover lead time + safety stock + forecast period
            safety_days = 7
            if avg_daily_demand > 0:
                min_needed = avg_daily_demand * (product.lead_time_days + safety_days)
                recommended_qty = max(
                    product.reorder_quantity,
                    int(min_needed - item.quantity_on_hand + avg_daily_demand * 14),
                )
            else:
                recommended_qty = product.reorder_quantity

            recommendations.append(
                ReorderRecommendation(
                    product=product,
                    current_stock=item.quantity_on_hand,
                    forecasted_demand=forecasted_demand,
                    days_until_stockout=days_until_stockout,
                    recommended_order_quantity=max(0, recommended_qty),
                    urgency=urgency,
                )
            )

        # Sort by urgency (critical first)
        urgency_order = {"critical": 0, "soon": 1, "planned": 2}
        recommendations.sort(key=lambda r: urgency_order[r.urgency])

        return recommendations

    def get_sales_summary(
        self, product_id: Optional[str] = None, days: int = 30
    ) -> dict:
        """Get sales summary for a product or all products."""
        cutoff_date = date.today() - timedelta(days=days)

        if product_id:
            relevant_sales = [
                s
                for s in self.sales
                if s.product_id == product_id and s.date >= cutoff_date
            ]
        else:
            relevant_sales = [s for s in self.sales if s.date >= cutoff_date]

        if not relevant_sales:
            return {
                "total_units": 0,
                "total_transactions": 0,
                "avg_daily_units": 0,
                "products_sold": 0,
            }

        total_units = sum(s.quantity for s in relevant_sales)
        unique_products = len(set(s.product_id for s in relevant_sales))

        return {
            "total_units": total_units,
            "total_transactions": len(relevant_sales),
            "avg_daily_units": total_units / days,
            "products_sold": unique_products,
        }

    def get_top_selling_products(self, days: int = 30, limit: int = 10) -> list[dict]:
        """Get top selling products by quantity."""
        cutoff_date = date.today() - timedelta(days=days)
        relevant_sales = [s for s in self.sales if s.date >= cutoff_date]

        # Aggregate by product
        product_sales: dict[str, int] = {}
        for sale in relevant_sales:
            product_sales[sale.product_id] = (
                product_sales.get(sale.product_id, 0) + sale.quantity
            )

        # Sort and limit
        sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        for product_id, quantity in sorted_products:
            product = self.products.get(product_id)
            results.append(
                {
                    "product_id": product_id,
                    "product_name": product.name if product else "Unknown",
                    "category": product.category.value if product else "unknown",
                    "quantity_sold": quantity,
                }
            )

        return results
