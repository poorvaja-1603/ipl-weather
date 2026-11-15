import json
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def generate_schema_context(
    manifest_path: str | Path = REPO_ROOT / "dbt/ipl_dbt/target/manifest.json",
    catalog_path: str | Path = REPO_ROOT / "dbt/ipl_dbt/target/catalog.json",
    output_path: str | Path = REPO_ROOT / "bi/context/schema_context.md",
) -> Path:
    manifest_file = Path(manifest_path)
    catalog_file = Path(catalog_path)
    output_file = Path(output_path)
    if not manifest_file.is_file():
        raise FileNotFoundError(f"dbt manifest not found: {manifest_file}")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    catalog = {}
    if catalog_file.is_file():
        catalog = json.loads(catalog_file.read_text(encoding="utf-8")).get("nodes", {})

    default_project = os.getenv("GCP_PROJECT_ID", "")
    lines = ["# IPL Marts Schema Context", ""]
    mart_nodes = [
        (node_id, node)
        for node_id, node in manifest.get("nodes", {}).items()
        if node.get("resource_type") == "model" and node.get("schema", "").lower() == "marts"
    ]
    mart_nodes.sort(key=lambda item: item[1].get("name", ""))

    if not mart_nodes:
        raise ValueError("No dbt models in the marts dataset were found in the manifest")

    for node_id, node in mart_nodes:
        project = node.get("database") or default_project
        alias = node.get("alias") or node.get("name")
        if not project or not alias:
            raise ValueError(f"Model {node_id} is missing a project or table name")

        relation = f"`{project}.marts.{alias}`"
        description = (node.get("description") or "No model description available.").replace("\n", " ")
        lines.extend([f"## Table: {relation}", "", description, "", "| Column | Type | Description |", "|---|---|---|"])

        catalog_columns = catalog.get(node_id, {}).get("columns", {})
        columns = node.get("columns", {})
        for column_name in sorted(columns):
            column = columns[column_name]
            catalog_column = catalog_columns.get(column_name, catalog_columns.get(column_name.lower(), {}))
            data_type = catalog_column.get("type", "UNKNOWN")
            column_description = (column.get("description") or "").replace("\n", " ").replace("|", "\\|")
            lines.append(f"| `{column_name}` | `{data_type}` | {column_description} |")
        lines.append("")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated schema context for {len(mart_nodes)} marts at {output_file}")
    return output_file


if __name__ == "__main__":
    generate_schema_context()
