import chromadb
from sentence_transformers import SentenceTransformer

PERSIST_DB_DIR = "chroma_data"
MODEL_NAME = "all-MiniLM-L6-v2"

# 5 Evaluation queries with mapped ground-truth parent IDs
BENCHMARK_SUITE = [
    {
        "query": "What is the return window for footwear?",
        "target_doc_id": "KB001",
    },
    {
        "query": "How long does a COD refund take?",
        "target_doc_id": "KB002",
    },
    {
        "query": "How long does standard delivery take?",
        "target_doc_id": "KB003",
    },
    {
        "query": "Can I exchange my shoes for another size?",
        "target_doc_id": "KB009",
    },
    {
        "query": "Can I cancel an order after it has shipped?",
        "target_doc_id": "KB006",
    },
]


def eval_strategy(collection_name: str, encoder: SentenceTransformer, db_client: chromadb.PersistentClient):
    col = db_client.get_collection(collection_name)
    
    precisions = []
    recalls = []

    print(f"\n================ EVALUATING COLLECTION: {collection_name} ================")

    for idx, test_case in enumerate(BENCHMARK_SUITE, 1):
        q_text = test_case["query"]
        target_id = test_case["target_doc_id"]

        q_vec = encoder.encode([q_text], normalize_embeddings=True).tolist()
        res = col.query(query_embeddings=q_vec, n_results=3)

        # Extract parent KB document IDs (extracting 'KB00x' prefix from 'KB00x_TITLE')
        retrieved_raw = [m["document_id"] for m in res["metadatas"][0]]
        retrieved_parents = [doc.split("_")[0] for doc in retrieved_raw]
        
        # Deduplicate while preserving order
        unique_retrieved = list(dict.fromkeys(retrieved_parents))

        # Precision@3 and Recall@3 arithmetic
        hits = [doc for doc in unique_retrieved if doc == target_id]
        
        p3 = len(hits) / len(unique_retrieved) if unique_retrieved else 0.0
        r3 = len(hits) / 1.0  # Target set size is 1 parent doc

        precisions.append(p3)
        recalls.append(r3)

        print(f"\n[Query {idx}]: '{q_text}'")
        print(f"  Target Doc ID:     {target_id}")
        print(f"  Retrieved Parents: {unique_retrieved}")
        print(f"  P@3 = {len(hits)}/{len(unique_retrieved)} = {p3:.3f} | R@3 = {len(hits)}/1 = {r3:.3f}")

    avg_p3 = sum(precisions) / len(precisions)
    avg_r3 = sum(recalls) / len(recalls)

    print("\n------------------------------------------------------------")
    print(f"Strategy Metrics ({collection_name}):")
    print(f"Mean Precision@3: {avg_p3:.3f}")
    print(f"Mean Recall@3:    {avg_r3:.3f}")
    print("------------------------------------------------------------")

    return avg_p3, avg_r3


def run_benchmark():
    encoder = SentenceTransformer(MODEL_NAME)
    db_client = chromadb.PersistentClient(path=PERSIST_DB_DIR)

    fixed_p, fixed_r = eval_strategy("nykaa_fixed_chunks", encoder, db_client)
    sent_p, sent_r = eval_strategy("nykaa_sentence_chunks", encoder, db_client)

    print("\n================ FINAL STRATEGY COMPARISON ================")
    print(f"Fixed-Size Chunks   -> Precision@3: {fixed_p:.3f} | Recall@3: {fixed_r:.3f}")
    print(f"Sentence-Based      -> Precision@3: {sent_p:.3f} | Recall@3: {sent_r:.3f}")
    
    print("\nRECOMMENDATION FOR AGENT:")
    if sent_p >= fixed_p:
        print("Use 'nykaa_sentence_chunks'. Sentence-based chunking maintains semantic cohesion without cutting policy rules mid-sentence.")
    else:
        print("Use 'nykaa_fixed_chunks'. Fixed-size overlap provided superior density for retrieval.")
    print("===========================================================")


if __name__ == "__main__":
    run_benchmark()