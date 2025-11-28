import json
import os
import urllib.request
import re
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from agent.tools.sqlite_tool import SQLiteTool
from agent.rag.retrieval import Retriever

import dspy
from agent.dspy_signatures import GenerateSQL

MODEL = "phi3.5:3.8b-mini-instruct-q4_K_M"

lm = dspy.LM(
    model="ollama/phi3.5:3.8b-mini-instruct-q4_K_M", 
    api_base="http://localhost:11434", 
    api_key="",
    temperature=0.0,
    num_ctx=6144
)
dspy.configure(lm=lm)

# Load the optimized SQL module
OPTIMIZED_SQL_PATH = "agent/sql_optimized.json"
if os.path.exists(OPTIMIZED_SQL_PATH):
    compiled_sql_module = dspy.Predict(GenerateSQL)
    compiled_sql_module.load(OPTIMIZED_SQL_PATH)
    USE_DSPY_SQL = True
else:
    compiled_sql_module = dspy.Predict(GenerateSQL)  
    USE_DSPY_SQL = True  

# Initialize DB Tool
db_tool = SQLiteTool()
schema_info = db_tool.get_schema()


#  Minimal Ollama Client 
def query_ollama(messages: List[Dict[str, str]], model: str = "phi3.5:3.8b-mini-instruct-q4_K_M", temperature: float = 0.0) -> str:
    """
    Sends a raw request to the local Ollama instance.
    """
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["message"]["content"]
    except Exception as e:
        return f"Error communicating with Ollama: {str(e)}"

# the Agent State 
class AgentState(TypedDict):
    question: str
    format_hint: str 
    classification: str 
    retrieved_docs: List[Dict[str, Any]] 
    sql_plan: str
    sql_query: str
    sql_result: str
    sql_valid: bool
    attempt_count: int
    final_answer: Any
    explanation: str
    citations: List[str]


def retriever_node(state: AgentState):
    print("--- Node: Retriever ---")
    question = state["question"]
    
    if Retriever:
        # Get top 3 chunks
        results = Retriever.search(question, top_k=3)
    else:
        results = []
        
    return {"retrieved_docs": results}

def classify_question_standard(question: str) -> str:
    """
    Classifies the user question into: 'rag' or 'hybrid'.
    
    Logic:
    - 'rag': Policy, text lookups, return windows, documentation questions.
    - 'hybrid': Any math, counting, database query, 'how many', 'top', 'revenue'.
    """
    system_instruction = """You are a Query Router.
Your task is to classify the User Question into one of two paths:

1. "rag": For static knowledge, policies, text lookup. (e.g. "What is the return policy?", "Days to return?")
2. "hybrid": For database queries, math, counting, rankings, or specific year data (1997).

### EXAMPLES
- "Return window for beverages?" -> "rag"
- "Top 3 products by sales?" -> "hybrid"
- "Revenue in 1997?" -> "hybrid"
- "Who is the best customer?" -> "hybrid"

### OUTPUT
Return a JSON object: {"classification": "..."}
"""
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"Question: {question}"}
    ]
    
    raw = query_ollama(messages, model=MODEL, temperature=0.0)
    
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return data.get("classification", "hybrid").lower()
    except:
        q = question.lower()
        if "how many" in q or "sum" in q or "count" in q or "total" in q or "1997" in q:
            return "hybrid"
        return "rag"

def router_node(state: AgentState):
    print("--- Node: Router ---")
    question = state["question"]
    
    # 1. Select Strategy (Toggle for DSPy later)
    use_dspy = False
    
    if use_dspy:
        # Placeholder for future DSPy module
        classification = classify_question_standard(question) 
    else:
        classification = classify_question_standard(question)
        
    print(f"   [Decision]: {classification}")
    
    return {"classification": classification}


def _apply_time_shift(text: str) -> str:
    """
    Finds years 1996-1999 in the text and adds 20 years.
    Returns the corrected text (e.g., 1997 -> 2017).
    """
    def replace_year(match):
        year = int(match.group(1))
        # Safety check: Only shift the specific Northwind years
        if 1996 <= year <= 1999:
            return str(year + 20)
        return match.group(0)
    
    # Regex for 4-digit years
    return re.sub(r'\b(199\d)\b', replace_year, text)

def planner_node(state: AgentState):
    print("--- Node: Planner ---")
    question = state["question"]
    docs = state.get("retrieved_docs", [])
    
    docs_text = ""
    if docs:
        docs_text = "RETRIEVED KNOWLEDGE:\n" + \
                    "\n\n".join([f"-- Source: {d['id']}\n{d['text']}" for d in docs])
    
    system_instruction = """You are a Query Parameter Extractor.

### TIME SHIFT RULES
- 1996 -> 2016, 1997 -> 2017, 1998 -> 2018

### INSTRUCTIONS
1. **Dates:** 
   - If "All Time", set scope ALL_TIME.
   - Else, set RANGE and apply +20 Year Shift.
   
2. **Metric Formula:** 
   - Extract ONLY the math (e.g., `SUM(UnitPrice * Quantity)`). 
   - **CRITICAL:** Do NOT write "SELECT", "WHERE", "BETWEEN" in this field. Math only.
   - Apply substitutions (e.g. Cost = 0.7 * Price).

3. **Ranking & Grouping (CRITICAL):**
   - **Identify the Entity:** Check if the user asks for a Customer, Product, or Category.
   - **Do NOT Default to Customer:** If asked for "Top Category", set intent to "Top 1 Category".
   - **Aggregates (Force NONE):** If the question asks for "Total Revenue", "AOV", or "How much..." (even if filtered by a specific Category like Beverages), YOU MUST set RANKING_INTENT: "None".

### FORMAT (Strict ONLY YAML) (DO NOT RETURN ANYTHING ELSE)
TIME_SCOPE: <'RANGE' or 'ALL_TIME'>
START_DATE: <YYYY-MM-DD or None>
END_DATE: <YYYY-MM-DD or None>
RANKING_INTENT: <e.g. "Top 1 Category", "Top 3 Products", "Top 1 Customer", or "None">
METRIC_FORMULA: <Math Only>
"""
    
    user_message = f"""
USER QUESTION: {question}

{docs_text}

OUTPUT:
"""
    
    messages = [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_message}]
    
    raw_plan = query_ollama(messages, model=MODEL, temperature=0.0)
    corrected_plan = _apply_time_shift(raw_plan)
    
    print(f"DEBUG [Planner]:\n{corrected_plan}")
    
    return {"sql_plan": corrected_plan}


def clean_sql(text: str) -> str:
    """Removes markdown fencing and whitespace."""
    pattern = r"```sql\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.replace("```", "").strip()



def nl2sql_node(state: AgentState):
    """
    NL2SQL Node - Now using DSPy Optimized Module
    """
    print("--- Node: NL2SQL (DSPy Optimized) ---")
    
    question = state["question"]
    plan = state["sql_plan"]
    
    prev_error = None
    prev_sql = None
    if state.get("sql_result") and not state.get("sql_valid"):
        print(f"   [Repairing] Attempt {state['attempt_count'] + 1}")
        prev_error = state["sql_result"]
        prev_sql = state["sql_query"]
    
    # Build plan_constraints string (same format as training data)
    # Add error context if this is a repair attempt
    plan_with_context = plan
    if prev_error and prev_sql:
        plan_with_context = f"""{plan}

### FIX ERROR
SQL: {prev_sql}
ERROR: {prev_error}

HINT: Check Joins and Column Names."""
    
    try:
        # Use DSPy module
        result = compiled_sql_module(
            question=question,
            schema_context=schema_info,
            plan_constraints=plan_with_context
        )
        
        raw_response = result.sql_query
        
    except Exception as e:
        print(f"   [DSPy Error]: {e}")
        print("   [Fallback]: Using raw SQL generation")
        # Fallback to raw generation if DSPy fails
        raw_response = generate_sql_fallback(plan_with_context)
    
    sql_query = clean_sql(raw_response)
    print(f"DEBUG [NL2SQL]: \n{sql_query}")
    
    return {"sql_query": sql_query}


def generate_sql_fallback(plan: str) -> str:
    """
    Fallback SQL generation if DSPy fails.
    Uses exact same prompt as DSPy signature.
    """
    system_instruction = """You are a SQLite Expert.

### SCHEMA
- `orders` (o): OrderID, CustomerID, OrderDate (YYYY-MM-DD)
- `order_items` (oi): OrderID, ProductID, UnitPrice, Quantity, Discount
- `products` (p): ProductID, ProductName, CategoryID (**NO CategoryName**)
- `categories` (c): CategoryID, CategoryName (**CategoryName is HERE**)
- `customers` (cust): CustomerID, CompanyName

### RULES
1. **Join Orders:** ALWAYS `JOIN orders o ON oi.OrderID = o.OrderID` to filter by Date.
2. **Join Categories:** To filter by "CategoryName", you MUST `JOIN categories c ON p.CategoryID = c.CategoryID`.
3. **Dates:** Use `>=` and `<=`. **NEVER** use `BETWEEN`.
4. **Grouping:**
   - If Plan says "Top X": `GROUP BY` the entity.
   - If Plan says "None": **DO NOT GROUP BY**. `SELECT SUM(...)`.

### FORMAT
Return raw SQL only.
"""

    user_message = f"""
### PLAN
{plan}
"""

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_message}
    ]
    
    return query_ollama(messages, model=MODEL, temperature=0.0)




def executor_node(state: AgentState):
    print("--- Node: Executor ---")
    query = state["sql_query"]
    tool = SQLiteTool()
    
    result = tool.query(query)
    
    is_error = result.lower().startswith("sql error") or result.lower().startswith("error")
    
    if is_error:
        print(f"   [Error]: {result}")
        return {
            "sql_result": result,
            "sql_valid": False,
            "attempt_count": state["attempt_count"] + 1
        }
    else:
        print("   [Success]: Query executed.")
        return {
            "sql_result": result,
            "sql_valid": True,
        }
    
def synthesize_answer_standard(question: str, sql_result: str, docs: List[Dict], format_hint: str) -> str:
    docs_text = "\n".join([f"- {d['text']}" for d in docs])
    
    system_instruction = f"""You are a JSON Bot.

### INPUT
- Question: {question}
- SQL Result: {sql_result}
- Docs: {docs_text}
- Hint: {format_hint}

### RULES
1. **SQL Answer:** If SQL Result has data, extract the answer from it.
2. **RAG Answer:** If SQL Result is empty/error, use **Docs** to answer.
3. **Format:** Strict JSON. Keys: "final_answer", "explanation", "citations".

### EXAMPLE (RAG)
Input: SQL: "No SQL", Docs: "Return window is 14 days."
Output: {{"final_answer": 14, "explanation": "Policy says 14 days.", "citations": ["Policy"]}}
"""
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": "JSON:"}
    ]
    
    return query_ollama(messages, model=MODEL, temperature=0.0)


def synthesizer_node(state: AgentState):
    print("--- Node: Synthesizer ---")
    
    question = state["question"]
    sql_result = state.get("sql_result", "No SQL executed")
    docs = state.get("retrieved_docs", [])
    format_hint = state["format_hint"]
    
    raw_response = synthesize_answer_standard(question, sql_result, docs, format_hint)
    
    try:
        clean_json = raw_response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        start = clean_json.find("{")
        end = clean_json.rfind("}")
        
        if start != -1 and end != -1:
            clean_json = clean_json[start:end+1]
        
        parsed = json.loads(clean_json)
        
        return {
            "final_answer": parsed.get("final_answer"),
            "explanation": parsed.get("explanation"),
            "citations": parsed.get("citations", [])
        }
    except json.JSONDecodeError as e:
        print(f"   [Synthesizer JSON Error]: {e}")
        print(f"   [Raw Output]: {raw_response}")
        return {
            "final_answer": None, 
            "explanation": f"JSON Parsing Failed. Raw result: {sql_result}",
            "citations": []
        }
    except Exception as e:
        print(f"   [Synthesizer Generic Error]: {e}")
        return {
            "final_answer": None, 
            "explanation": "Unknown error in synthesis.",
            "citations": []
        }
    
try:
    RETRIEVER = Retriever(docs_path="docs")
except Exception as e:
    print(f"Warning: Retriever failed to load (check docs/ folder): {e}")
    RETRIEVER = None


def retriever_node(state: AgentState):
    print("--- Node: Retriever ---")
    question = state["question"]
    if RETRIEVER:
        results = RETRIEVER.search(question, top_k=3)
    else:
        results = []
    return {"retrieved_docs": results}


workflow = StateGraph(AgentState)

# 1. Add Nodes
workflow.add_node("router", router_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("planner", planner_node)
workflow.add_node("nl2sql", nl2sql_node)
workflow.add_node("executor", executor_node)
workflow.add_node("synthesizer", synthesizer_node)

# 2. Set Entry Point
workflow.set_entry_point("router")

# 3. Router Logic
# Always get context first (both paths need it)
workflow.add_edge("router", "retriever")

# 4. Conditional Edge: Retriever -> (Planner OR Synthesizer)
def decide_post_retrieval(state):
    # If hybrid, we need to Plan and Generate SQL
    if state["classification"] == "hybrid":
        return "planner"
    # If RAG-only, skip straight to answering
    else:
        return "synthesizer"

workflow.add_conditional_edges(
    "retriever",
    decide_post_retrieval,
    {
        "planner": "planner",
        "synthesizer": "synthesizer"
    }
)

# 5. SQL Pipeline (Linear)
workflow.add_edge("planner", "nl2sql")
workflow.add_edge("nl2sql", "executor")

# 6. Repair Loop Logic
def check_execution_status(state):
    if state["sql_valid"]:
        # Success -> Go to Answer
        return "synthesizer"
    elif state["attempt_count"] < 2: # Limit: 2 retries (Total 3 attempts)
        # Failure -> Retry SQL Generation
        return "nl2sql"
    else:
        # Failure + Max Retries -> Give up and Synthesize Error
        return "synthesizer"

workflow.add_conditional_edges(
    "executor",
    check_execution_status,
    {
        "synthesizer": "synthesizer",
        "nl2sql": "nl2sql"
    }
)

# 7. Final Edge
workflow.add_edge("synthesizer", END)

# 8. Compile
app = workflow.compile()