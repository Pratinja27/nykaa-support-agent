import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "chroma_data"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.45

# Initialize objects at module level for external import
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection("nykaa_fixed_chunks")
model = SentenceTransformer(EMBEDDING_MODEL)


def retrieve(query, top_k=3):
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    documents = []
    for i, text in enumerate(results["documents"][0]):
        distance = results["distances"][0][i]
        
        # Safe fallback for document_id metadata
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        doc_id = meta.get("document_id", "KB_CUSTOM")

        documents.append({
            "text": text,
            "similarity": 1 - distance,
            "document_id": doc_id
        })

    return documents


def generate_answer(query):
    results = retrieve(query)

    if not results or results[0]["similarity"] < SIMILARITY_THRESHOLD:
        return {
            "answer": "I don't know based on the available knowledge base.",
            "fallback": True,
            "similarity": results[0]["similarity"] if results else 0.0,
            "sources": []
        }

    context = "\n\n".join(result["text"] for result in results)

    answer = (
        "Based on the knowledge base:\n\n"
        + context
    )

    return {
        "answer": answer,
        "fallback": False,
        "similarity": results[0]["similarity"],
        "sources": [result["document_id"] for result in results]
    }