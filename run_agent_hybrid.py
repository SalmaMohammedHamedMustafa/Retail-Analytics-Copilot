import argparse
import json
import sys
import os
import time  # Import time for tracking

# Ensure the agent module can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.graph_hybrid import app

def process_batch(input_file, output_file):
    print(f"=== Starting Batch Processing ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    # Track Total Time
    batch_start_time = time.time()
    
    # Read all lines first
    with open(input_file, "r") as f:
        lines = f.readlines()

    processed_count = 0
    
    # Open output file for writing results line-by-line
    with open(output_file, "w") as f_out:
        for line in lines:
            if not line.strip():
                continue
            
            data = json.loads(line)
            q_id = data["id"]
            question = data["question"]
            format_hint = data["format_hint"]
            
            print(f"\n[{processed_count+1}/{len(lines)}] ID: {q_id}")
            print(f"Question: {question[:60]}...")
            
            # 1. Initialize Input State
            inputs = {
                "question": question,
                "format_hint": format_hint,
                # Default values for safety
                "attempt_count": 0,
                "sql_valid": False,
                "retrieved_docs": [],
                "classification": "hybrid" 
            }
            
            # Track Individual Question Time
            q_start_time = time.time()
            
            try:
                # 2. Invoke the Graph
                # stream=False waits for the entire graph to finish
                final_state = app.invoke(inputs)
                
                # 3. Extract Results from State
                final_answer = final_state.get("final_answer")
                explanation = final_state.get("explanation") or "No explanation provided."
                citations = final_state.get("citations") or []
                
                # Determine SQL field (Only populate if it was a Hybrid/SQL path)
                sql_used = ""
                if final_state.get("classification") == "hybrid":
                    sql_used = final_state.get("sql_query", "")
                
                # Heuristic Confidence Calculation
                confidence = 0.0
                if final_state.get("sql_valid"):
                    confidence = 1.0
                elif final_state.get("classification") == "rag":
                    confidence = 0.8
                
                if final_answer is None:
                    confidence = 0.0
                
                # 4. Construct Output Object (Strict Contract)
                output_obj = {
                    "id": q_id,
                    "final_answer": final_answer,
                    "sql": sql_used,
                    "confidence": confidence,
                    "explanation": explanation,
                    "citations": list(set(citations)) # Deduplicate citations
                }
                
                # Calculate Duration
                q_end_time = time.time()
                duration = q_end_time - q_start_time
                
                # Log success and time
                print(f"   -> Answer: {str(final_answer)[:50]}")
                print(f"   -> SQL Valid: {final_state.get('sql_valid')}")
                print(f"   -> Time: {duration:.2f}s")
                
                # 5. Write to file
                f_out.write(json.dumps(output_obj) + "\n")
                f_out.flush() # Ensure it writes immediately
                
            except Exception as e:
                q_end_time = time.time()
                duration = q_end_time - q_start_time
                print(f"   [CRITICAL FAILURE]: {e}")
                print(f"   -> Time (Failed): {duration:.2f}s")
                
                # Fallback error object
                err_obj = {
                    "id": q_id,
                    "final_answer": None,
                    "sql": "",
                    "confidence": 0.0,
                    "explanation": f"System Error: {str(e)}",
                    "citations": []
                }
                f_out.write(json.dumps(err_obj) + "\n")
            
            processed_count += 1

    batch_end_time = time.time()
    total_duration = batch_end_time - batch_start_time
    avg_duration = total_duration / processed_count if processed_count > 0 else 0

    print(f"\n=== Batch Processing Complete ===")
    print(f"Results saved to: {output_file}")
    print(f"Total Time: {total_duration:.2f}s")
    print(f"Average Time per Question: {avg_duration:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Retail Analytics Copilot")
    parser.add_argument("--batch", required=True, help="Path to input JSONL file")
    parser.add_argument("--out", required=True, help="Path to output JSONL file")
    
    args = parser.parse_args()
    
    # Check if input exists
    if not os.path.exists(args.batch):
        print(f"Error: Input file '{args.batch}' not found.")
        sys.exit(1)
        
    process_batch(args.batch, args.out)