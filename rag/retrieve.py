import chromadb
from sentence_transformers import SentenceTransformer

VECTOR_DB_DIR = "chroma_data"
MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.50  # Default value; updated after running calibration script


def retrieve_context(collection_name: str, query: str, top_k: int = 3):
    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    collection = client.get_collection(collection_name)
    encoder = SentenceTransformer(MODEL_NAME)

    query_vector = encoder.encode([query], normalize_embeddings=True).tolist()
    
    raw_results = collection.query(
        query_embeddings=query_vector,
        n_results=top_k
    )

    documents = raw_results["documents"][0]
    metadatas = raw_results["metadatas"][0]
    distances = raw_results["distances"][0]

    filtered_results = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        sim = round(1.0 - dist, 4)
        filtered_results.append({
            "text": doc,
            "metadata": meta,
            "similarity": sim
        })

    # Top similarity evaluation
    top_score = filtered_results[0]["similarity"] if filtered_results else 0.0
    is_in_scope = top_score >= SIMILARITY_THRESHOLD

    return {
        "query": query,
        "is_in_scope": is_in_scope,
        "top_similarity": top_score,
        "chunks": filtered_results if is_in_scope else []
    }


if __name__ == "__main__":
    sample_q = "How long do I have to return footwear?"
    res = retrieve_context("nykaa_sentence_chunks", sample_q)

    print(f"Query: {res['query']}")
    print(f"In-Scope Status: {res['is_in_scope']} (Top Similarity: {res['top_similarity']})")
    print(f"Retrieved Chunks Count: {len(res['chunks'])}")