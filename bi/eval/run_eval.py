import yaml
import pandas as pd
from pathlib import Path
from bi.db import run_query
from bi.sql_guard import validate_and_guard_sql
from bi.llm import generate_sql

def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
    if df1.empty and df2.empty:
        return True
    if df1.shape != df2.shape:
        return False

    # Normalize values for order-insensitive and round comparison
    s1 = set(tuple(str(x).strip() for x in row) for row in df1.to_numpy())
    s2 = set(tuple(str(x).strip() for x in row) for row in df2.to_numpy())
    return s1 == s2

def run_evaluation(questions_path: str = "bi/eval/questions.yaml"):
    with open(questions_path, "r", encoding="utf-8") as f:
        test_cases = yaml.safe_load(f)

    schema_ctx = Path("bi/context/schema_context.md").read_text(encoding="utf-8") if Path("bi/context/schema_context.md").exists() else ""

    passed = 0
    total = len(test_cases)
    print(f"\n--- Running LLM SQL Evaluation ({total} questions) ---")

    for tc in test_cases:
        q_id = tc["id"]
        question = tc["question"]
        gold_sql = tc["gold_sql"]

        print(f"\n[{q_id}/{total}] Q: {question}")
        try:
            gold_df = run_query(gold_sql)
        except Exception as e:
            print(f"  FAILED: Error running gold SQL: {e}")
            continue

        llm_out = generate_sql(question, schema_ctx)
        gen_sql = llm_out.get("sql", "").strip()

        is_safe, guarded_sql, guard_err = validate_and_guard_sql(gen_sql)
        if not is_safe:
            print(f"  FAILED: SQL Guard rejected: {guard_err}")
            continue

        try:
            gen_df = run_query(guarded_sql)
        except Exception as e:
            print(f"  FAILED: Error running generated SQL: {e}")
            continue

        if compare_dataframes(gold_df, gen_df):
            print("  PASSED")
            passed += 1
        else:
            print("  FAILED: Result sets do not match.")
            print(f"    Gold ({len(gold_df)} rows):\n{gold_df.head(3)}")
            print(f"    Generated ({len(gen_df)} rows):\n{gen_df.head(3)}")

    print(f"\n==========================================")
    print(f"Evaluation Summary: {passed}/{total} Passed ({(passed/total)*100:.1f}%)")
    print(f"==========================================\n")

if __name__ == "__main__":
    run_evaluation()
