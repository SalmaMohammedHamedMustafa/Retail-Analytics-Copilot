import sqlite3
import pandas as pd
import os

DB_PATH = "data/northwind.sqlite"

def inspect():
    if not os.path.exists(DB_PATH):
        print(f"Error: DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=== 1. REAL TABLE NAMES ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(tables)

    # We want to check these specific concepts
    check_list = [
        "Orders", 
        "Order Details", 
        "Products", 
        "Categories", 
        "Customers",
        "orders",       # Check if lowercase views exist
        "order_items"   # Check if lowercase views exist
    ]

    print("\n=== 2. COLUMN CHECK ===")
    for t in check_list:
        if t not in tables and t not in [x.lower() for x in tables]:
            # Try to match case-insensitive
            continue
            
        print(f"\n--- TABLE: {t} ---")
        try:
            # Get columns
            cols = pd.read_sql_query(f"PRAGMA table_info('{t}')", conn)
            col_names = cols['name'].tolist()
            print(f"Columns: {col_names}")
            
            # Check for Date columns and print a sample
            date_cols = [c for c in col_names if 'Date' in c]
            if date_cols:
                sample = pd.read_sql_query(f"SELECT {', '.join(date_cols)} FROM '{t}' LIMIT 3", conn)
                print(f"Date Samples:\n{sample.to_string(index=False)}")
                
        except Exception as e:
            print(f"Could not read: {e}")

    conn.close()

if __name__ == "__main__":
    inspect()