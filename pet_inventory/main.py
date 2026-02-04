"""Main CLI application for pet inventory forecasting."""

import argparse
import sys
from datetime import date

from .inventory import InventoryManager
from .models import Category
from .utils import (
    format_currency,
    format_table,
    generate_sample_products,
    generate_sample_sales,
    load_sales_from_csv,
)


def create_demo_manager() -> InventoryManager:
    """Create inventory manager with sample data."""
    manager = InventoryManager()

    # Add sample products
    products = generate_sample_products()
    for product in products:
        manager.add_product(product)

    # Generate sample sales history
    sales = generate_sample_sales(products, days=90, seed=42)
    manager.record_sales(sales)

    # Set initial inventory levels (simulate current stock)
    import random
    random.seed(42)
    for product_id in manager.inventory:
        product = manager.products[product_id]
        # Random stock level, some intentionally low
        stock = random.randint(0, product.reorder_quantity * 2)
        manager.inventory[product_id].quantity_on_hand = stock

    return manager


def show_inventory_status(manager: InventoryManager) -> None:
    """Display current inventory status."""
    print("\n" + "=" * 70)
    print("INVENTORY STATUS")
    print("=" * 70)

    items = manager.get_inventory_status()

    # Group by category
    by_category: dict[Category, list] = {}
    for item in items:
        cat = item.product.category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    for category in Category:
        if category not in by_category:
            continue

        print(f"\n{category.value.upper()}")
        print("-" * 50)

        headers = ["Product", "Stock", "Status", "Reorder Point"]
        rows = []

        for item in sorted(by_category[category], key=lambda x: x.product.name):
            rows.append([
                item.product.name[:30],
                str(item.quantity_on_hand),
                item.stock_status,
                str(item.product.reorder_point),
            ])

        print(format_table(headers, rows))


def show_low_stock_alerts(manager: InventoryManager) -> None:
    """Display low stock alerts."""
    low_stock = manager.get_low_stock_items()

    if not low_stock:
        print("\n✓ All products are adequately stocked.")
        return

    print("\n" + "=" * 70)
    print("LOW STOCK ALERTS")
    print("=" * 70)

    for item in sorted(low_stock, key=lambda x: x.quantity_on_hand):
        status = "OUT OF STOCK" if item.quantity_on_hand == 0 else "LOW STOCK"
        print(f"  [{status}] {item.product.name}: {item.quantity_on_hand} units "
              f"(reorder at {item.product.reorder_point})")


def show_forecasts(manager: InventoryManager, product_id: str = None, days: int = 14) -> None:
    """Display demand forecasts."""
    print("\n" + "=" * 70)
    print(f"DEMAND FORECAST (Next {days} Days)")
    print("=" * 70)

    if product_id:
        products = [product_id]
    else:
        # Show forecasts for top-selling products
        top = manager.get_top_selling_products(days=30, limit=10)
        products = [p["product_id"] for p in top]

    for pid in products:
        product = manager.get_product(pid)
        if not product:
            continue

        forecasts = manager.forecast_demand(pid, days=days, method="exponential")

        if not forecasts:
            continue

        # Calculate summary
        total_demand = sum(f.predicted_demand for f in forecasts)
        avg_demand = total_demand / len(forecasts)
        trend = manager.forecaster.get_demand_trend(pid)

        print(f"\n{product.name}")
        print(f"  Method: {forecasts[0].method}")
        print(f"  Trend: {trend.replace('_', ' ').title()}")
        print(f"  Avg Daily Demand: {avg_demand:.1f} units")
        print(f"  Total {days}-Day Forecast: {total_demand:.0f} units")

        # Show daily breakdown for first 7 days
        if days <= 14:
            print("\n  Daily Forecast:")
            for f in forecasts[:7]:
                bar_len = int(f.predicted_demand * 2)
                bar = "█" * bar_len
                print(f"    {f.forecast_date}: {f.predicted_demand:5.1f} {bar}")
            if len(forecasts) > 7:
                print(f"    ... and {len(forecasts) - 7} more days")


def show_reorder_recommendations(manager: InventoryManager) -> None:
    """Display reorder recommendations."""
    print("\n" + "=" * 70)
    print("REORDER RECOMMENDATIONS")
    print("=" * 70)

    recommendations = manager.get_reorder_recommendations(forecast_days=30)

    # Group by urgency
    critical = [r for r in recommendations if r.urgency == "critical"]
    soon = [r for r in recommendations if r.urgency == "soon"]
    planned = [r for r in recommendations if r.urgency == "planned" and r.recommended_order_quantity > 0]

    if critical:
        print("\n🔴 CRITICAL - Order Immediately:")
        for rec in critical:
            days_str = f"{rec.days_until_stockout}d" if rec.days_until_stockout else "N/A"
            print(f"  • {rec.product.name}")
            print(f"    Current: {rec.current_stock} | Days to stockout: {days_str}")
            print(f"    Recommended order: {rec.recommended_order_quantity} units")

    if soon:
        print("\n🟡 SOON - Order This Week:")
        for rec in soon:
            days_str = f"{rec.days_until_stockout}d" if rec.days_until_stockout else "N/A"
            print(f"  • {rec.product.name}")
            print(f"    Current: {rec.current_stock} | Days to stockout: {days_str}")
            print(f"    Recommended order: {rec.recommended_order_quantity} units")

    if planned:
        print("\n🟢 PLANNED - Order When Convenient:")
        headers = ["Product", "Stock", "Stockout", "Order Qty"]
        rows = []
        for rec in planned[:10]:
            days_str = f"{rec.days_until_stockout}d" if rec.days_until_stockout else "N/A"
            rows.append([
                rec.product.name[:25],
                str(rec.current_stock),
                days_str,
                str(rec.recommended_order_quantity),
            ])
        print(format_table(headers, rows))

    # Summary
    total_critical = len(critical)
    total_soon = len(soon)
    print(f"\nSummary: {total_critical} critical, {total_soon} need ordering soon, "
          f"{len(planned)} for future planning")


def show_sales_summary(manager: InventoryManager, days: int = 30) -> None:
    """Display sales summary."""
    print("\n" + "=" * 70)
    print(f"SALES SUMMARY (Last {days} Days)")
    print("=" * 70)

    summary = manager.get_sales_summary(days=days)

    print(f"\n  Total Units Sold: {summary['total_units']:,}")
    print(f"  Total Transactions: {summary['total_transactions']:,}")
    print(f"  Average Daily Sales: {summary['avg_daily_units']:.1f} units")
    print(f"  Products Sold: {summary['products_sold']}")

    print("\n  Top Selling Products:")
    top_products = manager.get_top_selling_products(days=days, limit=10)

    headers = ["Rank", "Product", "Category", "Units Sold"]
    rows = []
    for i, prod in enumerate(top_products, 1):
        rows.append([
            str(i),
            prod["product_name"][:25],
            prod["category"],
            str(prod["quantity_sold"]),
        ])
    print(format_table(headers, rows))


def run_demo() -> None:
    """Run a full demo of the inventory forecasting system."""
    print("\n" + "=" * 70)
    print("PET INVENTORY FORECASTING SYSTEM - DEMO")
    print("=" * 70)
    print("\nInitializing with sample data (90 days of sales history)...")

    manager = create_demo_manager()

    print(f"\nLoaded {len(manager.products)} products")
    print(f"Loaded {len(manager.sales)} sales transactions")

    # Show all reports
    show_sales_summary(manager, days=30)
    show_inventory_status(manager)
    show_low_stock_alerts(manager)
    show_forecasts(manager, days=14)
    show_reorder_recommendations(manager)

    print("\n" + "=" * 70)
    print("END OF DEMO")
    print("=" * 70)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Pet Inventory Forecasting System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m pet_inventory.main --demo              Run demo with sample data
  python -m pet_inventory.main --status            Show inventory status
  python -m pet_inventory.main --forecast --days 30  Generate 30-day forecast
  python -m pet_inventory.main --reorder           Show reorder recommendations
        """,
    )

    parser.add_argument("--demo", action="store_true", help="Run demo with sample data")
    parser.add_argument("--status", action="store_true", help="Show inventory status")
    parser.add_argument("--forecast", action="store_true", help="Generate demand forecast")
    parser.add_argument("--reorder", action="store_true", help="Show reorder recommendations")
    parser.add_argument("--sales", action="store_true", help="Show sales summary")
    parser.add_argument("--alerts", action="store_true", help="Show low stock alerts")
    parser.add_argument("--product", type=str, help="Product ID for specific forecast")
    parser.add_argument("--days", type=int, default=14, help="Forecast period in days")
    parser.add_argument("--import", dest="import_file", type=str, help="Import sales from CSV")

    args = parser.parse_args()

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # Run demo
    if args.demo:
        run_demo()
        return

    # For other commands, create manager with sample data
    manager = create_demo_manager()

    # Import sales if specified
    if args.import_file:
        try:
            sales = load_sales_from_csv(args.import_file)
            manager.record_sales(sales)
            print(f"Imported {len(sales)} sales from {args.import_file}")
        except Exception as e:
            print(f"Error importing sales: {e}")
            return

    # Execute requested commands
    if args.status:
        show_inventory_status(manager)

    if args.alerts:
        show_low_stock_alerts(manager)

    if args.sales:
        show_sales_summary(manager, days=args.days)

    if args.forecast:
        show_forecasts(manager, product_id=args.product, days=args.days)

    if args.reorder:
        show_reorder_recommendations(manager)


if __name__ == "__main__":
    main()
