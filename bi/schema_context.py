import json
import os
from pathlib import Path

def generate_schema_context(
    manifest_path: str = "dbt/ipl_dbt/target/manifest.json",
    catalog_path: str = "dbt/ipl_dbt/target/catalog.json",
    output_path: str = "bi/context/schema_context.md"
):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(manifest_path):
        print(f"Warning: manifest file not found at {manifest_path}. Generating default context.")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    catalog = {}
    if os.path.exists(catalog_path):
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f).get("nodes", {})

    lines = ["# IPL Marts Schema Context\n"]
    for node_id, node in manifest.get("nodes", {}).items():
        if not node_id.startswith("model.ipl_dbt.mart_") and not node_id.startswith("model.ipl_dbt.fct_") and not node_id.startswith("model.ipl_dbt.dim_"):
            continue

        table_name = f"IPL_DB.MARTS.{node.get('name').upper()}"
        description = node.get("description", "No description available.")
        lines.append(f"## Table: `{table_name}`\n")
        lines.append(f"**Description**: {description}\n")
        lines.append("| Column | Type | Description |")
        lines.append("|---|---|---|")

        catalog_cols = catalog.get(node_id, {}).get("columns", {})
        for col_name, col_meta in node.get("columns", {}).items():
            c_type = catalog_cols.get(col_name, {}).get("type", "UNKNOWN")
            c_desc = col_meta.get("description", "").replace("\n", " ")
            lines.append(f"| `{col_name}` | `{c_type}` | {c_desc} |")
        lines.append("\n---\n")

    output_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated schema context at {output_path}")

if __name__ == "__main__":
    generate_schema_context()
