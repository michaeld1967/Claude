"""Utility functions for pet inventory system."""

import csv
from datetime import date, datetime, timedelta
import random
from typing import Optional

from .models import Category, Product, Sale


def parse_date(date_str: str) -> date:
    """Parse date string in various formats."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_str}")


def load_sales_from_csv(filepath: str) -> list[Sale]:
    """Load sales data from CSV file."""
    sales = []

    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            sale = Sale(
                date=parse_date(row["date"]),
                product_id=row["product_id"],
                quantity=int(row["quantity"]),
                unit_price=float(row.get("unit_price", 0)) or None,
            )
            sales.append(sale)

    return sales


def export_sales_to_csv(sales: list[Sale], filepath: str) -> None:
    """Export sales data to CSV file."""
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["date", "product_id", "quantity", "unit_price"]
        )
        writer.writeheader()

        for sale in sales:
            writer.writerow(
                {
                    "date": sale.date.isoformat(),
                    "product_id": sale.product_id,
                    "quantity": sale.quantity,
                    "unit_price": sale.unit_price or "",
                }
            )


def generate_sample_products() -> list[Product]:
    """Generate sample pet products for demo."""
    products = [
        # Food
        Product("FOOD-001", "Premium Dog Food (15lb)", Category.FOOD, 45.99, 15, 30, 5),
        Product("FOOD-002", "Premium Cat Food (10lb)", Category.FOOD, 35.99, 20, 40, 5),
        Product("FOOD-003", "Puppy Formula (5lb)", Category.FOOD, 24.99, 10, 25, 5),
        Product("FOOD-004", "Senior Dog Food (15lb)", Category.FOOD, 48.99, 12, 25, 5),
        Product("FOOD-005", "Grain-Free Cat Food (8lb)", Category.FOOD, 39.99, 15, 30, 5),
        # Toys
        Product("TOY-001", "Squeaky Ball Set", Category.TOYS, 12.99, 20, 50, 7),
        Product("TOY-002", "Cat Teaser Wand", Category.TOYS, 8.99, 25, 60, 7),
        Product("TOY-003", "Rope Tug Toy", Category.TOYS, 9.99, 15, 40, 7),
        Product("TOY-004", "Catnip Mouse (3-pack)", Category.TOYS, 6.99, 30, 75, 7),
        # Accessories
        Product("ACC-001", "Dog Collar (Medium)", Category.ACCESSORIES, 15.99, 10, 30, 7),
        Product("ACC-002", "Cat Collar with Bell", Category.ACCESSORIES, 8.99, 15, 40, 7),
        Product("ACC-003", "Retractable Leash", Category.ACCESSORIES, 24.99, 8, 20, 7),
        Product("ACC-004", "Pet ID Tag", Category.ACCESSORIES, 5.99, 25, 100, 10),
        # Medication/Health
        Product("MED-001", "Flea & Tick Treatment (Dogs)", Category.MEDICATION, 49.99, 10, 25, 3),
        Product("MED-002", "Flea & Tick Treatment (Cats)", Category.MEDICATION, 44.99, 10, 25, 3),
        Product("MED-003", "Pet Vitamins", Category.MEDICATION, 19.99, 12, 30, 5),
        Product("MED-004", "Joint Supplements", Category.MEDICATION, 29.99, 8, 20, 5),
        # Grooming
        Product("GROOM-001", "Pet Shampoo", Category.GROOMING, 12.99, 15, 40, 7),
        Product("GROOM-002", "Deshedding Brush", Category.GROOMING, 18.99, 8, 20, 7),
        Product("GROOM-003", "Nail Clippers", Category.GROOMING, 11.99, 10, 25, 7),
        # Bedding
        Product("BED-001", "Dog Bed (Large)", Category.BEDDING, 59.99, 5, 15, 10),
        Product("BED-002", "Cat Tree (48\")", Category.BEDDING, 89.99, 3, 8, 14),
        Product("BED-003", "Pet Blanket", Category.BEDDING, 19.99, 12, 30, 7),
    ]
    return products


def generate_sample_sales(
    products: list[Product], days: int = 90, seed: Optional[int] = None
) -> list[Sale]:
    """Generate realistic sample sales data for demo."""
    if seed is not None:
        random.seed(seed)

    sales = []
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Define base daily demand rates per category (units per day)
    category_demand = {
        Category.FOOD: (2, 8),  # min, max sales per day
        Category.TOYS: (1, 5),
        Category.ACCESSORIES: (0, 3),
        Category.MEDICATION: (1, 4),
        Category.GROOMING: (0, 3),
        Category.BEDDING: (0, 2),
    }

    # Add some seasonal patterns and trends
    current_date = start_date
    while current_date <= end_date:
        # Weekend boost (20% more sales)
        weekend_factor = 1.2 if current_date.weekday() >= 5 else 1.0

        # Slight upward trend over time
        day_number = (current_date - start_date).days
        trend_factor = 1.0 + (day_number / days) * 0.15

        for product in products:
            min_demand, max_demand = category_demand[product.category]

            # Calculate expected sales
            base_demand = random.uniform(min_demand, max_demand)
            adjusted_demand = base_demand * weekend_factor * trend_factor

            # Add some noise and randomness
            actual_sales = max(0, int(random.gauss(adjusted_demand, adjusted_demand * 0.3)))

            # Some products are more popular
            if "Premium" in product.name or "Flea" in product.name:
                actual_sales = int(actual_sales * 1.3)

            if actual_sales > 0:
                # Sometimes split into multiple transactions
                while actual_sales > 0:
                    qty = min(actual_sales, random.randint(1, 3))
                    sales.append(
                        Sale(
                            date=current_date,
                            product_id=product.product_id,
                            quantity=qty,
                            unit_price=product.unit_price,
                        )
                    )
                    actual_sales -= qty

        current_date += timedelta(days=1)

    return sales


def format_currency(amount: float) -> str:
    """Format amount as currency."""
    return f"${amount:,.2f}"


def format_table(headers: list[str], rows: list[list[str]], min_width: int = 10) -> str:
    """Format data as ASCII table."""
    # Calculate column widths
    widths = [max(min_width, len(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))

    # Build table
    lines = []

    # Header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("-" * len(header_line))

    # Rows
    for row in rows:
        row_line = " | ".join(
            str(cell).ljust(widths[i]) if i < len(widths) else str(cell)
            for i, cell in enumerate(row)
        )
        lines.append(row_line)

    return "\n".join(lines)
