"""
generate_report.py.py — CSV Analytics Report Agent
--------------------------------------------------
Reads any CSV file, uses Azure OpenAI to decide what metrics
and charts are most useful, generates charts with matplotlib,
and assembles a polished PDF report with reportlab.

Requirements:
    pip install -r requirements.txt

Usage:
    python generate_report.py --csv data.csv --output ./reports
    python generate_report.py --csv sales.csv --output ./reports
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────

AZURE_ENDPOINT    = "https://sachinramuk72-0063-resource.cognitiveservices.azure.com/"
AZURE_DEPLOYMENT  = "gpt-4o-mini"
AZURE_API_VERSION = "2024-12-01-preview"

# Colour palette for charts
CHART_COLORS = ["#4F81BD", "#C0504D", "#9BBB59", "#8064A2", "#4BACC6",
                "#F79646", "#2C4770", "#7F3F3F", "#3B6E3B", "#5C4A7F"]

# ─── Azure OpenAI client ──────────────────────────────────────────────────────

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=os.environ.get("AZURE_OPENAI_KEY"),
    api_version=AZURE_API_VERSION,
)

# ─── Step 1: PERCEIVE — Read and profile the CSV ─────────────────────────────


def read_csv(filepath: str) -> pd.DataFrame:
    """Load CSV into a DataFrame, coercing numeric columns."""
    df = pd.read_csv(filepath)
    # Try to parse any column that looks numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")
    return df


def profile_dataframe(df: pd.DataFrame) -> dict:
    """
    Build a lightweight profile of the DataFrame to send to the LLM.
    Avoids sending raw data — just shape, dtypes, and sample stats.
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    stats = {}
    for col in numeric_cols:
        stats[col] = {
            "min":    round(df[col].min(), 2),
            "max":    round(df[col].max(), 2),
            "mean":   round(df[col].mean(), 2),
            "median": round(df[col].median(), 2),
            "nulls":  int(df[col].isnull().sum()),
        }

    return {
        "row_count":        len(df),
        "column_count":     len(df.columns),
        "columns":          df.columns.tolist(),
        "numeric_columns":  numeric_cols,
        "categorical_columns": categorical_cols,
        "sample_rows":      df.head(3).to_dict(orient="records"),
        "numeric_stats":    stats,
    }


# ─── Step 2: DECIDE — Ask LLM what to analyse and chart ──────────────────────


class _NumpySafeEncoder(json.JSONEncoder):
    """Converts numpy int64/float64 to plain Python types before serialising."""
    def default(self, o):
        import numpy as np
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)


def decide_analysis(profile: dict) -> dict:
    """
    Send the CSV profile to Azure OpenAI.
    Ask it to decide:
      - A title and executive summary for the report
      - Key metrics to highlight
      - Which charts to generate and what columns to use
    Returns a structured JSON plan.
    """
    prompt = f"""
You are a senior data analyst. You have been given a profile of a CSV dataset.
Your job is to design a concise, insightful analytics report.

Dataset profile:
{json.dumps(profile, indent=2, cls=_NumpySafeEncoder)}

Based on the column names, data types, and statistics, respond with a JSON object
that follows this EXACT structure (no extra keys):

{{
  "report_title": "<descriptive title based on the data>",
  "executive_summary": "<2-3 sentences summarising what this dataset represents and key findings>",
  "key_metrics": [
    {{
      "label": "<metric name>",
      "value": "<computed value as a string>",
      "insight": "<one sentence explaining why this matters>"
    }}
  ],
  "charts": [
    {{
      "chart_type": "bar" | "line" | "pie" | "histogram",
      "title": "<chart title>",
      "x_column": "<column name or null>",
      "y_column": "<column name>",
      "description": "<one sentence describing what this chart shows>"
    }}
  ],
  "conclusion": "<2-3 sentences with actionable recommendations or observations>"
}}

Rules:
- key_metrics: pick 4-6 most meaningful metrics (totals, averages, extremes)
- charts: suggest 3-5 charts. Only use column names that exist in the dataset.
- For pie charts: x_column = category column, y_column = numeric column
- For histogram: x_column = null, y_column = the numeric column to distribute
- For bar/line: x_column = category or date column, y_column = numeric column
- Be specific and insightful — not generic
"""

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    usage = response.usage
    print(f"   🪙 Tokens — prompt: {usage.prompt_tokens}  "
          f"completion: {usage.completion_tokens}  "
          f"total: {usage.total_tokens}")

    return json.loads(response.choices[0].message.content)


# ─── Step 3: GENERATE — Render charts with matplotlib ────────────────────────


def render_chart(chart_spec: dict, df: pd.DataFrame, tmp_dir: str) -> str | None:
    """
    Render a single chart based on the LLM spec.
    Saves to a temp PNG and returns the file path.
    Returns None if the chart can't be rendered.
    """
    chart_type = chart_spec.get("chart_type", "bar")
    title      = chart_spec.get("title", "Chart")
    x_col      = chart_spec.get("x_column")
    y_col      = chart_spec.get("y_column")

    # Validate columns exist
    if y_col not in df.columns:
        print(f"   ⚠️  Skipping chart '{title}': column '{y_col}' not found")
        return None
    if x_col and x_col not in df.columns:
        print(f"   ⚠️  Skipping chart '{title}': column '{x_col}' not found")
        return None

    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    try:
        if chart_type == "bar":
            data = df.groupby(x_col)[y_col].sum().nlargest(12)
            bars = ax.bar(data.index.astype(str), data.values,
                          color=CHART_COLORS[:len(data)], edgecolor="white", linewidth=0.5)
            ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8)
            plt.xticks(rotation=30, ha="right", fontsize=8)

        elif chart_type == "line":
            data = df.groupby(x_col)[y_col].sum()
            ax.plot(data.index.astype(str), data.values,
                    color=CHART_COLORS[0], linewidth=2, marker="o", markersize=4)
            ax.fill_between(range(len(data)), data.values, alpha=0.1, color=CHART_COLORS[0])
            plt.xticks(rotation=30, ha="right", fontsize=8)

        elif chart_type == "pie":
            data = df.groupby(x_col)[y_col].sum().nlargest(8)
            wedges, texts, autotexts = ax.pie(
                data.values,
                labels=data.index.astype(str),
                autopct="%1.1f%%",
                colors=CHART_COLORS[:len(data)],
                startangle=90,
                pctdistance=0.82,
            )
            for t in autotexts:
                t.set_fontsize(8)
            ax.axis("equal")

        elif chart_type == "histogram":
            col_data = df[y_col].dropna()
            ax.hist(col_data, bins=20, color=CHART_COLORS[0],
                    edgecolor="white", linewidth=0.5)
            ax.set_xlabel(y_col, fontsize=9)
            ax.set_ylabel("Frequency", fontsize=9)

        else:
            plt.close(fig)
            return None

        # Styling
        ax.set_title(title, fontsize=12, fontweight="bold", pad=12, color="#2C2C2C")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CCCCCC")
        ax.spines["bottom"].set_color("#CCCCCC")
        ax.tick_params(colors="#555555", labelsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"{x:,.0f}"
        ))
        plt.tight_layout()

        # Save to temp file
        out_path = os.path.join(tmp_dir, f"chart_{abs(hash(title))}.png")
        plt.savefig(out_path, dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        return out_path

    except Exception as e:
        print(f"   ⚠️  Chart '{title}' failed: {e}")
        plt.close(fig)
        return None


# ─── Step 4: ACT — Assemble the PDF ──────────────────────────────────────────


def build_pdf(
    plan: dict,
    chart_paths: list[dict],
    profile: dict,
    csv_filename: str,
    output_path: str,
):
    """Assemble the full PDF report using reportlab Platypus."""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ──
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#2C4770"),
        spaceAfter=6,
        leading=28,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#777777"),
        spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#2C4770"),
        spaceBefore=16,
        spaceAfter=6,
        borderPad=0,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#333333"),
        spaceAfter=6,
    )
    metric_label_style = ParagraphStyle(
        "MetricLabel",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#777777"),
        leading=12,
    )
    metric_value_style = ParagraphStyle(
        "MetricValue",
        parent=styles["Normal"],
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#2C4770"),
        leading=22,
    )
    metric_insight_style = ParagraphStyle(
        "MetricInsight",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#555555"),
        leading=11,
        italics=1,
    )
    chart_caption_style = ParagraphStyle(
        "ChartCaption",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        alignment=1,  # centre
        spaceAfter=12,
    )

    story = []

    # ── Cover / Header ──
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(plan.get("report_title", "Data Report"), title_style))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}  •  "
        f"Source: {csv_filename}  •  "
        f"{profile['row_count']:,} rows × {profile['column_count']} columns",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#2C4770"), spaceAfter=12))

    # ── Executive Summary ──
    story.append(Paragraph("Executive Summary", h2_style))
    story.append(Paragraph(plan.get("executive_summary", ""), body_style))

    # ── Key Metrics grid ──
    story.append(Paragraph("Key Metrics", h2_style))
    metrics = plan.get("key_metrics", [])

    # Build 2-column metric cards using a Table
    metric_cells = []
    row = []
    for i, m in enumerate(metrics):
        cell = [
            Paragraph(m.get("label", ""), metric_label_style),
            Paragraph(str(m.get("value", "")), metric_value_style),
            Paragraph(m.get("insight", ""), metric_insight_style),
        ]
        row.append(cell)
        if len(row) == 2:
            metric_cells.append(row)
            row = []
    if row:  # odd one out
        row.append("")
        metric_cells.append(row)

    if metric_cells:
        col_w = (A4[0] - 4 * cm) / 2
        metric_table = Table(metric_cells, colWidths=[col_w, col_w], rowHeights=None)
        metric_table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), colors.HexColor("#F0F4FA")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1),
             [colors.HexColor("#F0F4FA"), colors.HexColor("#E8EEF8")]),
            ("BOX",         (0, 0), (-1, -1), 0.5, colors.HexColor("#C5D0E6")),
            ("INNERGRID",   (0, 0), (-1, -1), 0.5, colors.HexColor("#C5D0E6")),
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",  (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(metric_table)
        story.append(Spacer(1, 0.4 * cm))

    # ── Charts ──
    if chart_paths:
        story.append(PageBreak())
        story.append(Paragraph("Charts & Visualisations", h2_style))
        story.append(HRFlowable(width="100%", thickness=1,
                                 color=colors.HexColor("#CCCCCC"), spaceAfter=10))

        usable_width = A4[0] - 4 * cm

        for item in chart_paths:
            img_path = item["path"]
            description = item.get("description", "")
            chart_title = item.get("title", "")

            if img_path and Path(img_path).exists():
                img = Image(img_path, width=usable_width, height=usable_width * 0.5)
                story.append(img)
                if description:
                    story.append(Paragraph(
                        f"<i>{chart_title}:</i> {description}", chart_caption_style
                    ))
                story.append(Spacer(1, 0.5 * cm))

    # ── Data Summary table ──
    story.append(PageBreak())
    story.append(Paragraph("Data Summary", h2_style))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#CCCCCC"), spaceAfter=10))

    numeric_stats = profile.get("numeric_stats", {})
    if numeric_stats:
        header = ["Column", "Min", "Max", "Mean", "Median", "Nulls"]
        rows = [header]
        for col, s in numeric_stats.items():
            rows.append([
                col,
                f"{s['min']:,}",
                f"{s['max']:,}",
                f"{s['mean']:,}",
                f"{s['median']:,}",
                str(s["nulls"]),
            ])

        col_widths = [5.5 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 1.8 * cm]
        summary_table = Table(rows, colWidths=col_widths)
        summary_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#2C4770")),
            ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0),  9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F5F7FA")]),
            ("FONTSIZE",     (0, 1), (-1, -1), 9),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
            ("ALIGN",        (1, 0), (-1, -1), "RIGHT"),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)

    # ── Conclusion ──
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Conclusion & Recommendations", h2_style))
    story.append(Paragraph(plan.get("conclusion", ""), body_style))

    # ── Footer note ──
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#CCCCCC"), spaceAfter=6))
    story.append(Paragraph(
        f"Report generated by CSV Report Agent using Azure OpenAI ({AZURE_DEPLOYMENT}).",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       fontSize=8, textColor=colors.HexColor("#AAAAAA")),
    ))

    doc.build(story)


# ─── Main agent ───────────────────────────────────────────────────────────────


def run(csv_path: str, output_folder: str):
    csv_filename = Path(csv_path).name
    timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_name     = f"report_{Path(csv_path).stem}_{timestamp}.pdf"
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    pdf_path = output_folder / pdf_name

    print(f"\n📊 CSV Report Agent")
    print(f"   CSV    : {csv_path}")
    print(f"   Output : {pdf_path}\n")

    # PERCEIVE
    print("1️⃣  Reading CSV...")
    df = read_csv(csv_path)
    profile = profile_dataframe(df)
    print(f"   {profile['row_count']:,} rows  ×  {profile['column_count']} columns")
    print(f"   Numeric  : {profile['numeric_columns']}")
    print(f"   Category : {profile['categorical_columns']}")

    # DECIDE
    print("\n2️⃣  Asking Azure OpenAI to design the report...")
    plan = decide_analysis(profile)
    print(f"   Title    : {plan.get('report_title')}")
    print(f"   Metrics  : {len(plan.get('key_metrics', []))} key metrics")
    print(f"   Charts   : {len(plan.get('charts', []))} charts planned")

    # GENERATE charts
    print("\n3️⃣  Rendering charts...")
    chart_results = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for chart_spec in plan.get("charts", []):
            print(f"   📈 {chart_spec.get('chart_type').upper()}: {chart_spec.get('title')}")
            img_path = render_chart(chart_spec, df, tmp_dir)
            chart_results.append({
                "path":        img_path,
                "title":       chart_spec.get("title", ""),
                "description": chart_spec.get("description", ""),
            })

        # ACT — build PDF while temp dir still exists
        print("\n4️⃣  Assembling PDF...")
        build_pdf(plan, chart_results, profile, csv_filename, str(pdf_path))

    print(f"\n✅ PDF saved → {pdf_path}\n")
    return str(pdf_path)


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV → AI-powered PDF report")
    parser.add_argument("--csv",    required=True, help="Path to input CSV file")
    parser.add_argument("--output", required=True, help="Output folder for the PDF")
    args = parser.parse_args()

    if not Path(args.csv).exists():
        print(f"❌ CSV file not found: {args.csv}")
        sys.exit(1)

    run(args.csv, args.output)