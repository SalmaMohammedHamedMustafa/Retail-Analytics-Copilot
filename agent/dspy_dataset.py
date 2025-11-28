import dspy
# 40 examples 
train_data = [
    #  CATEGORY 1: GLOBAL TOTALS (No Grouping) - 10 examples 
    
    dspy.Example(
        question="What is the total revenue for all time?",
        plan_constraints="TIME_SCOPE: ALL_TIME, RANKING_INTENT: None, FILTERS: None",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Calculate the global Average Order Value (AOV) for 2017.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: None, FILTERS: None",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity * (1 - COALESCE(oi.Discount, 0))) / COUNT(DISTINCT o.OrderID) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Total revenue from Beverages in 2017?",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: None, FILTERS: Category = 'Beverages'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' AND c.CategoryName = 'Beverages'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="How many units of Tofu were sold in 2016?",
        plan_constraints="TIME_SCOPE: 2016, RANKING_INTENT: None, FILTERS: Product = 'Tofu'",
        sql_query="SELECT SUM(oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID WHERE o.OrderDate >= '2016-01-01' AND o.OrderDate <= '2016-12-31' AND p.ProductName = 'Tofu'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Total revenue excluding discounts for Seafood all time.",
        plan_constraints="TIME_SCOPE: ALL_TIME, RANKING_INTENT: None, FILTERS: Category = 'Seafood'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE c.CategoryName = 'Seafood'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Total quantity sold for Confections in December 2017?",
        plan_constraints="TIME_SCOPE: 2017-12, RANKING_INTENT: None, FILTERS: Category = 'Confections'",
        sql_query="SELECT SUM(oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-12-01' AND o.OrderDate <= '2017-12-31' AND c.CategoryName = 'Confections'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Revenue from Dairy Products in June 2017?",
        plan_constraints="TIME_SCOPE: 2017-06, RANKING_INTENT: None, FILTERS: Category = 'Dairy Products'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-06-01' AND o.OrderDate <= '2017-06-30' AND c.CategoryName = 'Dairy Products'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Count of orders in April 2017.",
        plan_constraints="TIME_SCOPE: 2017-04, RANKING_INTENT: None, FILTERS: None",
        sql_query="SELECT COUNT(DISTINCT o.OrderID) FROM orders o WHERE o.OrderDate >= '2017-04-01' AND o.OrderDate <= '2017-04-30'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Total freight cost for orders in 2017.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: None, FILTERS: None",
        sql_query="SELECT SUM(o.Freight) FROM orders o WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Revenue from Produce on 2017-01-01.",
        plan_constraints="TIME_SCOPE: 2017-01-01, RANKING_INTENT: None, FILTERS: Category = 'Produce'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate = '2017-01-01' AND c.CategoryName = 'Produce'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    #  CATEGORY 2: RANKINGS (Must Group By) - 15 examples 
    
    dspy.Example(
        question="Who is the top customer by revenue all time?",
        plan_constraints="TIME_SCOPE: ALL_TIME, RANKING_INTENT: Top 1 Customer, FILTERS: None",
        sql_query="SELECT cust.CompanyName, SUM(oi.UnitPrice * oi.Quantity) as Val FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN customers cust ON o.CustomerID = cust.CustomerID GROUP BY cust.CompanyName ORDER BY Val DESC LIMIT 1"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top 3 products by sales quantity in 2017.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: Top 3 Products, FILTERS: None",
        sql_query="SELECT p.ProductName, SUM(oi.Quantity) as Val FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' GROUP BY p.ProductName ORDER BY Val DESC LIMIT 3"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Which category generated the most revenue in August 2016?",
        plan_constraints="TIME_SCOPE: 2016-08, RANKING_INTENT: Top 1 Category, FILTERS: None",
        sql_query="SELECT c.CategoryName, SUM(oi.UnitPrice * oi.Quantity) as Val FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2016-08-01' AND o.OrderDate <= '2016-08-31' GROUP BY c.CategoryName ORDER BY Val DESC LIMIT 1"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top 5 customers by revenue for Dairy Products in 2017.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: Top 5 Customers, FILTERS: Category = 'Dairy Products'",
        sql_query="SELECT cust.CompanyName, SUM(oi.UnitPrice * oi.Quantity) as Val FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN customers cust ON o.CustomerID = cust.CustomerID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' AND c.CategoryName = 'Dairy Products' GROUP BY cust.CompanyName ORDER BY Val DESC LIMIT 5"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Best selling product by revenue in 2018?",
        plan_constraints="TIME_SCOPE: 2018, RANKING_INTENT: Top 1 Product, FILTERS: None",
        sql_query="SELECT p.ProductName, SUM(oi.UnitPrice * oi.Quantity) as Val FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID WHERE o.OrderDate >= '2018-01-01' AND o.OrderDate <= '2018-12-31' GROUP BY p.ProductName ORDER BY Val DESC LIMIT 1"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Which category had highest sales in June 2017?",
        plan_constraints="TIME_SCOPE: 2017-06, RANKING_INTENT: Top 1 Category, FILTERS: None",
        sql_query="SELECT c.CategoryName, SUM(oi.Quantity) as Val FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-06-01' AND o.OrderDate <= '2017-06-30' GROUP BY c.CategoryName ORDER BY Val DESC LIMIT 1"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top 3 customers by order count in 2017.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: Top 3 Customers, FILTERS: None",
        sql_query="SELECT cust.CompanyName, COUNT(DISTINCT o.OrderID) as OrderCount FROM orders o JOIN customers cust ON o.CustomerID = cust.CustomerID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' GROUP BY cust.CompanyName ORDER BY OrderCount DESC LIMIT 3"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top 2 categories by total revenue in 2017.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: Top 2 Categories, FILTERS: None",
        sql_query="SELECT c.CategoryName, SUM(oi.UnitPrice * oi.Quantity) as Revenue FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' GROUP BY c.CategoryName ORDER BY Revenue DESC LIMIT 2"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Which supplier had the most products sold in 2017?",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: Top 1 Supplier, FILTERS: None",
        sql_query="SELECT s.CompanyName, SUM(oi.Quantity) as Val FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN Suppliers s ON p.SupplierID = s.SupplierID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' GROUP BY s.CompanyName ORDER BY Val DESC LIMIT 1"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top 3 products by revenue in 2016?",
        plan_constraints="TIME_SCOPE: 2016, RANKING_INTENT: Top 3 Products, FILTERS: None",
        sql_query="SELECT p.ProductName, SUM(oi.UnitPrice * oi.Quantity * (1 - COALESCE(oi.Discount, 0))) as Revenue FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID WHERE o.OrderDate >= '2016-01-01' AND o.OrderDate <= '2016-12-31' GROUP BY p.ProductName ORDER BY Revenue DESC LIMIT 3"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Which category sold the most units in September 2017?",
        plan_constraints="TIME_SCOPE: 2017-09, RANKING_INTENT: Top 1 Category, FILTERS: None",
        sql_query="SELECT c.CategoryName, SUM(oi.Quantity) as Val FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-09-01' AND o.OrderDate <= '2017-09-30' GROUP BY c.CategoryName ORDER BY Val DESC LIMIT 1"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top 2 customers by revenue in Beverages category all time?",
        plan_constraints="TIME_SCOPE: ALL_TIME, RANKING_INTENT: Top 2 Customers, FILTERS: Category = 'Beverages'",
        sql_query="SELECT cust.CompanyName, SUM(oi.UnitPrice * oi.Quantity) as Revenue FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN customers cust ON o.CustomerID = cust.CustomerID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE c.CategoryName = 'Beverages' GROUP BY cust.CompanyName ORDER BY Revenue DESC LIMIT 2"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top product by quantity sold in Seafood category in 2017?",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: Top 1 Product, FILTERS: Category = 'Seafood'",
        sql_query="SELECT p.ProductName, SUM(oi.Quantity) as Val FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' AND c.CategoryName = 'Seafood' GROUP BY p.ProductName ORDER BY Val DESC LIMIT 1"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Which category had the highest revenue in Q1 2017?",
        plan_constraints="TIME_SCOPE: 2017-Q1, RANKING_INTENT: Top 1 Category, FILTERS: None",
        sql_query="SELECT c.CategoryName, SUM(oi.UnitPrice * oi.Quantity) as Revenue FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-03-31' GROUP BY c.CategoryName ORDER BY Revenue DESC LIMIT 1"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top 5 products by revenue in December 2017?",
        plan_constraints="TIME_SCOPE: 2017-12, RANKING_INTENT: Top 5 Products, FILTERS: None",
        sql_query="SELECT p.ProductName, SUM(oi.UnitPrice * oi.Quantity) as Revenue FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID WHERE o.OrderDate >= '2017-12-01' AND o.OrderDate <= '2017-12-31' GROUP BY p.ProductName ORDER BY Revenue DESC LIMIT 5"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    # CATEGORY 3: AOV & FORMULAS - 8 examples 
    
    dspy.Example(
        question="Average Order Value for Queen Cozinha in 2017.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: None, FILTERS: Customer = 'Queen Cozinha'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity * (1 - COALESCE(oi.Discount, 0))) / COUNT(DISTINCT o.OrderID) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN customers cust ON o.CustomerID = cust.CustomerID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' AND cust.CompanyName = 'Queen Cozinha'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="What is the AOV for 2018?",
        plan_constraints="TIME_SCOPE: 2018, RANKING_INTENT: None, FILTERS: None",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity * (1 - COALESCE(oi.Discount, 0))) / COUNT(DISTINCT o.OrderID) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate >= '2018-01-01' AND o.OrderDate <= '2018-12-31'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="AOV for Beverages category in 2017?",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: None, FILTERS: Category = 'Beverages'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity * (1 - COALESCE(oi.Discount, 0))) / COUNT(DISTINCT o.OrderID) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' AND c.CategoryName = 'Beverages'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Average Order Value in December 2017?",
        plan_constraints="TIME_SCOPE: 2017-12, RANKING_INTENT: None, FILTERS: None",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity * (1 - COALESCE(oi.Discount, 0))) / COUNT(DISTINCT o.OrderID) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate >= '2017-12-01' AND o.OrderDate <= '2017-12-31'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top customer by gross margin in 2017. Margin = (Price - Cost) * Qty.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: Top 1 Customer, FILTERS: None",
        sql_query="SELECT cust.CompanyName, SUM((oi.UnitPrice - (0.7 * oi.UnitPrice)) * oi.Quantity) as Margin FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN customers cust ON o.CustomerID = cust.CustomerID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' GROUP BY cust.CompanyName ORDER BY Margin DESC LIMIT 1"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Total gross margin for all orders in 2017. Use Cost = 0.7 * Price.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: None, FILTERS: None",
        sql_query="SELECT SUM((oi.UnitPrice - (0.7 * oi.UnitPrice)) * oi.Quantity * (1 - COALESCE(oi.Discount, 0))) as TotalMargin FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Average discount rate applied in 2017?",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: None, FILTERS: None",
        sql_query="SELECT AVG(oi.Discount) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Gross margin for Dairy Products in 2017? Cost = 0.7 * Price.",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: None, FILTERS: Category = 'Dairy Products'",
        sql_query="SELECT SUM((oi.UnitPrice - (0.7 * oi.UnitPrice)) * oi.Quantity) as Margin FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' AND c.CategoryName = 'Dairy Products'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    # CATEGORY 4: BEVERAGE-SPECIFIC (Critical for eval) - 7 examples 
    
    dspy.Example(
        question="Give me the total sales of Beverages.",
        plan_constraints="TIME_SCOPE: ALL_TIME, RANKING_INTENT: None, FILTERS: Category = 'Beverages'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE c.CategoryName = 'Beverages'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Revenue from Beverages in summer 2017 (June-August)?",
        plan_constraints="TIME_SCOPE: 2017-06 to 2017-08, RANKING_INTENT: None, FILTERS: Category = 'Beverages'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-06-01' AND o.OrderDate <= '2017-08-31' AND c.CategoryName = 'Beverages'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Total quantity of Beverages sold in June 2017?",
        plan_constraints="TIME_SCOPE: 2017-06, RANKING_INTENT: None, FILTERS: Category = 'Beverages'",
        sql_query="SELECT SUM(oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-06-01' AND o.OrderDate <= '2017-06-30' AND c.CategoryName = 'Beverages'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Revenue from Beverages in July 2017?",
        plan_constraints="TIME_SCOPE: 2017-07, RANKING_INTENT: None, FILTERS: Category = 'Beverages'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-07-01' AND o.OrderDate <= '2017-07-31' AND c.CategoryName = 'Beverages'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="How many Beverage orders were placed in 2017?",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: None, FILTERS: Category = 'Beverages'",
        sql_query="SELECT COUNT(DISTINCT o.OrderID) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' AND c.CategoryName = 'Beverages'"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Top 3 Beverage products by revenue in 2017?",
        plan_constraints="TIME_SCOPE: 2017, RANKING_INTENT: Top 3 Products, FILTERS: Category = 'Beverages'",
        sql_query="SELECT p.ProductName, SUM(oi.UnitPrice * oi.Quantity) as Revenue FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-01-01' AND o.OrderDate <= '2017-12-31' AND c.CategoryName = 'Beverages' GROUP BY p.ProductName ORDER BY Revenue DESC LIMIT 3"
    ).with_inputs("question", "plan_constraints", "schema_context"),

    dspy.Example(
        question="Revenue from Beverages and Condiments combined in June 2017?",
        plan_constraints="TIME_SCOPE: 2017-06, RANKING_INTENT: None, FILTERS: Categories = 'Beverages, Condiments'",
        sql_query="SELECT SUM(oi.UnitPrice * oi.Quantity) FROM order_items oi JOIN orders o ON oi.OrderID = o.OrderID JOIN products p ON oi.ProductID = p.ProductID JOIN categories c ON p.CategoryID = c.CategoryID WHERE o.OrderDate >= '2017-06-01' AND o.OrderDate <= '2017-06-30' AND c.CategoryName IN ('Beverages', 'Condiments')"
    ).with_inputs("question", "plan_constraints", "schema_context"),
]
