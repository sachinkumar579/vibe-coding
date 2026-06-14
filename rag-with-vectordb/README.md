# RAG with a Vector Database 🗄️

> The same tiny RAG pipeline as [`rag-app-in-local`](../rag-app-in-local), with one
> upgrade that matters in the real world: the vectors now live in a real **vector
> database** ([ChromaDB](https://www.trychroma.com)) instead of a Python list.

This is the natural "step 5" from the first project's *Where to go next* list. You
already understand chunking, embeddings, cosine similarity, and grounded generation.
Now you swap the hand-written in-memory search for a proper vector store and *feel*
what that buys you.

---

## What changes, and why it matters

The earlier projects did this on every run:

```python
index = [(c, embed(c)) for c in chunks]                 # embed everything, every time
scored = [(cosine(q_vec, vec), text) for text, vec in index]   # scan all vectors by hand
```

This project replaces both lines with a vector DB. Three concrete wins:

| Win | Before (in-memory list) | After (ChromaDB) |
|---|---|---|
| **Persistence** | Re-embeds the whole file every launch | Embeds once, saves to disk, reuses forever |
| **Speed** | Full scan + manual `cosine()` over every chunk | Indexed approximate-nearest-neighbour search (HNSW) |
| **Metadata** | Just `(text, vector)` pairs | Each vector carries its source file + chunk number, so answers can **cite sources** |

You also get **incremental indexing** for free: each chunk's ID is a hash of its
text, so re-running only embeds chunks that actually changed.

---

## Prerequisites

- **Python 3.8+**
- **[Ollama](https://ollama.ai)** installed and running
- The two models from the first project:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
```

---

## Setup

```bash
pip install -r requirements.txt
```

That installs `requests` (to talk to Ollama) and `chromadb` (the vector store).
Chroma runs **embedded** — there's no server to start and no cloud account.

---

## Running it

```bash
python rag.py
```

First run:

```
Indexing sample_app.py ...
Index ready: 5 chunks (5 newly embedded this run). Ask me about the code.

Q:
```

**Run it a second time** and watch the difference:

```
Index ready: 5 chunks (0 newly embedded this run). Ask me about the code.
```

Zero re-embedding — the vectors were loaded straight from the `chroma_db/` folder
on disk. *That* is the persistence win, made visible.

---

## Watch it think

Every question prints the retrieved chunks, now with their **source location**:

```
[retrieved chunks]
  sim=0.648  (sample_app.py chunk 0)  def hash_password(password: str) -> str:
  sim=0.602  (sample_app.py chunk 1)  def authenticate(username: str, password: str, users: dict) -> bool:
```

`sim` is cosine similarity (`1 - distance`, since Chroma reports distance). The
`(source chunk N)` part comes from the **metadata** we stored alongside each vector —
the foundation for citing sources in answers.

---

## Try these questions first

`sample_app.py` is a tiny fake banking app. Ask it about itself:

| Question | What should happen |
|---|---|
| `How are passwords stored?` | Retrieves the hashing function, explains SHA-256 |
| `What stops someone transferring more money than they have?` | Retrieves the transfer function, finds the balance check |
| `How is interest calculated?` | Retrieves the interest function |
| `How do I connect to the database?` | Should answer **"I don't know based on this code"** — there is no database code |

---

## Experiments

### 1. Prove persistence is real
Run `python rag.py` once, quit, run it again. The second run says
`0 newly embedded`. Now delete the `chroma_db/` folder and run again — back to
`5 newly embedded`. You just watched the index live on disk.

### 2. Prove incremental indexing works
Edit one function in `sample_app.py`, then re-run. Only the chunks containing your
edit get re-embedded; the rest are skipped because their content hash is unchanged.

### 3. Tune the index
Change `TOP_K` at the top of `rag.py` (try 1, then 4) and watch how much context the
model gets. More isn't always better — extra chunks can add noise.

### 4. Point it at your own code
Change `SOURCE_FILE = "sample_app.py"` to any `.py` file. Delete `chroma_db/` so it
re-indexes the new file from scratch.

---

## How it maps to the from-scratch version

| Concept | From-scratch project | This project |
|---|---|---|
| Chunking | `chunk_file()` | `chunk_file()` (identical) |
| Embeddings | `embed()` via Ollama | `embed()` via Ollama (identical, on purpose) |
| Vector search | hand-written `cosine()` over a list | `collection.query()` over an HNSW index |
| Storage | Python list in RAM | persistent `chroma_db/` folder |
| Metadata | none | `{source, chunk}` per vector |

We deliberately kept our own `embed()` call instead of letting Chroma embed for us —
the embedding step stays visible, which is the whole point of the learning arc.

---

## Where to go next

- **Cite sources in the answer** — you already store the metadata; feed it into the prompt
- **Hybrid search** — combine vector similarity with keyword/BM25 matching
- **Reranking** — over-fetch top-10, then rerank down to top-3
- **Index a whole repo** — walk a directory, store each file's path as metadata
- Swap Chroma for **Qdrant** (Docker) or **pgvector** to see a client/server vector DB

---

## Project structure

```
.
├── rag.py             # The RAG tool, now backed by ChromaDB — run this
├── sample_app.py      # A tiny banking app — the code the tool answers questions about
├── requirements.txt   # requests + chromadb
└── README.md          # This file
```

---

## License

MIT — it's a learning project.
