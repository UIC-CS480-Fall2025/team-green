# general utiliies
import os, glob, dotenv, time
import psycopg2
import pdf_helper   # helper module that processes initial Corpus
from sentence_transformers import SentenceTransformer # for text -> vector embedding
import subprocess    # detect at runtime if we have cuda installed
import ollama

dotenv.load_dotenv()

FETCH_K = int(os.environ.get("FETCH_K", 5))

conn = psycopg2.connect(database="postgres",
        host="localhost",
        user="postgres",
        password="postgres",
        port="5432")

model = None          # SentenceTransformer model
chunks = []           # list[str]
dimension = None      # embedding dimension

# use CLI function to figure out if the computer has CUDA installed
def has_cuda():
    try:
        result = subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def start_model():
    global model, dimension

    print("Loading SentenceTransformer model...")
    model_name = "all-MiniLM-L6-v2"

    # if system has CUDA, SentenceTransformer will use it automatically
    model = SentenceTransformer(model_name)

    # determine embedding vector size
    test_vec = model.encode(["test"], convert_to_numpy=True)
    dimension = test_vec.shape[1]

    print(f"Model loaded. Embedding dimension = {dimension}")


def embed_and_index_chunks():
    global chunks, model

    print("Embedding chunks...")
    start = time.time()

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # Insert embeddings into psql database
    # TODO: make sure table format matches
    cur = conn.cursor()
    for chunk, embedding in zip(chunks, embeddings):
        insert_query = """
        INSERT INTO cs480_finalproject.embeddings (chunk, embedding)
        VALUES (%s, %s)"""
        cur.execute(insert_query, (chunk, embedding.tolist()))
    conn.commit()

    # Create an HNSW index for searching
    create = """CREATE INDEX IF NOT EXISTS hnsw_index ON embeddings USING hnsw (embedding);"""
    cur.execute(create)
    conn.commit()
    cur.close()

    print(f"Embedding & indexing complete. Took {time.time() - start:.2f} seconds")

def update_all_chunks():
    global chunks

    check_files = glob.glob(os.path.join(pdf_helper.CHUNKS_OUTPUT_DIRECTORY, "*.txt"))
    if not check_files:
        print("Chunked texts not found — regenerating.")
        pdf_helper.process_pdf_to_txt()
        pdf_helper.chunk_processed_txt()
        print("Chunking complete.")

    chunk_files = glob.glob(os.path.join(pdf_helper.CHUNKS_OUTPUT_DIRECTORY, "*.txt"))

    chunks = []
    for txt_path in chunk_files:
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append(line)

    print(f"Loaded {len(chunks)} chunks.")

def init_rag():
    """
    Call this once in any external script.
    """
    start_model()
    update_all_chunks()
    embed_and_index_chunks()

    print("RAG system initialized.")


# turn query text in to an embedding, then search our index
def search(query, k=FETCH_K):
    global model

    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]

    # Search nearest neighbors
    cur = conn.cursor()
    # TODO: check query
    search_query = """SELECT id, chunk, embedding <=> %s AS distance
    FROM embeddings
    ORDER BY embedding <=> %s
    LIMIT %s;"""
    cur.execute(search_query, (q_emb.tolist(), q_emb.tolist(), k))
    results = cur.fetchall()
    cur.close()

    top_k = []
    for rank, item in enumerate(results[:k], start=1):
        top_k.append({
            "rank": rank,
            "score": item["score"],
            "chunk": item["chunk"]
        })

    return top_k

def queryDB():
    query = input("What would you like to know about? Answer with \"X\" or nothing to exit.\n->")
    while query and query != "X":
        # TODO: sanitize user input to prevent injection

        hits = search(query, k=FETCH_K)

        print("\nTop matches:")
        for h in hits:
            print(f"[{h['rank']}] score={h['score']:.3f}\n{h['chunk'][:200]}...\n---")
        print("\n\n")

        print("Thinking...")
        # Construct a RAG-style prompt by injecting the retrieved hits
        context = "\n".join([hit['chunk'] for hit in hits])
        prompt = f"Answer the following question grounded on, but not absolutely limited to, the provided context.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"

        # Query the local Ollama endpoint
        response = ollama.chat(
            model="llama3",   # replace with the model you have locally
            messages=[
                {"role": "system", "content": "You are a domain expert assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        print("\n\n")
        print(response["message"]["content"])
        print("\n\n")
        query = input("What would you like to know about? Answer with \"X\" or nothing to exit.\n->")

if __name__ == "__main__":
    init_rag()
    queryDB()
