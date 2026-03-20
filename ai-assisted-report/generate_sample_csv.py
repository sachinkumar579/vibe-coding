"""
generate_sample_csv.py
----------------------
Uses Azure OpenAI to generate realistic tabular data on any topic,
then saves it as a CSV file ready for the report agent.

Usage:
    python generate_sample_csv.py
    python generate_sample_csv.py --topic "hospital patient records" --rows 50
    python generate_sample_csv.py --topic "ecommerce orders" --rows 100 --output my_data.csv
"""

import argparse
import csv
import io
import json
import os
import sys

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────

AZURE_ENDPOINT    = "https://sachinramuk72-0063-resource.cognitiveservices.azure.com/"
AZURE_DEPLOYMENT  = "gpt-4o-mini"
AZURE_API_VERSION = "2024-12-01-preview"

# How many rows to request per LLM call (keep under ~40 for reliable JSON)
BATCH_SIZE = 25

# ─── Azure OpenAI client ──────────────────────────────────────────────────────

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=os.environ.get("AZURE_OPENAI_KEY"),
    api_version=AZURE_API_VERSION,
)

# ─── Step 1: Ask LLM to design the schema ─────────────────────────────────────


def design_schema(topic: str) -> dict:
    """
    Ask GPT to decide the best column structure for the given topic.
    Returns a schema dict with column names and descriptions.
    """
    print(f"🧠 Designing schema for: '{topic}'...")

    prompt = f"""
You are a data engineer. Design a realistic CSV dataset schema for the topic: "{topic}"

Respond with a JSON object with this exact structure:
{{
  "dataset_title": "<short descriptive title>",
  "description": "<one sentence describing what this dataset represents>",
  "columns": [
    {{
      "name": "<column_name_snake_case>",
      "type": "string" | "integer" | "float" | "date",
      "description": "<what this column represents>",
      "example": "<a realistic example value>"
    }}
  ]
}}

Rules:
- Use 6 to 10 columns
- Include a mix of numeric and categorical columns
- Include at least one date column
- Include at least 2 numeric columns suitable for aggregation
- Column names must be snake_case
- Make values realistic and domain-specific for the topic
"""

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    schema = json.loads(response.choices[0].message.content)
    print(f"   ✅ Schema: {len(schema['columns'])} columns — {schema['dataset_title']}")
    for col in schema["columns"]:
        print(f"      • {col['name']} ({col['type']}) — {col['description']}")
    print()
    return schema


# ─── Step 2: Ask LLM to generate rows in batches ─────────────────────────────


def generate_batch(schema: dict, batch_num: int, batch_size: int) -> list[dict]:
    """
    Ask GPT to generate one batch of rows matching the schema.
    Returns a list of row dicts.
    """
    col_summary = "\n".join(
        f"  - {c['name']} ({c['type']}): {c['description']}. Example: {c['example']}"
        for c in schema["columns"]
    )
    col_names = [c["name"] for c in schema["columns"]]

    prompt = f"""
Generate exactly {batch_size} rows of realistic, varied data for this dataset:

Dataset: {schema['dataset_title']}
{schema['description']}

Columns:
{col_summary}

Rules:
- Data must be realistic and varied — no copy-paste repetition
- Dates should be spread across a 12-month period in 2024
- Numeric values should have natural variance (not all round numbers)
- String values should be domain-appropriate and diverse
- This is batch {batch_num} — use different values from previous batches

Respond with a JSON object:
{{
  "rows": [
    {{ "<col_name>": <value>, ... }},
    ...
  ]
}}
"""

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,   # higher temp = more variety across batches
        response_format={"type": "json_object"},
    )

    usage = response.usage
    data  = json.loads(response.choices[0].message.content)
    rows  = data.get("rows", [])

    print(f"   Batch {batch_num}: {len(rows)} rows  "
          f"(tokens: {usage.total_tokens})")
    return rows


# ─── Step 3: Write to CSV ─────────────────────────────────────────────────────


def save_csv(schema: dict, all_rows: list[dict], filename: str):
    """Write all rows to a CSV file using the schema column order."""
    col_names = [c["name"] for c in schema["columns"]]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=col_names, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    print(f"\n✅ Saved {len(all_rows)} rows → {filename}")
    print(f"   Columns: {', '.join(col_names)}")


# ─── Main ─────────────────────────────────────────────────────────────────────


def run(topic: str, total_rows: int, output_file: str):
    print(f"\n📊 CSV Data Generator (Azure OpenAI)")
    print(f"   Topic  : {topic}")
    print(f"   Rows   : {total_rows}")
    print(f"   Output : {output_file}\n")

    # DESIGN schema
    schema = design_schema(topic)

    # GENERATE rows in batches
    print(f"🔄 Generating {total_rows} rows in batches of {BATCH_SIZE}...")
    all_rows  = []
    batch_num = 1
    remaining = total_rows

    while remaining > 0:
        batch_size = min(BATCH_SIZE, remaining)
        rows = generate_batch(schema, batch_num, batch_size)
        all_rows.extend(rows)
        remaining -= len(rows)
        batch_num += 1

    # SAVE
    save_csv(schema, all_rows[:total_rows], output_file)
    print(f"\n   Ready to run: python generate_report.py --csv {output_file} --output ./reports\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a realistic CSV dataset using Azure OpenAI"
    )
    parser.add_argument(
        "--topic",
        default="retail sales transactions",
        help='Topic for the dataset e.g. "hospital patient records", "ecommerce orders"',
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=50,
        help="Number of rows to generate (default: 50)",
    )
    parser.add_argument(
        "--output",
        default="sample_data.csv",
        help="Output CSV filename (default: sample_data.csv)",
    )
    args = parser.parse_args()
    run(args.topic, args.rows, args.output)