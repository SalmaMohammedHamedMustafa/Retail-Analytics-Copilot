import dspy

class GenerateSQL(dspy.Signature):
    """
    You are a SQLite Expert.
    
    ### SCHEMA (LOWERCASE VIEWS)
    - orders (o): OrderID, CustomerID, OrderDate (YYYY-MM-DD)
    - order_items (oi): OrderID, ProductID, UnitPrice, Quantity, Discount
    - products (p): ProductID, ProductName, CategoryID (**NO CategoryName**)
    - categories (c): CategoryID, CategoryName (**CategoryName is HERE**)
    - customers (cust): CustomerID, CompanyName

    ### CRITICAL RULES
    1. **Join Orders:** ALWAYS `JOIN orders o ON oi.OrderID = o.OrderID` to filter by Date.
    2. **Join Categories:** To filter by "CategoryName", you MUST `JOIN categories c ON p.CategoryID = c.CategoryID`.
    3. **Dates:** Use `>=` and `<=`. **NEVER** use `BETWEEN`.
    4. **Grouping:**
       - If Plan says "Top X": `GROUP BY` the entity.
       - If Plan says "None": **DO NOT GROUP BY**. `SELECT SUM(...)`.
    
    ### FORMAT
    Return raw SQL only. No markdown.
    """

    question = dspy.InputField(desc="The user's business question")
    schema_context = dspy.InputField(desc="Schema info (usually implied, but kept for context)")
    plan_constraints = dspy.InputField(desc="The execution plan: Time Scope, Intent, Filters, Formulas")
    sql_query = dspy.OutputField(desc="Valid SQLite query string")
