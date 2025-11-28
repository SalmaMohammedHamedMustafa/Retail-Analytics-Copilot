import dspy
import os
import sys
from dspy.evaluate import Evaluate
from dspy.teleprompt import BootstrapFewShot
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.tools.sqlite_tool import SQLiteTool
from agent.dspy_signatures import GenerateSQL
from dspy_dataset import train_data

# --- 1. CONFIGURATION ---
lm = dspy.LM(
    model="ollama/phi3.5:3.8b-mini-instruct-q4_K_M", 
    api_base="http://localhost:11434", 
    api_key="",
    temperature=0.0,
    num_ctx=4096  # Increased context for more examples
)
dspy.configure(lm=lm)

db_tool = SQLiteTool()
schema_info = db_tool.get_schema()

# Inject schema into all examples
for ex in train_data:
    ex.schema_context = schema_info

def sqlite_metric(gold, pred, trace=None):
    """
    Validates SQL executes without error.
    """
    predicted_sql = pred.sql_query
    clean_sql = predicted_sql.replace("```sql", "").replace("```", "").strip()
    
    # Basic sanity checks
    if not clean_sql or len(clean_sql) < 15:
        return False
    
    try:
        result = db_tool.query(clean_sql)
        if result.lower().startswith("error") or result.lower().startswith("sql error"):
            return False
        return True 
    except Exception:
        return False

def strategic_split(data):
    """
    Split data to ensure diverse coverage in both sets.
    Uses stratification to balance query types.
    30 train / 10 val split.
    """
    import random
    
    # Categorize examples
    global_totals = []
    rankings = []
    formulas = []
    beverages = []
    
    for i, ex in enumerate(data):
        q = ex.question.lower()
        if 'beverage' in q:
            beverages.append((i, ex))
        elif 'top' in q or 'best' in q or 'highest' in q:
            rankings.append((i, ex))
        elif 'aov' in q or 'margin' in q:
            formulas.append((i, ex))
        else:
            global_totals.append((i, ex))
    
    # Helper to split list
    def split_list(lst, val_count):
        random.shuffle(lst)
        return [x[1] for x in lst[val_count:]], [x[1] for x in lst[:val_count]]

    # Allocate validation set (aiming for 10 total)
    # 2 Beverages, 3 Rankings, 2 Formulas, 3 Globals
    t1, v1 = split_list(beverages, 2)
    t2, v2 = split_list(rankings, 3)
    t3, v3 = split_list(formulas, 2)
    t4, v4 = split_list(global_totals, 3)
    
    train_set = t1 + t2 + t3 + t4
    val_set = v1 + v2 + v3 + v4
    
    return train_set, val_set

def run_optimization():
    print("=== 1. Initializing DSPy Module ===")
    sql_module = dspy.Predict(GenerateSQL)
    
    # Strategic split
    train_set, val_set = strategic_split(train_data)
    print(f"Train set: {len(train_set)} examples")
    print(f"Val set: {len(val_set)} examples")

    print("\n=== 2. Evaluating Baseline (Before Optimization) ===")
    evaluator = Evaluate(
        devset=val_set, 
        metric=sqlite_metric, 
        num_threads=1, 
        display_progress=True, 
        display_table=0
    )
    
    # Run baseline
    score_before = evaluator(sql_module)
    print(f"\nBASELINE SCORE: {score_before}%")

    print("\n=== 3. Running BootstrapFewShot (Optimization) ===")
    print("Strategy: 3 Demonstrations max to prevent context overflow.")
    
    teleprompter = BootstrapFewShot(
        metric=sqlite_metric,
        max_bootstrapped_demos=3,    # Limit to 3 perfect examples
        max_labeled_demos=0,         # Don't force manual demos, let it pick the best
        max_rounds=1                 # Single pass is enough for small datasets
    )
    
    print("Training")
    compiled_sql_module = teleprompter.compile(sql_module, trainset=train_set)

    print("\n=== 4. Evaluating Optimized Module (After Optimization) ===")
    score_after = evaluator(compiled_sql_module)
    print(f"\nOPTIMIZED SCORE: {score_after}%")
    
    print(f"\n=== RESULTS ===")
    print(f"Baseline:   {score_before}%")
    print(f"Optimized:  {score_after}%")

    # Save the optimized module
    save_path = "agent/sql_optimized.json"
    compiled_sql_module.save(save_path)
    print(f"\nOptimized module saved to: {save_path}")
    
    return compiled_sql_module

if __name__ == "__main__":
    run_optimization()