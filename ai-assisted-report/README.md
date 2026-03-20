# ai-assited-report-generator

Reads any CSV file, uses Azure OpenAI to decide what metrics and charts to generate, and exports a polished PDF report.

---

## Files

```
ai-assited-report-generator/
├── generate_report.py       # Main agent
├── generate_sample_csv.py    # Generate test CSV using AI
├── requirements.txt
├── .env                      # Your Azure key (not committed)
└── reports/                  # PDF output folder
```

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:
```
AZURE_ENDPOINT=your-endpoint-here
AZURE_OPENAI_KEY=your-key-here
```

---

## Run

**Step 1 — Get a CSV** (skip if you have your own)
```bash
python generate_sample_csv.py --topic "retail sales" --rows 50
# or any topic: "hospital records", "ecommerce orders", etc.
```

**Step 2 — Generate the PDF report**
```bash
python generate_report.py --csv sample_data.csv --output ./reports
```

PDF saved to `reports/report_<filename>_<timestamp>.pdf`

---

## Requirements

- Python 3.10+
- Azure OpenAI resource with `gpt-4o-mini` deployment