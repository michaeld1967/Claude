# Pet Inventory Forecasting System

A Python-based inventory forecasting tool designed for pet businesses. Helps predict future inventory needs based on historical sales data.

## Features

- Track inventory for pet products (food, toys, accessories, medications, etc.)
- Record and analyze sales history
- Forecast future demand using multiple algorithms:
  - Simple Moving Average
  - Weighted Moving Average
  - Exponential Smoothing
- Generate reorder recommendations
- CSV import/export support

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Run the demo with sample data
python -m pet_inventory.main --demo

# Import your own sales data
python -m pet_inventory.main --import sales_data.csv

# Generate forecast for a specific product
python -m pet_inventory.main --forecast --product "Premium Dog Food" --days 30

# Show current inventory status
python -m pet_inventory.main --status
```

## Data Format

Sales data CSV should have the following columns:
- `date`: Sale date (YYYY-MM-DD)
- `product_id`: Unique product identifier
- `product_name`: Product name
- `quantity`: Units sold
- `category`: Product category (food, toys, accessories, medication, grooming)

## Project Structure

```
pet_inventory/
├── __init__.py
├── main.py           # CLI entry point
├── models.py         # Data models (Product, Sale, Inventory)
├── forecasting.py    # Forecasting algorithms
├── inventory.py      # Inventory management
└── utils.py          # Utility functions
```
