import chromadb
from sentence_transformers import SentenceTransformer


CHROMA_PATH = "chroma_data"
MODEL_NAME = "all-MiniLM-L6-v2"

QUERIES = [
    {
        "query": "What is the return window for footwear?",
        "relevant_docs": {"KB001"},
    },
    {
        "query": "How long does a COD refund take?",
        "relevant_docs": {"KB002"},
    },
    {
        "query": "How long does standard delivery take?",
        "relevant_docs": {"KB003"},
    },
    {
        "query": "Can I exchange my shoes for another size?",
        "relevant_docs": {"KB009"},
    },
    {
        "query": "Can I cancel an order after it has shipped?",
        "relevant_docs": {"KB006"},
    },
]


def get_collection(name):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(name)


def evaluate_collection(collection_name):
    model = SentenceTransformer(MODEL_NAME)
    collection = get_collection(collection_name)

    print("\n" + "=" * 70)
    print(f"COLLECTION: {collection_name}")
    print("=" * 70)

    precision_scores = []
    recall_scores = []

    for item in QUERIES:
        query = item["query"]
        relevant_docs = item["relevant_docs"]

        embedding = model.encode(
            [query],
            normalize_embeddings=True
        ).tolist()

        results = collection.query(
            query_embeddings=embedding,
            n_results=3
        )

        retrieved_docs = []

        for metadata in results["metadatas"][0]:
            doc_id = metadata["document_id"]

            if doc_id not in retrieved_docs:
                retrieved_docs.append(doc_id)

        retrieved_set = set(retrieved_docs)

        true_positives = retrieved_set.intersection(
            relevant_docs
        )

        precision = len(true_positives) / len(retrieved_set)

        recall = len(true_positives) / len(relevant_docs)

        precision_scores.append(precision)
        recall_scores.append(recall)

        print("\nQuery:")
        print(query)

        print(f"Relevant documents: {sorted(relevant_docs)}")
        print(f"Retrieved documents: {retrieved_docs}")
        print(f"Relevant retrieved: {sorted(true_positives)}")

        print(
            f"Precision@3 = "
            f"{len(true_positives)}/{len(retrieved_set)} "
            f"= {precision:.3f}"
        )

        print(
            f"Recall@3 = "
            f"{len(true_positives)}/{len(relevant_docs)} "
            f"= {recall:.3f}"
        )

    avg_precision = sum(precision_scores) / len(precision_scores)
    avg_recall = sum(recall_scores) / len(recall_scores)

    print("\n" + "-" * 70)
    print(f"Average Precision@3: {avg_precision:.3f}")
    print(f"Average Recall@3: {avg_recall:.3f}")
    print("-" * 70)

    return avg_precision, avg_recall


if __name__ == "__main__":
    fixed = evaluate_collection(
        "nykaa_fixed_chunks"
    )

    sentence = evaluate_collection(
        "nykaa_sentence_chunks"
    )

    print("\n" + "=" * 70)
    print("FINAL COMPARISON")
    print("=" * 70)

    print(
        f"\nFixed-size chunks:"
        f"\nPrecision@3 = {fixed[0]:.3f}"
        f"\nRecall@3 = {fixed[1]:.3f}"
    )

    print(
        f"\nSentence-based chunks:"
        f"\nPrecision@3 = {sentence[0]:.3f}"
        f"\nRecall@3 = {sentence[1]:.3f}"
    )