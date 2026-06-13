"""
rag.py — A minimal RAG (Retrieval-Augmented Generation) tool, from scratch.

It reads a Python source file, lets you ask questions about it in plain English,
and answers using the actual code as grounding.

No frameworks. Every step is hand-written so you can see what's happening.
Run it:  python rag.py
Then type questions. Type 'quit' to exit.
"""

import requests   # pip install requests
import math
from pypdf import PdfReader   # pip install pypdf   (only needed for PDFs)

OLLAMA = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"   # turns text -> 768-number vector
CHAT_MODEL  = "qwen2.5:1.5b"       # generates the answer
SOURCE_FILE = "../tokenizer/How To Write Unmaintainable Code.pdf"   # what we RAG over


# ---------------------------------------------------------------------------
# STEP 1 — CHUNKING
# Models retrieve better over small focused pieces than one giant blob.
# We split the source into overlapping windows. Overlap means an idea that
# straddles a boundary still shows up whole in at least one chunk.
#
# Code reads naturally in LINES, but prose (a PDF) reads in WORDS — so we pick
# the unit based on the file type. Try changing the sizes and watch retrieval
# quality change.
# ---------------------------------------------------------------------------
CHUNK_LINES = 8      # code: lines per chunk
LINE_OVERLAP = 3
CHUNK_WORDS = 150    # prose: words per chunk
WORD_OVERLAP = 30


def read_source(path):
    """Return the raw text of a source file (.pdf extracted, otherwise read as-is)."""
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _window(units, size, overlap, joiner):
    """Slide a fixed-size window over a list of units, leaving an overlap."""
    chunks = []
    start = 0
    while start < len(units):
        text = joiner.join(units[start:start + size])
        if text.strip():                     # skip empty chunks
            chunks.append(text)
        start += size - overlap              # step forward, leaving overlap
    return chunks


def chunk_file(path):
    text = read_source(path)
    if path.lower().endswith(".pdf"):
        return _window(text.split(), CHUNK_WORDS, WORD_OVERLAP, " ")     # prose -> words
    return _window(text.splitlines(keepends=True), CHUNK_LINES, LINE_OVERLAP, "")  # code -> lines


# ---------------------------------------------------------------------------
# STEP 2 — EMBEDDINGS
# Ask Ollama to turn a piece of text into a vector (a list of 768 numbers)
# that captures its meaning. Similar meaning -> vectors that point the same way.
# This is INFERENCE: we're running a model to get an output.
# ---------------------------------------------------------------------------
def embed(text):
    r = requests.post(f"{OLLAMA}/api/embeddings",
                      json={"model": EMBED_MODEL, "prompt": text})
    r.raise_for_status()
    return r.json()["embedding"]


# ---------------------------------------------------------------------------
# STEP 3 — COSINE SIMILARITY  (the heart of VECTOR SEARCH)
# Two vectors are "similar" if they point in the same direction. Cosine
# similarity = dot product / (length * length). 1.0 = identical direction.
# A real VECTOR DATABASE does exactly this, just faster and at scale.
# ---------------------------------------------------------------------------
def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# STEP 4 — GENERATION  (the "G" in RAG, + PROMPT ENGINEERING)
# We hand the retrieved code to the chat model and tell it to answer ONLY
# from that code. The instruction to say "I don't know" is our defense against
# HALLUCINATION — without it the model will happily invent answers.
# ---------------------------------------------------------------------------
def generate(question, context_chunks):
    context = "\n---\n".join(context_chunks)
    
    prompt = (
        "You are a helpful assistant. Answer the question using ONLY the text "
        "below. If the answer is not in the text, say \"I don't know based on "
        "this document.\"\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\nANSWER:"
    )
    r = requests.post(f"{OLLAMA}/api/generate",
                      json={"model": CHAT_MODEL, "prompt": prompt, "stream": False})
    r.raise_for_status()
    return r.json()["response"].strip()


# ---------------------------------------------------------------------------
# PUT IT TOGETHER
# ---------------------------------------------------------------------------
def main():
    print("Indexing", SOURCE_FILE, "...")

    # Chunk, then embed every chunk once and keep them in memory.
    # (Re-embedding on every question would be wasteful — this is your first
    #  taste of why caching matters for LATENCY and cost.)
    chunks = chunk_file(SOURCE_FILE)
    index = [(c, embed(c)) for c in chunks]
    print(f"Indexed {len(index)} chunks. Ask me about the document.\n")

    while True:
        question = input("Q: ").strip()
        if question.lower() in ("quit", "exit", ""):
            break

        # RETRIEVAL: embed the question, score against every chunk, take top 2.
        q_vec = embed(question)
        scored = [(cosine(q_vec, vec), text) for (text, vec) in index]
        scored.sort(reverse=True)            # highest similarity first
        top = [text for (score, text) in scored[:2]]

        # Peek at what got retrieved — this is your eyeball EVALUATION step.
        print("\n[retrieved chunks]")
        for score, text in scored[:2]:
            first_line = text.strip().splitlines()[0]
            print(f"  {score:.3f}  {first_line}")

        # GENERATION grounded in the retrieved chunks.
        answer = generate(question, top)
        print("\nA:", answer, "\n")


if __name__ == "__main__":
    main()