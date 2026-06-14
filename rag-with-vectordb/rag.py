"""
rag.py — A minimal RAG tool backed by a real VECTOR DATABASE (ChromaDB).

This is the same RAG pipeline as the earlier from-scratch projects, with one
big upgrade: instead of holding vectors in a Python list and scanning them all
with a hand-written cosine() on every question, we store them in Chroma.

What that buys us:
  * PERSISTENCE — embed once, reuse forever. Re-running is instant; we only
    embed chunks the DB hasn't seen before.
  * SPEED       — Chroma uses an approximate-nearest-neighbour (HNSW) index,
    not a full scan, so search stays fast as the data grows.
  * METADATA    — each vector is stored with its source file + chunk number,
    so answers can CITE where they came from.

No cloud, no API keys — Chroma runs embedded, Ollama runs locally.
Run it:  python rag.py
Then type questions. Type 'quit' to exit.
"""

import hashlib

import requests           # pip install requests   (talks to Ollama)
import chromadb           # pip install chromadb    (the vector database)

OLLAMA = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"   # turns text -> 768-number vector
CHAT_MODEL  = "qwen2.5:1.5b"       # generates the answer
SOURCE_FILE = "sample_app.py"      # the codebase we're RAG-ing over

DB_DIR     = "chroma_db"           # folder where Chroma persists the index
COLLECTION = "code_chunks"         # a "collection" is Chroma's table of vectors
TOP_K      = 2                     # how many chunks to retrieve per question


# ---------------------------------------------------------------------------
# STEP 1 — CHUNKING  (unchanged from the from-scratch version)
# Models retrieve better over small focused pieces than one giant blob.
# We split the file into overlapping windows of lines so a function that
# straddles a boundary still shows up whole in at least one chunk.
# ---------------------------------------------------------------------------
CHUNK_LINES = 12
OVERLAP = 4

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
# STEP 2 — EMBEDDINGS  (still our own Ollama call, on purpose)
# Chroma can embed for you, but we keep this explicit so the embedding step
# stays visible — that's the whole point of the learning arc. We compute the
# vector here and hand it to Chroma to STORE and SEARCH.
# ---------------------------------------------------------------------------
def embed(text):
    r = requests.post(f"{OLLAMA}/api/embeddings",
                      json={"model": EMBED_MODEL, "prompt": text})
    r.raise_for_status()
    return r.json()["embedding"]


# ---------------------------------------------------------------------------
# STEP 3 — THE VECTOR DATABASE  (this replaces the in-memory list + cosine())
# We open a PERSISTENT Chroma client pointed at a folder on disk. The collection
# is told to use "cosine" distance — the exact same maths we wrote by hand
# before, just indexed and done for us.
#
# Each chunk gets a content-hash as its ID. Because the ID is derived from the
# text, re-running only embeds chunks that changed — unchanged chunks are
# already in the DB and we skip them. That is INCREMENTAL INDEXING for free.
# ---------------------------------------------------------------------------
def build_or_load_index():
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},   # search by cosine similarity
    )

    chunks = chunk_file(SOURCE_FILE)
    new_count = 0
    for i, chunk in enumerate(chunks):
        cid = hashlib.sha256(chunk.encode()).hexdigest()   # stable ID per chunk

        # Already embedded on a previous run? Skip it — this is the persistence win.
        if collection.get(ids=[cid])["ids"]:
            continue

        collection.add(
            ids=[cid],
            embeddings=[embed(chunk)],                       # we compute the vector
            documents=[chunk],                               # Chroma stores the text
            metadatas=[{"source": SOURCE_FILE, "chunk": i}], # ...and where it came from
        )
        new_count += 1

    return collection, new_count


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
    r = requests.post(f"{OLLAMA}/api/generate",
                      json={"model": CHAT_MODEL, "prompt": prompt, "stream": False})
    r.raise_for_status()
    return r.json()["response"].strip()


# ---------------------------------------------------------------------------
# PUT IT TOGETHER
# ---------------------------------------------------------------------------
def main():
    print("Indexing", SOURCE_FILE, "...")
    collection, new_count = build_or_load_index()
    total = collection.count()
    print(f"Index ready: {total} chunks ({new_count} newly embedded this run). "
          "Ask me about the code.\n")

    while True:
        question = input("Q: ").strip()
        if question.lower() in ("quit", "exit", ""):
            break

        # RETRIEVAL: embed the question, then let Chroma find the nearest vectors.
        # No manual cosine loop — the database does the search.
        q_vec = embed(question)
        res = collection.query(query_embeddings=[q_vec], n_results=TOP_K)

        docs  = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]           # cosine DISTANCE (0 = identical)

        # Peek at what got retrieved — your eyeball EVALUATION step.
        # Chroma returns distance; similarity = 1 - distance for cosine space.
        print("\n[retrieved chunks]")
        for doc, meta, dist in zip(docs, metas, dists):
            first_line = doc.strip().splitlines()[0]
            print(f"  sim={1 - dist:.3f}  ({meta['source']} chunk {meta['chunk']})  {first_line}")

        # GENERATION grounded in the retrieved chunks.
        answer = generate(question, docs)
        print("\nA:", answer, "\n")


if __name__ == "__main__":
    main()
