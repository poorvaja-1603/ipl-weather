import argparse
import math
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import yaml

from bi.config import GCP_PROJECT_ID
from bi.db import run_query
from bi.llm import generate_sql
from bi.sql_guard import validate_and_guard_sql


ROOT = Path(__file__).resolve().parents[2]


def normalize_value(value: object) -> object:
    if pd.isna(value):
        return None
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isfinite(number):
            return round(number, 6)
        return str(number)
    return str(value).strip()


def compare_dataframes(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    if left.shape != right.shape:
        return False
    left_rows = Counter(tuple(normalize_value(value) for value in row) for row in left.to_numpy())
    right_rows = Counter(tuple(normalize_value(value) for value in row) for row in right.to_numpy())
    return left_rows == right_rows


def run_evaluation(questions_path: str | Path = ROOT / "bi/eval/questions.yaml") -> tuple[int, int]:
    if not GCP_PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID is not set.")

    test_cases = yaml.safe_load(Path(questions_path).read_text(encoding="utf-8")) or []
    context_path = ROOT / "bi/context/schema_context.md"
    schema_context = context_path.read_text(encoding="utf-8") if context_path.is_file() else ""

    passed = 0
    total = len(test_cases)
    print(f"\n--- Running LLM SQL evaluation ({total} questions) ---")
    for index, test_case in enumerate(test_cases, start=1):
        question = test_case["question"]
        gold_sql = test_case["gold_sql"].replace("{{ project }}", GCP_PROJECT_ID)
        print(f"\n[{index}/{total}] {question}")

        valid_gold, safe_gold, error = validate_and_guard_sql(gold_sql)
        if not valid_gold:
            print(f"  FAILED: gold SQL rejected: {error}")
            continue
        try:
            gold_result = run_query(safe_gold)
        except Exception as error:
            print(f"  FAILED: gold query error: {error}")
            continue

        try:
            generated = generate_sql(question, schema_context)
        except Exception as error:
            print(f"  FAILED: Gemini error: {error}")
            continue

        generated_sql = generated.get("sql", "").strip()
        valid_generated, safe_generated, guard_error = validate_and_guard_sql(generated_sql)
        if not valid_generated:
            print(f"  FAILED: generated SQL rejected: {guard_error}")
            continue
        try:
            generated_result = run_query(safe_generated)
        except Exception as error:
            print(f"  FAILED: generated query error: {error}")
            continue

        if compare_dataframes(gold_result, generated_result):
            passed += 1
            print("  PASSED")
        else:
            print("  FAILED: result values differ")
            print(f"    Gold results:\n{gold_result.head(3)}")
            print(f"    Generated results:\n{generated_result.head(3)}")

    rate = 100 * passed / total if total else 0
    print(f"\nEvaluation: {passed}/{total} passed ({rate:.1f}%)")
    return passed, total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare Gemini SQL results to the evaluation set.")
    parser.add_argument("--questions", default=str(ROOT / "bi/eval/questions.yaml"))
    args = parser.parse_args()
    passed_count, total_count = run_evaluation(args.questions)
    raise SystemExit(0 if total_count and passed_count >= 12 else 1)
