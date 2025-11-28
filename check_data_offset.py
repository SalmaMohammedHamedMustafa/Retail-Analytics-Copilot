import sqlite3
import pandas as pd

DB_PATH = "data/northwind.sqlite"

conn = sqlite3.connect(DB_PATH)

def count_orders_in_month(year, month):
    start_date = f"{year}-{month:02d}-01"
    # End date trick: just go to next month/year approx or use strict string matching
    # simple string match for YYYY-MM is easier
    query = f"""
    SELECT COUNT(*) as count 
    FROM Orders 
    WHERE OrderDate LIKE '{year}-{month:02d}%'
    """
    df = pd.read_sql_query(query, conn)
    return df['count'].iloc[0]

print("=== Hypothesis Check: Is the offset +20 Years? ===")

# 1. Check the "Marketing Calendar" target (June 1997)
print(f"Orders in June 1997 (Original): {count_orders_in_month(1997, 6)}")

# 2. Check the +20 year shift (June 2017)
print(f"Orders in June 2017 (+20 years): {count_orders_in_month(2017, 6)}")

# 3. Check specific start date to confirm alignement with Original Northwind (July 4, 1996)
first_order = pd.read_sql_query("SELECT Min(OrderDate) as first_date FROM Orders", conn)
print(f"\nFirst Order Date in DB: {first_order['first_date'].iloc[0]}")

# 4. Check Winter 1997 -> Winter 2017
print(f"Orders in Dec 2017 (+20 years): {count_orders_in_month(2017, 12)}")

conn.close()