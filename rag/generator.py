import chromadb
from sentence_transformers import SentenceTransformer


CHROMA_PATH = "chroma_data"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.30


def retrieve(query, top_k=3):
    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_collection(
       "nykaa_fixed_chunks"
    )

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

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

        documents.append({
            "text": text,
            "similarity": 1 - distance,
            "document_id": results["metadatas"][0][i]["document_id"]
        })

    return documents


def generate_answer(query):
    results = retrieve(query)

    top_similarity = results[0]["similarity"]

    if top_similarity < SIMILARITY_THRESHOLD:
        return {
            "answer": "I don't know based on the available knowledge base.",
            "fallback": True,
            "similarity": top_similarity,
            "sources": []
        }

    context = "\n\n".join(
        result["text"]
        for result in results
    )

    answer = (
        "Based on the knowledge base:\n\n"
        + context
    )

    return {
        "answer": answer,
        "fallback": False,
        "similarity": top_similarity,
        "sources": [
            result["document_id"]
            for result in results
        ]
    }


if __name__ == "__main__":
    queries = [
        "What is the return window for footwear?",
        "How long does a COD refund take?",
        "How long does standard delivery take?",
        "Can I exchange my shoes for another size?",
        "Can I cancel an order after it has shipped?",
        "What is the capital of France?"
    ]

    for query in queries:
        print("\n" + "=" * 60)
        print(f"Query: {query}")

        result = generate_answer(query)

        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Fallback: {result['fallback']}")
        print(f"Answer:\n{result['answer']}")
        print(f"Sources: {result['sources']}")