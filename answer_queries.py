# general utiliies
import os, glob, dotenv, time
dotenv.load_dotenv()

FETCH_K = int(os.environ.get("FETCH_K", 3))

import pdf_helper   # helper module that processes initial Corpus

# for converting chunks in to embeddings, and then storing them
import numpy as np
from sentence_transformers import SentenceTransformer # for text -> vector embedding
import faiss # an example of a vector DB (currently stores in the memory)

import ollama


if __name__ == "__main__":
    pdf_helper.process_pdf_to_txt()    # convert pdfs to txt files
    pdf_helper.chunk_processed_txt()   # create chunks from txt files

    # "CHUNKS_OUTPUT_DIRECTORY" has .txt files where each line of a file is a chunk 
    chunk_files = glob.glob(os.path.join(pdf_helper.CHUNKS_OUTPUT_DIRECTORY, "*.txt"))

    print("Starting Embedding Generation")
    embed_start = time.time()

    chunks = []

    # read each line of each file in "CHUNKS_OUTPUT_DIRECTORY" and collect it into "chunks"
    for txt_path in chunk_files:
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:                # skip empty lines
                    chunks.append(line)
    
    # TA demo code for converting chunks to embeddings and storing them in FAISS
    # model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cuda")
    emb_matrix = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
    dim = emb_matrix.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine works with normalized vectors using inner product
    index.add(emb_matrix)           # store embeddings
    print(f"Embed Total: {time.time() - embed_start}")
    emb_matrix = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
    dim = emb_matrix.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine works with normalized vectors using inner product
    index.add(emb_matrix)           # store embeddings
    print(f"Embed Total: {time.time() - embed_start}")

    # turn query text in to an embeddings, then search our index
    def search(query, k=3):
        q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        scores, idxs = index.search(q_emb, k)  # (1, k)
        results = []
        for rank, (i, s) in enumerate(zip(idxs[0], scores[0]), start=1):
            results.append({"rank": rank, "score": float(s), "chunk": chunks[i]})
        return results

    query = input("What would you like to know about? Answer with \"X\" or nothing to exit.\n\t")
    while query and query != "X":
        # TODO: sanitize user input to prevent injection

        hits = search(query, k=FETCH_K)

        print("\nTop matches:")
        for h in hits:
            print(f"[{h['rank']}] score={h['score']:.3f}\n{h['chunk']}\n---")
        print("\n\n")
        
        # import pickle
        # with open("hits.pkl", "wb") as f:
            # pickle.dump(hits, f)

        # TODO: Add a ollama endpoint and provide the embeddings as context to it.

        # Construct a RAG-style prompt by injecting the retrieved hits
        context = "\n".join([hit['chunk'] for hit in hits])
        prompt = f"Answer the following question using the provided context.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"

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
        query = input("What would you like to know about? Answer with \"X\" or nothing to exit.\n")