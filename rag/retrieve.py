import chromadb
from sentence_transformers import SentenceTransformer


CHROMA_PATH = "chroma_data"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def search_collection(collection_name, query, top_k=3):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(collection_name)

    model = SentenceTransformer(EMBEDDING_MODEL)
    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    return results


def print_results(collection_name, query):
    results = search_collection(
        collection_name,
        query
    )

    print(f"\nCollection: {collection_name}")
    print(f"Query: {query}")

    for i, document in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]

        similarity = 1 - distance

        print(f"\nResult {i + 1}")
        print(f"Document: {metadata['document_id']}")
        print(f"Similarity: {similarity:.4f}")
        print(f"Text: {document}")


if __name__ == "__main__":
    query = "How long do I have to return footwear?"

    print_results(
        "nykaa_fixed_chunks",
        query
    )

    print_results(
        "nykaa_sentence_chunks",
        query
    )