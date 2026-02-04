"""Inventory projection engine."""

from datetime import date
from typing import Optional

from .models import MonthlyProjection, PurchaseOrder, SKU


class InventoryProjector:
    """Projects inventory levels month by month."""

    def __init__(self):
        """Initialize projector."""
        self.skus: dict[str, SKU] = {}
        self.purchase_orders: list[PurchaseOrder] = []

    def add_sku(self, sku: SKU) -> None:
        """Add or update a SKU."""
        self.skus[sku.sku] = sku

    def add_purchase_order(self, po: PurchaseOrder) -> None:
        """Add a purchase order."""
        self.purchase_orders.append(po)

    def get_pos_for_month(self, sku: str, year: int, month: int) -> int:
        """Get total units arriving from POs in a specific month for a SKU."""
        total = 0
        for po in self.purchase_orders:
            if po.sku == sku and po.arrives_in_month(year, month):
                total += po.quantity
        return total

    def project_sku(
        self, sku_id: str, num_months: int = 12, start_date: Optional[date] = None
    ) -> list[MonthlyProjection]:
        """
        Project inventory for a single SKU over multiple months.

        Args:
            sku_id: The SKU identifier
            num_months: Number of months to project
            start_date: Starting date (defaults to current month)

        Returns:
            List of MonthlyProjection objects
        """
        if sku_id not in self.skus:
            raise ValueError(f"SKU {sku_id} not found")

        sku = self.skus[sku_id]

        if start_date is None:
            start_date = date.today().replace(day=1)

        projections = []
        current_inventory = float(sku.current_inventory)
        current_year = start_date.year
        current_month = start_date.month

        for month_offset in range(num_months):
            # Calculate year and month
            year = current_year + (current_month + month_offset - 1) // 12
            month = (current_month + month_offset - 1) % 12 + 1

            # Beginning inventory is ending inventory from previous month
            beginning_inventory = current_inventory

            # Get incoming POs for this month
            incoming_pos = self.get_pos_for_month(sku_id, year, month)

            # Calculate projected sales with growth rate
            projected_sales = sku.get_projected_sales(month_offset)

            # Calculate ending inventory
            ending_inventory = beginning_inventory + incoming_pos - projected_sales

            projection = MonthlyProjection(
                sku=sku_id,
                sku_name=sku.name,
                year=year,
                month=month,
                beginning_inventory=int(beginning_inventory),
                incoming_pos=incoming_pos,
                projected_sales=round(projected_sales, 1),
                ending_inventory=round(ending_inventory, 1),
            )
            projections.append(projection)

            # Carry forward ending inventory
            current_inventory = ending_inventory

        return projections

    def project_all(
        self, num_months: int = 12, start_date: Optional[date] = None
    ) -> dict[str, list[MonthlyProjection]]:
        """
        Project inventory for all SKUs.

        Returns:
            Dictionary mapping SKU to list of projections
        """
        results = {}
        for sku_id in self.skus:
            results[sku_id] = self.project_sku(sku_id, num_months, start_date)
        return results

    def get_stockout_alerts(
        self, num_months: int = 12, start_date: Optional[date] = None
    ) -> list[MonthlyProjection]:
        """Get all projections where stockout occurs."""
        alerts = []
        all_projections = self.project_all(num_months, start_date)

        for sku_id, projections in all_projections.items():
            for proj in projections:
                if proj.stockout_risk:
                    alerts.append(proj)
                    break  # Only report first stockout month per SKU

        return sorted(alerts, key=lambda p: (p.year, p.month))
