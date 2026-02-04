"""Utility functions for CSV import/export and data handling."""

import csv
from datetime import date, datetime
from typing import Optional

from .models import PurchaseOrder, SKU, MonthlyProjection


def parse_date(date_str: str) -> date:
    """Parse date string in various formats."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y"]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_str}")


def parse_float(value: str, default: float = 0.0) -> float:
    """Parse float from string, handling percentages."""
    value = value.strip()
    if not value:
        return default

    # Handle percentage format (e.g., "5%" -> 0.05)
    if value.endswith('%'):
        return float(value[:-1]) / 100

    return float(value)


def load_skus_from_csv(filepath: str) -> list[SKU]:
    """
    Load SKUs from CSV file.

    Expected columns:
    - sku: SKU identifier (required)
    - name: Product name (required)
    - current_inventory: Current stock on hand (required)
    - current_monthly_sales: Current monthly sales rate - baseline demand (required)
    - growth_rate: Monthly growth rate, e.g., 0.05 or 5% (optional, default 0)
    """
    skus = []

    with open(filepath, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            sku = SKU(
                sku=row['sku'].strip(),
                name=row['name'].strip(),
                current_inventory=int(row['current_inventory']),
                current_monthly_sales=float(row['current_monthly_sales']),
                growth_rate=parse_float(row.get('growth_rate', '0')),
            )
            skus.append(sku)

    return skus


def load_pos_from_csv(filepath: str) -> list[PurchaseOrder]:
    """
    Load Purchase Orders from CSV file.

    Expected columns:
    - po_number: PO identifier (required)
    - sku: SKU identifier (required)
    - quantity: Units ordered (required)
    - expected_arrival: Expected arrival date (required)
    """
    pos = []

    with open(filepath, 'r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            po = PurchaseOrder(
                po_number=row['po_number'].strip(),
                sku=row['sku'].strip(),
                quantity=int(row['quantity']),
                expected_arrival=parse_date(row['expected_arrival']),
            )
            pos.append(po)

    return pos


def export_projections_to_csv(
    projections: dict[str, list[MonthlyProjection]], filepath: str
) -> None:
    """
    Export projections to CSV file.

    Creates a worksheet-style output with months as columns.
    """
    if not projections:
        return

    # Get all months from first SKU's projections
    first_sku = next(iter(projections.values()))
    months = [p.month_label for p in first_sku]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header row
        header = ['SKU', 'Name', 'Metric'] + months
        writer.writerow(header)

        # Write each SKU's data
        for sku_id, sku_projections in projections.items():
            sku_name = sku_projections[0].sku_name if sku_projections else ''

            # Beginning Inventory row
            row = [sku_id, sku_name, 'Beginning Inventory']
            row.extend([p.beginning_inventory for p in sku_projections])
            writer.writerow(row)

            # Incoming POs row
            row = [sku_id, sku_name, 'Incoming POs']
            row.extend([p.incoming_pos for p in sku_projections])
            writer.writerow(row)

            # Projected Sales row
            row = [sku_id, sku_name, 'Projected Sales']
            row.extend([p.projected_sales for p in sku_projections])
            writer.writerow(row)

            # Ending Inventory row
            row = [sku_id, sku_name, 'Ending Inventory']
            row.extend([p.ending_inventory for p in sku_projections])
            writer.writerow(row)

            # Empty row between SKUs
            writer.writerow([])


def generate_sample_skus() -> list[SKU]:
    """Generate sample SKU data for demo."""
    return [
        # SKU(sku, name, current_inventory, current_monthly_sales, growth_rate)
        SKU("DOG-FOOD-001", "Premium Dog Food 15lb", 500, 120, 0.03),
        SKU("DOG-FOOD-002", "Puppy Formula 5lb", 200, 80, 0.05),
        SKU("CAT-FOOD-001", "Premium Cat Food 10lb", 400, 100, 0.02),
        SKU("CAT-FOOD-002", "Kitten Formula 5lb", 150, 45, 0.04),
        SKU("DOG-TOY-001", "Squeaky Ball Set", 300, 75, 0.0),
        SKU("DOG-TOY-002", "Rope Tug Toy", 250, 60, 0.02),
        SKU("CAT-TOY-001", "Feather Wand", 200, 50, 0.01),
        SKU("TREAT-001", "Dog Training Treats", 400, 90, 0.03),
        SKU("TREAT-002", "Cat Treats Variety", 350, 70, 0.02),
        SKU("COLLAR-001", "Adjustable Dog Collar M", 150, 35, 0.0),
        SKU("LEASH-001", "Retractable Leash 16ft", 100, 25, 0.01),
        SKU("BED-001", "Orthopedic Dog Bed L", 80, 20, 0.02),
    ]


def generate_sample_pos(start_date: Optional[date] = None) -> list[PurchaseOrder]:
    """Generate sample purchase orders for demo."""
    if start_date is None:
        start_date = date.today()

    # Generate POs arriving over the next few months
    year = start_date.year
    month = start_date.month

    def future_date(months_ahead: int, day: int = 15) -> date:
        m = month + months_ahead
        y = year + (m - 1) // 12
        m = (m - 1) % 12 + 1
        return date(y, m, min(day, 28))

    return [
        PurchaseOrder("PO-001", "DOG-FOOD-001", 300, future_date(1, 10)),
        PurchaseOrder("PO-002", "DOG-FOOD-001", 300, future_date(3, 15)),
        PurchaseOrder("PO-003", "DOG-FOOD-002", 200, future_date(1, 5)),
        PurchaseOrder("PO-004", "CAT-FOOD-001", 250, future_date(2, 20)),
        PurchaseOrder("PO-005", "CAT-FOOD-001", 250, future_date(4, 10)),
        PurchaseOrder("PO-006", "CAT-FOOD-002", 150, future_date(2, 1)),
        PurchaseOrder("PO-007", "DOG-TOY-001", 200, future_date(1, 25)),
        PurchaseOrder("PO-008", "DOG-TOY-002", 150, future_date(3, 5)),
        PurchaseOrder("PO-009", "TREAT-001", 300, future_date(2, 15)),
        PurchaseOrder("PO-010", "TREAT-002", 200, future_date(2, 15)),
        PurchaseOrder("PO-011", "BED-001", 50, future_date(1, 20)),
        PurchaseOrder("PO-012", "BED-001", 50, future_date(4, 10)),
    ]


def create_sample_csv_files(directory: str = ".") -> tuple[str, str]:
    """Create sample CSV files for testing."""
    import os

    # Create SKUs CSV
    skus_path = os.path.join(directory, "sample_skus.csv")
    with open(skus_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['sku', 'name', 'current_inventory', 'current_monthly_sales', 'growth_rate'])
        for sku in generate_sample_skus():
            writer.writerow([
                sku.sku,
                sku.name,
                sku.current_inventory,
                sku.current_monthly_sales,
                f"{sku.growth_rate:.0%}" if sku.growth_rate else "0%"
            ])

    # Create POs CSV
    pos_path = os.path.join(directory, "sample_pos.csv")
    with open(pos_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['po_number', 'sku', 'quantity', 'expected_arrival'])
        for po in generate_sample_pos():
            writer.writerow([
                po.po_number,
                po.sku,
                po.quantity,
                po.expected_arrival.isoformat()
            ])

    return skus_path, pos_path
