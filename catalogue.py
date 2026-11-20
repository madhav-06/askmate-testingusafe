"""HomeShine's product list: read it from data/products_raw.csv and clean it.

The list came out of the shop's old billing software, so it is messy: prices are written five different ways, product
codes too, and some rows are empty or repeated. Every reply AskMate gives comes from this list, so it must be clean.
"""

import csv
from pathlib import Path

RAW = Path(__file__).parent / "data" / "products_raw.csv"


def tidy(text):
    """'  New   Smile ' becomes 'New Smile': no spaces at the ends, one space between words."""
    return " ".join((text or "").split())


def clean_price(text):
    """'₹ 11,500' and 'Rs. 9900/-' must both become a whole number of rupees, like 11500."""
    text = tidy(text)
    return int(text) if text.isdigit() else 0


def clean_code(text):
    """'opc-180', 'OPC180' and ' OPC 180 ' must all become 'OPC 180'."""
    return tidy(text)


def product_from(row):
    """One row of the file as one clean product."""
    return {
        "code": clean_code(row["code"]),
        "name": tidy(row["name"]).title(),
        "category": tidy(row["category"]).capitalize(),
        "size": tidy(row["size"]),
        "features": tidy(row["features"]),
        "colour": tidy(row["colour"]),
        "price": clean_price(row["price"]),
    }


def load_catalogue(path=RAW):
    """Every product in the file, cleaned."""
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [product_from(row) for row in rows]
