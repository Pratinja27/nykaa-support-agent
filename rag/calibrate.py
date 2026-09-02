import chromadb
from sentence_transformers import SentenceTransformer


CHROMA_PATH = "chroma_data"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

IN_SCOPE_QUERIES = [
    "What is the return window for footwear?",
    "How long does a COD refund take?",
    "Can I exchange my shoes for another size?",
    "How long does standard delivery take?",
]

OUT_OF_SCOPE_QUERIES = [
    "What is the capital of France?",
    "Write a Python program to sort a list.",
]


def get_top_similarity(collection, model, query):
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=1
    )

    distance = results["distances"][0][0]
    similarity = 1 - distance

    return similarity, results["metadatas"][0][0]["document_id"]


def main():
    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_collection(
        "nykaa_sentence_chunks"
    )

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    print("=" * 60)
    print("TASK 4 - SIMILARITY CALIBRATION")
    print("=" * 60)

    in_scope_scores = []
    out_scope_scores = []

    print("\nIN-SCOPE QUERIES")

    for query in IN_SCOPE_QUERIES:
        similarity, document_id = get_top_similarity(
            collection,
            model,
            query
        )

        in_scope_scores.append(similarity)

        print(f"\nQuery: {query}")
        print(f"Top document: {document_id}")
        print(f"Top-1 similarity: {similarity:.4f}")

    print("\nOUT-OF-SCOPE QUERIES")

    for query in OUT_OF_SCOPE_QUERIES:
        similarity, document_id = get_top_similarity(
            collection,
            model,
            query
        )

        out_scope_scores.append(similarity)

        print(f"\nQuery: {query}")
        print(f"Top document: {document_id}")
        print(f"Top-1 similarity: {similarity:.4f}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print("\nIn-scope scores:")
    for score in in_scope_scores:
        print(f"{score:.4f}")

    print("\nOut-of-scope scores:")
    for score in out_scope_scores:
        print(f"{score:.4f}")

    print(
        f"\nLowest in-scope score: "
        f"{min(in_scope_scores):.4f}"
    )

    print(
        f"Highest out-of-scope score: "
        f"{max(out_scope_scores):.4f}"
    )


if __name__ == "__main__":
    main()