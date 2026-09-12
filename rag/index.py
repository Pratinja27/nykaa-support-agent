from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

from rag.chunking import fixed_size_chunks, sentence_chunks

# Paths and model config
BASE_KB_DIR = Path("data/knowledge_base")
PERSIST_DB_DIR = "chroma_data"
MODEL_NAME = "all-MiniLM-L6-v2"


def fetch_kb_files():
    """Reads all markdown and text files from the KB directory."""
    raw_docs = []
    
    # Grab both markdown and standard text files
    kb_paths = sorted(list(BASE_KB_DIR.glob("*.md")) + list(BASE_KB_DIR.glob("*.txt")))

    for file_path in kb_paths:
        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        # Extract Document ID header if present, otherwise default to filename stem
        lines = content.splitlines()
        first_line = lines[0] if lines else ""
        
        file_tag = file_path.stem.upper()
        if "Document ID:" in first_line:
            parsed_id = first_line.split("Document ID:")[1].strip()
            doc_identifier = f"{parsed_id}_{file_tag}"
        else:
            doc_identifier = file_tag

        raw_docs.append({
            "doc_id": doc_identifier,
            "file_name": file_path.name,
            "content": content
        })

    return raw_docs


def generate_all_chunks(docs):
    """Splits documents into fixed-size and sentence-based chunk dictionaries."""
    fixed_list = []
    sentence_list = []

    for doc in docs:
        # Strategy 1: Fixed-size overlap chunking
        f_chunks = fixed_size_chunks(doc["content"])
        for idx, text_block in enumerate(f_chunks):
            fixed_list.append({
                "chunk_id": f"{doc['doc_id']}_fixed_{idx}",
                "text": text_block,
                "doc_id": doc["doc_id"],
                "file_name": doc["file_name"],
                "pos": idx
            })

        # Strategy 2: Sentence-level chunking
        s_chunks = sentence_chunks(doc["content"])
        for idx, text_block in enumerate(s_chunks):
            sentence_list.append({
                "chunk_id": f"{doc['doc_id']}_sent_{idx}",
                "text": text_block,
                "doc_id": doc["doc_id"],
                "file_name": doc["file_name"],
                "pos": idx
            })

    return fixed_list, sentence_list


def sync_to_chroma(db_client, collection_name, chunk_data, encoder):
    """Upserts chunk payloads and embeddings into a targeted ChromaDB collection."""
    col = db_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    ids = [item["chunk_id"] for item in chunk_data]
    texts = [item["text"] for item in chunk_data]
    
    # Generate vector embeddings
    vectors = encoder.encode(texts, normalize_embeddings=True).tolist()

    metadata_payload = [
        {
            "document_id": item["doc_id"],
            "filename": item["file_name"],
            "chunk_index": item["pos"]
        }
        for item in chunk_data
    ]

    col.upsert(
        ids=ids,
        documents=texts,
        embeddings=vectors,
        metadatas=metadata_payload
    )

    return col


def main():
    documents = fetch_kb_files()
    if not documents:
        print("Warning: Knowledge base directory is empty. Nothing to index.")
        return

    fixed_chunks, sentence_chunks_data = generate_all_chunks(documents)
    
    print(f"Loading transformer model: {MODEL_NAME}...")
    embedder = SentenceTransformer(MODEL_NAME)
    
    db_client = chromadb.PersistentClient(path=PERSIST_DB_DIR)

    # Sync Strategy 1 (Fixed)
    col_fixed = sync_to_chroma(
        db_client, 
        "nykaa_fixed_chunks", 
        fixed_chunks, 
        embedder
    )

    # Sync Strategy 2 (Sentence)
    col_sent = sync_to_chroma(
        db_client, 
        "nykaa_sentence_chunks", 
        sentence_chunks_data, 
        embedder
    )

    print("\n--- Vector Store Summary ---")
    print(f"Raw documents parsed: {len(documents)}")
    print(f"Fixed-size collection count: {col_fixed.count()}")
    print(f"Sentence-based collection count: {col_sent.count()}")


if __name__ == "__main__":
    main()