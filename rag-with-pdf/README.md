# RAG over a PDF, from Scratch 🔍📄

> Learn how Retrieval-Augmented Generation actually works by building a tiny one yourself — no LangChain, no LlamaIndex, no cloud bills. Just Python, Ollama, and about 150 lines of code you can read top to bottom.

This is a learning project. Instead of reading another tutorial about RAG, you run a working example over a **real PDF**, break it on purpose, and watch *why* each piece matters.

> **What changed:** this started life answering questions about a single Python source file. It now reads a **PDF**, extracts its text, and answers questions grounded in the document. The script auto-detects the file type — prose (PDF) is chunked by *words*, code is chunked by *lines* — so it still works on `.py` files too.

---

## What is RAG, in one paragraph

A language model only knows what it was trained on. It has never seen *your* docs, *your* code, or *your* PDFs. **Retrieval-Augmented Generation** fixes this: before asking the model a question, you first *retrieve* the most relevant pieces of your own data and hand them to the model alongside the question. The model then answers grounded in your data instead of guessing from training. That's the whole trick — retrieve first, generate second.

---

## What this project does

You point the tool at a PDF (or any text/code file). It:

1. **Reads** the file — extracting text from the PDF with `pypdf` — and splits it into small overlapping chunks
2. **Embeds** each chunk into a vector (a list of numbers that captures meaning)
3. Waits for your question, then **embeds the question** too
4. **Retrieves** the chunks whose vectors are closest to your question
5. **Generates** an answer using a local LLM, grounded only in those retrieved chunks

Everything runs **locally** on your machine through [Ollama](https://ollama.ai). No API keys. No cost.

The default document is `../tokenizer/How To Write Unmaintainable Code.pdf` — Roedy Green's classic, tongue-in-cheek essay.

---

## The concepts you'll learn (and where they live in the code)

| Concept | What it means | Where in `rag.py` |
|---|---|---|
| **PDF extraction** | Pulling raw text out of a PDF so it can be embedded | `read_source()` |
| **Chunking** | Splitting data into small focused pieces so retrieval is precise | `chunk_file()` / `_window()` |
| **Embeddings** | Turning text into vectors that capture meaning | `embed()` |
| **Vector search** | Finding similar vectors via cosine similarity | `cosine()` |
| **Context window** | The limited amount of text a model can read at once | the prompt built in `generate()` |
| **Prompt engineering** | Structuring instructions so the model behaves | the prompt string in `generate()` |
| **Hallucination defense** | Telling the model to say "I don't know" when ungrounded | the instruction in `generate()` |
| **Retrieval** | Picking the top-matching chunks for a question | the loop in `main()` |
| **Generation** | The model writing the final answer | `generate()` |

---

## Prerequisites

- **Python 3.8+**
- **[Ollama](https://ollama.ai)** installed and running
- About 1.3 GB of disk for the two models

---

## Setup

### 1. Install Ollama

Download it from [ollama.ai](https://ollama.ai) and install. On Windows and Mac, opening the app starts the background server automatically. On Linux, run `ollama serve`.

### 2. Pull the two models

This project uses two small models — one to create embeddings, one to generate answers:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
```

- `nomic-embed-text` — a dedicated embedding model. Turns text into a 768-number vector.
- `qwen2.5:1.5b` — a small, fast chat model. Writes the answers.

### 3. Confirm Ollama is running

```bash
curl http://localhost:11434/api/tags
```

You should get back JSON listing both models. If you do, the server is up.

### 4. Install the Python dependencies

```bash
pip install -r requirements.txt
```

Two libraries: `requests` (to talk to Ollama) and `pypdf` (to read the PDF). Everything else is hand-written on purpose.

---

## Running it

From this folder:

```bash
python rag.py
```

You'll see (chunk count depends on the document — a ~16k-word PDF yields ~135 chunks):

```
Indexing ../tokenizer/How To Write Unmaintainable Code.pdf ...
Indexed 135 chunks. Ask me about the document.

Q:
```

Indexing a whole PDF means embedding every chunk once, so the first startup takes a little while. Type a question, or `quit` (or just press Enter) to exit.

---

## Try these questions first

The default PDF is a satirical essay on writing deliberately awful code. Ask it about itself:

| Question | What should happen |
|---|---|
| `What is the goal of writing unmaintainable code?` | Retrieves the "specify each fact in as many places as possible" passage |
| `How should you name variables?` | Retrieves advice on misleading names, reserved-word lookalikes, misspellings |
| `What does it say about comments?` | Retrieves the section on lying or useless comments |
| `What is the boiling point of water?` | Should answer **"I don't know based on this document"** — it's not in the PDF |

That last one is the important one. The answer isn't in the document, so a well-behaved RAG system should *refuse to answer* rather than invent something. If it declines, your **hallucination defense** is working.

---

## Watch it think

Every time you ask a question, the tool prints the chunks it retrieved and their similarity scores:

```
[retrieved chunks]
  0.811  Sun AWT JavaDOC. Program Design The cardinal rule of writing unmaintainable code is...
  0.789  How To Write Unmaintainable Code Ensure a job for life ;-) Roedy Green...
```

The number is the **cosine similarity** between your question and that chunk — higher means a closer match. This line *is* retrieval, made visible. Don't chase numbers near 1.0; what matters is the ranking and the gap between chunks.

---

## Experiments — this is where the real learning is

Don't stop at "it works." Break it on purpose:

### 1. Wreck the chunking
In `rag.py`, change `CHUNK_WORDS = 150` to `CHUNK_WORDS = 20`, re-run, and ask a question again. Answers get worse because ideas get sliced across tiny chunks. Now you *feel* why chunk size is a real engineering decision.

### 2. See an embedding with your own eyes
Add this line in `main()` right after `q_vec = embed(question)`:

```python
print(len(q_vec), q_vec[:5])
```

You'll see it's 768 numbers. "Embeddings" stops being an abstract word.

### 3. See the exact prompt the model receives
Add this inside `generate()` right before the `requests.post(...)` call:

```python
print("PROMPT SENT:\n", prompt)
```

Now you can see the instruction + retrieved text + your question, all concatenated into one string. That's prompt engineering in the raw.

### 4. Change how many chunks you retrieve
In `main()`, the line `scored[:2]` keeps the top 2 chunks. Try `scored[:1]` (less context) or `scored[:4]` (more). More isn't always better — extra chunks can add noise that confuses the model.

### 5. Test semantic search
Ask a question using words that *don't* appear in the document but mean the same thing. Notice it still finds the right passage — that's the magic of embeddings: they match *meaning*, not keywords.

---

## Use it on your own document

Change one line at the top of `rag.py`:

```python
SOURCE_FILE = "../tokenizer/How To Write Unmaintainable Code.pdf"   # <- point this at any .pdf or text/code file
```

Point it at any PDF and ask questions about it. The script picks the chunking strategy by extension:

- **`.pdf`** → text is extracted and chunked by *words* (`CHUNK_WORDS` / `WORD_OVERLAP`)
- **anything else** (e.g. a `.py` file) → chunked by *lines* (`CHUNK_LINES` / `LINE_OVERLAP`)

For larger documents, tune those sizes.

---

## Project structure

```
.
├── rag.py            # The RAG tool — this is the one you run
├── requirements.txt  # requests + pypdf
└── README.md         # This file
```

The default PDF lives in the sibling `../tokenizer/` folder.

---

## How it works, step by step

1. **Index once at startup.** `read_source()` extracts the PDF text, then `chunk_file()` splits it into overlapping word windows. Each chunk is embedded once via `nomic-embed-text` and stored in memory as `(text, vector)` pairs. Embedding once and caching avoids redundant work — your first lesson in why latency and cost matter.

2. **Embed the question.** When you type a question, it gets embedded into a vector the same way.

3. **Retrieve.** Cosine similarity scores your question vector against every chunk vector. The chunks are sorted by score and the top 2 are kept.

4. **Generate.** Those top chunks are pasted into a prompt that instructs `qwen2.5` to answer using only the provided text — and to say "I don't know" otherwise. The model returns the final answer.

---

## Why no framework?

LangChain and LlamaIndex hide exactly the parts you're trying to learn. By hand-writing PDF extraction, chunking, cosine similarity, and the prompt, you can see every moving part. Once you understand the mechanics, reach for frameworks to save time — not to skip understanding.

---

## Where to go next

- Swap the in-memory list for a real **vector database** (pgvector, Chroma, Qdrant)
- Chunk on **sentence/paragraph boundaries** instead of fixed word windows
- Index a **folder of PDFs** instead of one file
- Build a simple **eval set** — questions with known answers — to measure retrieval quality
- Let the model **call the search itself** as a tool — the first step toward an **agent**

---

## License

MIT — do whatever you want with it. It's a learning project.
