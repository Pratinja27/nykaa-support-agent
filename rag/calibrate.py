import chromadb
from sentence_transformers import SentenceTransformer

VECTOR_DB_DIR = "chroma_data"
MODEL_NAME = "all-MiniLM-L6-v2"

# Task 4 mandates >= 5 in-scope queries and >= 2 out-of-scope queries
IN_SCOPE_PROMPTS = [
    "What is the return window for footwear?",
    "How long does a COD refund take?",
    "Can I exchange my shoes for another size?",
    "How long does standard delivery take?",
    "What is the warranty period for beauty appliances?"
]

OUT_OF_SCOPE_PROMPTS = [
    "What is the capital of France?",
    "Write a Python program to sort a list."
]


def compute_top_similarity(collection, model, user_query):
    query_vector = model.encode([user_query], normalize_embeddings=True).tolist()
    
    response = collection.query(
        query_embeddings=query_vector,
        n_results=1
    )

    cosine_dist = response["distances"][0][0]
    similarity_score = 1.0 - cosine_dist
    doc_id = response["metadatas"][0][0]["document_id"]

    return similarity_score, doc_id


def run_calibration():
    db_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
    target_collection = db_client.get_collection("nykaa_sentence_chunks")
    encoder = SentenceTransformer(MODEL_NAME)

    in_scope_results = []
    out_scope_results = []

    print("=== TASK 4: EMPIRICAL THRESHOLD CALIBRATION ===")

    print("\n--- Testing In-Scope Queries ---")
    for q in IN_SCOPE_PROMPTS:
        score, target_doc = compute_top_similarity(target_collection, encoder, q)
        in_scope_results.append(score)
        print(f"Query: '{q}'\n  -> Matched Doc: {target_doc} | Top-1 Score: {score:.4f}")

    print("\n--- Testing Out-of-Scope Queries ---")
    for q in OUT_OF_SCOPE_PROMPTS:
        score, target_doc = compute_top_similarity(target_collection, encoder, q)
        out_scope_results.append(score)
        print(f"Query: '{q}'\n  -> Matched Doc: {target_doc} | Top-1 Score: {score:.4f}")

    # Calculate cluster boundaries
    lowest_in_scope = min(in_scope_results)
    highest_out_of_scope = max(out_scope_results)
    
    # Selected threshold positioned in the gap between the two clusters
    calibrated_threshold = round((lowest_in_scope + highest_out_of_scope) / 2, 2)

    print("\n" + "=" * 45)
    print("CALIBRATION SUMMARY & RECOMMENDED THRESHOLD")
    print("=" * 45)
    print(f"Lowest In-Scope Similarity:    {lowest_in_scope:.4f}")
    print(f"Highest Out-of-Scope Similarity: {highest_out_of_scope:.4f}")
    print(f"CALIBRATED THRESHOLD:          {calibrated_threshold}")
    print("=" * 45)


if __name__ == "__main__":
    run_calibration()