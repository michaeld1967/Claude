"""Main CLI application for pet inventory projection."""

import argparse
import sys
from datetime import date

from .inventory import InventoryProjector
from .models import MonthlyProjection
from .utils import (
    create_sample_csv_files,
    export_projections_to_csv,
    generate_sample_pos,
    generate_sample_skus,
    load_pos_from_csv,
    load_skus_from_csv,
)


def print_worksheet(projections: dict[str, list[MonthlyProjection]]) -> None:
    """Print projections as a formatted worksheet."""
    if not projections:
        print("No projections to display.")
        return

    # Get months from first SKU
    first_sku = next(iter(projections.values()))
    months = [p.month_label for p in first_sku]

    # Calculate column widths
    sku_width = max(len(sku) for sku in projections.keys())
    name_width = min(25, max(len(p[0].sku_name) for p in projections.values()))
    month_width = 10

    # Print header
    header = f"{'SKU':<{sku_width}} | {'Name':<{name_width}} | {'Metric':<18}"
    for month in months:
        header += f" | {month:>{month_width}}"
    print("=" * len(header))
    print("MONTHLY INVENTORY PROJECTION WORKSHEET")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    # Print each SKU
    for sku_id, sku_projections in projections.items():
        sku_name = sku_projections[0].sku_name[:name_width] if sku_projections else ''

        # Beginning Inventory
        row = f"{sku_id:<{sku_width}} | {sku_name:<{name_width}} | {'Begin Inv':<18}"
        for p in sku_projections:
            row += f" | {p.beginning_inventory:>{month_width}}"
        print(row)

        # Incoming POs
        row = f"{'':<{sku_width}} | {'':<{name_width}} | {'+ Incoming POs':<18}"
        for p in sku_projections:
            val = p.incoming_pos if p.incoming_pos > 0 else "-"
            row += f" | {str(val):>{month_width}}"
        print(row)

        # Projected Sales
        row = f"{'':<{sku_width}} | {'':<{name_width}} | {'- Projected Sales':<18}"
        for p in sku_projections:
            row += f" | {p.projected_sales:>{month_width}.0f}"
        print(row)

        # Ending Inventory (highlight negative values)
        row = f"{'':<{sku_width}} | {'':<{name_width}} | {'= Ending Inv':<18}"
        for p in sku_projections:
            if p.ending_inventory < 0:
                val = f"({abs(p.ending_inventory):.0f})"  # Parentheses for negative
            else:
                val = f"{p.ending_inventory:.0f}"
            row += f" | {val:>{month_width}}"
        print(row)

        print("-" * len(header))


def print_stockout_alerts(alerts: list[MonthlyProjection]) -> None:
    """Print stockout warnings."""
    if not alerts:
        print("\nNo stockout risks detected in the projection period.")
        return

    print("\n" + "=" * 60)
    print("STOCKOUT ALERTS")
    print("=" * 60)

    for alert in alerts:
        print(f"  WARNING: {alert.sku_name} ({alert.sku})")
        print(f"           Stockout in {alert.month_label}")
        print(f"           Projected ending inventory: {alert.ending_inventory:.0f}")
        print()


def print_summary(projections: dict[str, list[MonthlyProjection]]) -> None:
    """Print summary statistics."""
    total_skus = len(projections)

    # Count stockouts
    stockouts = []
    for sku_id, sku_projs in projections.items():
        for p in sku_projs:
            if p.ending_inventory < 0:
                stockouts.append((sku_id, p.month_label, p.ending_inventory))
                break

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total SKUs projected: {total_skus}")
    print(f"  SKUs with stockout risk: {len(stockouts)}")

    if stockouts:
        print("\n  Stockout risks:")
        for sku, month, inv in stockouts:
            print(f"    - {sku}: stockout in {month} (ending inv: {inv:.0f})")


def run_demo() -> None:
    """Run demo with sample data."""
    print("\n" + "=" * 70)
    print("PET INVENTORY PROJECTION - DEMO")
    print("=" * 70)

    # Create projector with sample data
    projector = InventoryProjector()

    skus = generate_sample_skus()
    pos = generate_sample_pos()

    print(f"\nLoading {len(skus)} SKUs...")
    for sku in skus:
        projector.add_sku(sku)
        print(f"  {sku.sku}: {sku.name}")
        print(f"    Inventory: {sku.current_inventory}, Current Sales: {sku.current_monthly_sales}/mo, Growth: {sku.growth_rate:.0%}")

    print(f"\nLoading {len(pos)} Purchase Orders...")
    for po in pos:
        projector.add_purchase_order(po)
        print(f"  {po.po_number}: {po.sku} x{po.quantity} arriving {po.expected_arrival}")

    # Generate projections
    print("\nGenerating 12-month projection...\n")
    projections = projector.project_all(num_months=12)

    # Print worksheet
    print_worksheet(projections)

    # Print alerts and summary
    alerts = projector.get_stockout_alerts(num_months=12)
    print_stockout_alerts(alerts)
    print_summary(projections)

    print("\n" + "=" * 70)
    print("END OF DEMO")
    print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pet Inventory Projection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Workflow:
  1. Create a SKU CSV with your products, inventory, monthly sales, and growth rates
  2. Create a PO CSV with your incoming purchase orders
  3. Run the projection to see monthly ending inventory

Examples:
  # Run demo with sample data
  python -m pet_inventory.main --demo

  # Create sample CSV templates
  python -m pet_inventory.main --create-samples

  # Run projection with your data
  python -m pet_inventory.main --skus my_skus.csv --pos my_pos.csv

  # Project 6 months and export to CSV
  python -m pet_inventory.main --skus skus.csv --pos pos.csv --months 6 --output projection.csv

CSV Formats:
  SKUs (skus.csv):
    sku,name,current_inventory,current_monthly_sales,growth_rate
    DOG-FOOD-001,Premium Dog Food,500,120,3%

  Purchase Orders (pos.csv):
    po_number,sku,quantity,expected_arrival
    PO-001,DOG-FOOD-001,300,2026-03-15
        """,
    )

    parser.add_argument("--demo", action="store_true", help="Run demo with sample data")
    parser.add_argument("--create-samples", action="store_true", help="Create sample CSV files")
    parser.add_argument("--skus", type=str, help="Path to SKUs CSV file")
    parser.add_argument("--pos", type=str, help="Path to Purchase Orders CSV file")
    parser.add_argument("--months", type=int, default=12, help="Number of months to project (default: 12)")
    parser.add_argument("--output", "-o", type=str, help="Export projections to CSV file")

    args = parser.parse_args()

    # Show help if no arguments
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # Create sample files
    if args.create_samples:
        skus_path, pos_path = create_sample_csv_files()
        print(f"Created sample files:")
        print(f"  SKUs: {skus_path}")
        print(f"  POs: {pos_path}")
        print("\nEdit these files with your data, then run:")
        print(f"  python -m pet_inventory.main --skus {skus_path} --pos {pos_path}")
        return

    # Run demo
    if args.demo:
        run_demo()
        return

    # Run projection with provided files
    if not args.skus:
        print("Error: --skus file is required")
        print("Use --create-samples to generate template files")
        return

    projector = InventoryProjector()

    # Load SKUs
    try:
        skus = load_skus_from_csv(args.skus)
        print(f"Loaded {len(skus)} SKUs from {args.skus}")
        for sku in skus:
            projector.add_sku(sku)
    except Exception as e:
        print(f"Error loading SKUs: {e}")
        return

    # Load POs (optional)
    if args.pos:
        try:
            pos = load_pos_from_csv(args.pos)
            print(f"Loaded {len(pos)} Purchase Orders from {args.pos}")
            for po in pos:
                projector.add_purchase_order(po)
        except Exception as e:
            print(f"Error loading POs: {e}")
            return

    # Generate projections
    print(f"\nProjecting {args.months} months...\n")
    projections = projector.project_all(num_months=args.months)

    # Print worksheet
    print_worksheet(projections)

    # Print alerts and summary
    alerts = projector.get_stockout_alerts(num_months=args.months)
    print_stockout_alerts(alerts)
    print_summary(projections)

    # Export to CSV if requested
    if args.output:
        export_projections_to_csv(projections, args.output)
        print(f"\nProjections exported to: {args.output}")


if __name__ == "__main__":
    main()
