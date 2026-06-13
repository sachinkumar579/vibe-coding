"""
rag.py — A minimal RAG (Retrieval-Augmented Generation) tool, from scratch.

It reads a Python source file, lets you ask questions about it in plain English,
and answers using the actual code as grounding.

No frameworks. Every step is hand-written so you can see what's happening.
Run it:  python rag.py
Then type questions. Type 'quit' to exit.
"""

import requests   # pip install requests   (the only dependency)
import math

OLLAMA = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"   # turns text -> 768-number vector
CHAT_MODEL  = "qwen2.5:1.5b"       # generates the answer
SOURCE_FILE = "sample_app.py"      # the codebase we're RAG-ing over


# ---------------------------------------------------------------------------
# STEP 1 — CHUNKING
# Models retrieve better over small focused pieces than one giant blob.
# We split the file into overlapping windows of lines. Overlap means a function
# that straddles a boundary still shows up whole in at least one chunk.
# Try changing CHUNK_LINES / OVERLAP later and watch retrieval quality change.
# ---------------------------------------------------------------------------
CHUNK_LINES = 8
OVERLAP = 3

def chunk_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    chunks = []
    start = 0
    while start < len(lines):
        end = start + CHUNK_LINES
        text = "".join(lines[start:end])
        if text.strip():                      # skip empty chunks
            chunks.append(text)
        start += CHUNK_LINES - OVERLAP        # step forward, leaving overlap
    return chunks


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
        "You are a code assistant. Answer the question using ONLY the code "
        "below. If the answer is not in the code, say \"I don't know based on "
        "this code.\"\n\n"
        f"CODE:\n{context}\n\n"
        f"QUESTION: {question}\n\nANSWER:"
    )
    print("PROMPT SENT:\n", prompt)
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
    print(f"Indexed {len(index)} chunks. Ask me about the code.\n")

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