# Pet Inventory Projection System

A Python-based inventory projection tool for pet businesses. Projects monthly ending inventory based on current stock, incoming purchase orders, monthly sales rates, and growth rates.

## Workflow

1. **Upload your SKUs** - Product list with current inventory, monthly sales, and growth rate
2. **Upload your POs** - Incoming purchase orders with expected arrival dates
3. **Run projection** - Get a monthly worksheet showing ending inventory for each month

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Run demo with sample data
python -m pet_inventory.main --demo

# Create sample CSV templates to fill in
python -m pet_inventory.main --create-samples

# Run projection with your data
python -m pet_inventory.main --skus my_skus.csv --pos my_pos.csv

# Project 6 months and export to CSV
python -m pet_inventory.main --skus skus.csv --pos pos.csv --months 6 --output projection.csv
```

## CSV File Formats

### SKUs File (required)

| Column | Description | Example |
|--------|-------------|---------|
| sku | Unique product identifier | DOG-FOOD-001 |
| name | Product name | Premium Dog Food 15lb |
| current_inventory | Current stock on hand | 500 |
| current_monthly_sales | Current monthly sales (baseline demand) | 120 |
| growth_rate | Monthly growth rate (optional) | 3% or 0.03 |

The `current_monthly_sales` is your baseline demand. The `growth_rate` is applied each month:
- Month 1: `current_monthly_sales × (1 + growth_rate)`
- Month 2: `current_monthly_sales × (1 + growth_rate)²`
- etc.

Example `skus.csv`:
```csv
sku,name,current_inventory,current_monthly_sales,growth_rate
DOG-FOOD-001,Premium Dog Food 15lb,500,120,3%
CAT-FOOD-001,Premium Cat Food 10lb,400,100,2%
DOG-TOY-001,Squeaky Ball Set,300,75,0%
```

### Purchase Orders File (optional)

| Column | Description | Example |
|--------|-------------|---------|
| po_number | PO identifier | PO-001 |
| sku | Product SKU | DOG-FOOD-001 |
| quantity | Units ordered | 300 |
| expected_arrival | Expected delivery date | 2026-03-15 |

Example `pos.csv`:
```csv
po_number,sku,quantity,expected_arrival
PO-001,DOG-FOOD-001,300,2026-03-15
PO-002,DOG-FOOD-001,300,2026-05-15
PO-003,CAT-FOOD-001,250,2026-04-20
```

## Output

The tool generates a monthly worksheet showing for each SKU:
- **Beginning Inventory** - Stock at start of month
- **Incoming POs** - Units arriving from purchase orders
- **Projected Sales** - Expected sales (with growth rate applied)
- **Ending Inventory** - Stock at end of month

Negative ending inventory indicates a **stockout risk**.

## Example Output

```
======================================================================
MONTHLY INVENTORY PROJECTION WORKSHEET
======================================================================
SKU          | Name                 | Metric             |   Feb 2026 |   Mar 2026 |   Apr 2026
----------------------------------------------------------------------------------------------
DOG-FOOD-001 | Premium Dog Food 15lb | Begin Inv         |        500 |        380 |        560
             |                      | + Incoming POs     |          - |        300 |          -
             |                      | - Projected Sales  |        120 |        124 |        127
             |                      | = Ending Inv       |        380 |        556 |        429
----------------------------------------------------------------------------------------------

STOCKOUT ALERTS
============================================================
  WARNING: Squeaky Ball Set (DOG-TOY-001)
           Stockout in Jun 2026
           Projected ending inventory: -75
```

## Project Structure

```
pet_inventory/
├── __init__.py      # Package initialization
├── main.py          # CLI application
├── models.py        # Data models (SKU, PurchaseOrder, MonthlyProjection)
├── inventory.py     # Projection engine
└── utils.py         # CSV import/export utilities
```
