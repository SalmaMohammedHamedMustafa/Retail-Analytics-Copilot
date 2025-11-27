import sqlite3
import pandas as pd

DB_PATH = "data/northwind.sqlite"

# Map of "Clean Name" -> "Raw SQL Definition"
VIEWS = {
    "orders": 'SELECT * FROM Orders',
    "order_items": 'SELECT * FROM "Order Details"',
    "products": 'SELECT * FROM Products',
    "customers": 'SELECT * FROM Customers'
}
TARGET_TABLES = list(VIEWS.keys()) + ['Categories']

class SQLiteTool:
    def __init__(self):
        # Initialize views once safely
        self._init_views()

    def _init_views(self):
        """
        Safely ensures lowercase views exist. 
        Crucial: Does NOT drop existing objects to avoid 'use DROP TABLE' errors.
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for view_name, definition in VIEWS.items():
            try:
                # 1. Check if it exists (Table or View)
                cursor.execute(f"SELECT name FROM sqlite_master WHERE name='{view_name}'")
                if cursor.fetchone():
                    continue
                
                # 2. If not exists, create the view
                cursor.execute(f"CREATE VIEW {view_name} AS {definition}")
            except Exception:
                pass
                
        conn.commit()
        conn.close()

    def _get_date_range(self):
        """Helper to get the actual date range of orders to ground the agent."""
        try:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT MIN(OrderDate) as mn, MAX(OrderDate) as mx FROM Orders", conn)
            conn.close()
            if not df.empty:
                return f"{df.iloc[0]['mn']} to {df.iloc[0]['mx']}"
        except:
            pass
        return "Unknown"

    def get_schema(self):
        conn = sqlite3.connect(DB_PATH)
        lines = []
        
        # 1. Add Date Context
        date_range = self._get_date_range()
        lines.append(f"--- DATABASE TIMEFRAME: {date_range} ---")
        lines.append("NOTE: The database contains data shifted +20 years from the original 1997 dataset.")
        lines.append("(e.g., 1997-06-01 in docs = 2017-06-01 in DB)\n")

        # 2. Add Table Schemas
        for table in TARGET_TABLES:
            try:
                # PRAGMA table_info works for both Tables and Views
                query = f"PRAGMA table_info('{table}');"
                df = pd.read_sql_query(query, conn)
                
                # Manual override for order_items if introspection returns empty
                if table == 'order_items' and df.empty:
                    columns = "OrderID, ProductID, UnitPrice, Quantity, Discount"
                elif df.empty:
                    continue
                else:
                    columns = ", ".join(df['name'].tolist())
                lines.append(f"Table {table} has columns: {columns}")
            except:
                continue
        conn.close()
        return "\n".join(lines)
    
    def query(self, sql_query):
        # Allow SELECT and WITH clauses
        clean_sql = sql_query.lower().strip()
        if not (clean_sql.startswith("select") or clean_sql.startswith("with")):
            return "Error: Only SELECT queries are allowed."
        
        try:
            conn = sqlite3.connect(DB_PATH)
            # We do NOT run _init_views here to avoid locking/performance issues
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            
            if df.empty:
                return "Query executed successfully but returned no results."
            
            return df.to_string(index=False)
        except Exception as e:
            return f"SQL error occurred: {str(e)}"

if __name__ == "__main__":
    tool = SQLiteTool()
    print(tool.get_schema())