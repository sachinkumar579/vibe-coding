# RAG from Scratch 🔍

> Learn how Retrieval-Augmented Generation actually works by building a tiny one yourself — no LangChain, no LlamaIndex, no cloud bills. Just Python, Ollama, and about 130 lines of code you can read top to bottom.

This repo is a learning project. Instead of reading another tutorial about RAG, you run a working example, break it on purpose, and watch *why* each piece matters.

---

## What is RAG, in one paragraph

A language model only knows what it was trained on. It has never seen *your* code, *your* docs, or *your* PDFs. **Retrieval-Augmented Generation** fixes this: before asking the model a question, you first *retrieve* the most relevant pieces of your own data and hand them to the model alongside the question. The model then answers grounded in your data instead of guessing from training. That's the whole trick — retrieve first, generate second.

---

## What this project does

You point the tool at a Python file. It:

1. **Reads** the file and splits it into small overlapping chunks
2. **Embeds** each chunk into a vector (a list of numbers that captures meaning)
3. Waits for your question, then **embeds the question** too
4. **Retrieves** the chunks whose vectors are closest to your question
5. **Generates** an answer using a local LLM, grounded only in those retrieved chunks

Everything runs **locally** on your machine through [Ollama](https://ollama.ai). No API keys. No cost.

---

## The concepts you'll learn (and where they live in the code)

| Concept | What it means | Where in `rag.py` |
|---|---|---|
| **Chunking** | Splitting data into small focused pieces so retrieval is precise | `chunk_file()` |
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

### 4. Install the one Python dependency

```bash
pip install requests
```

That's the only library this project needs. Everything else is hand-written on purpose.

---

## Running it

Put `rag.py` and `sample_app.py` in the same folder, then:

```bash
python rag.py
```

You'll see:

```
Indexing sample_app.py ...
Indexed 5 chunks. Ask me about the code.

Q:
```

Type a question. Type `quit` (or just press Enter) to exit.

---

## Try these questions first

`sample_app.py` is a tiny fake banking app. Ask it about itself:

| Question | What should happen |
|---|---|
| `How are passwords stored?` | Retrieves the hashing function, explains SHA-256 |
| `What stops someone transferring more money than they have?` | Retrieves the transfer function, finds the balance check |
| `How is interest calculated?` | Retrieves the interest function |
| `How do I connect to the database?` | Should answer **"I don't know based on this code"** — there is no database code |

That last one is the important one. There is no database code in the file, so a well-behaved RAG system should *refuse to answer* rather than invent something. If it answers honestly, your **hallucination defense** is working.

---

## Watch it think

Every time you ask a question, the tool prints the chunks it retrieved and their similarity scores:

```
[retrieved chunks]
  0.648  def hash_password(password: str) -> str:
  0.602  def authenticate(username: str, password: str, users: dict) -> bool:
```

The number is the **cosine similarity** between your question and that chunk — higher means a closer match. This line *is* retrieval, made visible. Don't chase numbers near 1.0; what matters is the ranking and the gap between chunks.

---

## Experiments — this is where the real learning is

Don't stop at "it works." Break it on purpose:

### 1. Wreck the chunking
In `rag.py`, change `CHUNK_LINES = 8` to `CHUNK_LINES = 2`, re-run, and ask the password question again. Answers get worse because functions get sliced across chunks. Now you *feel* why chunk size is a real engineering decision.

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

Now you can see the instruction + retrieved code + your question, all concatenated into one string. That's prompt engineering in the raw.

### 4. Change how many chunks you retrieve
In `main()`, the line `scored[:2]` keeps the top 2 chunks. Try `scored[:1]` (less context) or `scored[:4]` (more). More isn't always better — extra chunks can add noise that confuses the model.

### 5. Test semantic search
Ask `how do I move money between accounts?` — notice it still finds the `transfer_funds` function even though you never used the word "transfer." That's the magic of embeddings: they match *meaning*, not keywords.

---

## Use it on your own code

Change one line at the top of `rag.py`:

```python
SOURCE_FILE = "sample_app.py"   # <- point this at any .py file
```

Point it at any Python file and ask questions about it. For larger files, tune `CHUNK_LINES` and `OVERLAP`.

---

## Project structure

```
.
├── rag.py          # The RAG tool — this is the one you run
├── sample_app.py   # A tiny banking app — the code the tool answers questions about
└── README.md       # This file
```

---

## How it works, step by step

1. **Index once at startup.** `chunk_file()` splits the source file into overlapping 8-line windows. Each chunk is embedded once via `nomic-embed-text` and stored in memory as `(text, vector)` pairs. Embedding once and caching avoids redundant work — your first lesson in why latency and cost matter.

2. **Embed the question.** When you type a question, it gets embedded into a vector the same way.

3. **Retrieve.** Cosine similarity scores your question vector against every chunk vector. The chunks are sorted by score and the top 2 are kept.

4. **Generate.** Those top chunks are pasted into a prompt that instructs `qwen2.5` to answer using only the provided code — and to say "I don't know" otherwise. The model returns the final answer.

---

## Why no framework?

LangChain and LlamaIndex hide exactly the parts you're trying to learn. By hand-writing chunking, cosine similarity, and the prompt, you can see every moving part. Once you understand the mechanics, reach for frameworks to save time — not to skip understanding.

---

## Where to go next

- Swap the in-memory list for a real **vector database** (pgvector, Chroma, Qdrant)
- Chunk on **function/class boundaries** instead of fixed line windows
- Index a **whole repo** of files instead of one
- Build a simple **eval set** — questions with known answers — to measure retrieval quality
- Let the model **call the search itself** as a tool — the first step toward an **agent**

---

## License

MIT — do whatever you want with it. It's a learning project.