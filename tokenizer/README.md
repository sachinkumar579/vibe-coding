# PDF Token Counter 🔢

A tiny script that counts how many **tokens** (and words) a PDF contains, using
OpenAI's [`tiktoken`](https://github.com/openai/tiktoken) tokenizer. Handy for
estimating how much of an LLM's context window a document will eat — and the
rough API cost — before you send it.

---

## How it works

1. **Read** the PDF and extract its text with [`pypdf`](https://pypdf.readthedocs.io)
2. **Encode** that text with the `tiktoken` encoding for the chosen model
3. **Print** the total token and word counts

---

## Prerequisites

- Python 3.8+

## Setup

```bash
# (optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

Or install it as a package (gives you a `count-tokens` command):

```bash
pip install .
```

---

## Usage

```bash
python count_tokens.py path/to/your_file.pdf
```

Pick a different model's tokenizer with `-m`:

```bash
python count_tokens.py path/to/your_file.pdf -m gpt-4o
```

Add `--cost` to also estimate the input (prompt) price for that model:

```bash
python count_tokens.py path/to/your_file.pdf -m gpt-4o --cost
```

If installed as a package:

```bash
count-tokens path/to/your_file.pdf
```

### Example output

```
Total tokens: 12843
Total words: 9210
Estimated input cost (gpt-4o @ $2.50/1M): $0.0321
```

---

## Notes

- Cost estimates use the **input/prompt** price only and are approximate —
  update the `INPUT_PRICE_PER_MILLION` table in `count_tokens.py` as provider
  pricing changes.

- Token counts vary by model because different models use different encodings.
  `gpt-3.5-turbo` and `gpt-4` share the `cl100k_base` encoding; `gpt-4o` uses
  `o200k_base`.
- Scanned/image-only PDFs have no extractable text — you'd need OCR first.

---

## License

MIT — do whatever you want with it.
